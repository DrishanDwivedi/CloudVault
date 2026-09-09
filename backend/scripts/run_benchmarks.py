import os
import sys
import time
import uuid
import hashlib
import statistics
from pathlib import Path

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.file import File
from app.adapters.service import storage_service
from app.tasks.migration import migrate_file_task

SIZES_MB = [1, 10, 100]
REPETITIONS = 5

def generate_payload(size_mb: int) -> bytes:
    print(f"[INFO] Generating {size_mb} MB test payload in memory...")
    chunk = os.urandom(1024 * 1024)
    return chunk * size_mb

def calc_stats(times_ms, size_mb):
    sorted_times = sorted(times_ms)
    mean_val = float(statistics.mean(times_ms))
    median_val = float(statistics.median(times_ms))
    # 95th percentile
    k = (len(sorted_times) - 1) * 0.95
    f = int(k)
    c = min(f + 1, len(sorted_times) - 1)
    p95_val = sorted_times[f] + (k - f) * (sorted_times[c] - sorted_times[f])
    throughput = (size_mb / (mean_val / 1000.0)) if mean_val > 0 else 0.0
    return {
        "mean_ms": mean_val,
        "median_ms": median_val,
        "p95_ms": p95_val,
        "throughput_mb_s": throughput
    }

def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    user = db.query(User).filter(User.email == "benchmark@example.com").first()
    if not user:
        user = User(
            email="benchmark@example.com",
            hashed_password="hash",
            full_name="Benchmark Runner",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    user_id = user.id
    db.close()

    print("=" * 70)
    print("      CLOUDVAULT EMPIRICAL BENCHMARK SUITE")
    print("=" * 70)

    # 1. Generate payloads
    payloads = {}
    for sz in SIZES_MB:
        payloads[sz] = generate_payload(sz)

    # Dictionary to hold results
    results_direct = {}
    results_cloudvault = {}
    results_migration = {}

    # -------------------------------------------------------------
    # 2. Direct Storage Baseline Measurements (MinIO, SeaweedFS, Garage)
    # -------------------------------------------------------------
    print("\n--- Running Direct Storage Baselines ---")
    for tier in ["hot", "warm", "archive"]:
        adapter, bucket = storage_service._get_adapter_and_bucket(tier)
        results_direct[tier] = {"put": {}, "get": {}}
        print(f"\n[Direct] Storage Tier: {tier.upper()} (Bucket: {bucket})")

        for sz in SIZES_MB:
            data = payloads[sz]
            put_times = []
            get_times = []

            for rep in range(REPETITIONS):
                fname = f"bench-direct-{tier}-{sz}mb-{rep}-{uuid.uuid4()}"

                # Measure Direct PUT
                t0 = time.perf_counter()
                adapter.upload(data, fname, bucket)
                t1 = time.perf_counter()
                put_times.append((t1 - t0) * 1000.0)

                # Measure Direct GET
                t0 = time.perf_counter()
                downloaded = adapter.download(fname, bucket)
                t1 = time.perf_counter()
                get_times.append((t1 - t0) * 1000.0)

                # Cleanup
                adapter.delete(fname, bucket)

            results_direct[tier]["put"][sz] = calc_stats(put_times, sz)
            results_direct[tier]["get"][sz] = calc_stats(get_times, sz)
            print(f"  {sz}MB: PUT Mean={results_direct[tier]['put'][sz]['mean_ms']:.2f}ms ({results_direct[tier]['put'][sz]['throughput_mb_s']:.2f} MB/s) | GET Mean={results_direct[tier]['get'][sz]['mean_ms']:.2f}ms ({results_direct[tier]['get'][sz]['throughput_mb_s']:.2f} MB/s)")

    # -------------------------------------------------------------
    # 3. CloudVault-Mediated PUT/GET (Application Layer Overhead)
    # -------------------------------------------------------------
    print("\n--- Running CloudVault-Mediated Operations ---")
    results_cloudvault["put"] = {}
    results_cloudvault["get"] = {}

    for sz in SIZES_MB:
        data = payloads[sz]
        chk = hashlib.sha256(data).hexdigest()
        put_times = []
        get_times = []

        for rep in range(REPETITIONS):
            file_uuid = f"bench-cv-{sz}mb-{rep}-{uuid.uuid4()}"

            # CloudVault-mediated PUT: SHA256 calc + StorageService upload + DB metadata write
            t0 = time.perf_counter()
            storage_service.upload_file(data, file_uuid, "hot")
            db = SessionLocal()
            f_record = File(
                name=f"bench_{sz}mb.dat",
                original_name=f"bench_{sz}mb.dat",
                uuid=file_uuid,
                size=len(data),
                current_tier="hot",
                current_backend="minio",
                checksum=chk,
                status="active",
                owner_id=user_id
            )
            db.add(f_record)
            db.commit()
            db.refresh(f_record)
            f_id = f_record.id
            db.close()
            t1 = time.perf_counter()
            put_times.append((t1 - t0) * 1000.0)

            # CloudVault-mediated GET: DB lookup + StorageService download + Checksum validation
            t0 = time.perf_counter()
            db = SessionLocal()
            f_lookup = db.query(File).filter(File.id == f_id).first()
            downloaded = storage_service.download_file(f_lookup.uuid, f_lookup.current_tier)
            download_chk = hashlib.sha256(downloaded).hexdigest()
            assert download_chk == f_lookup.checksum
            f_lookup.download_count += 1
            db.commit()
            db.close()
            t1 = time.perf_counter()
            get_times.append((t1 - t0) * 1000.0)

            # Cleanup
            storage_service.delete_file(file_uuid, "hot")
            db = SessionLocal()
            del_record = db.query(File).filter(File.id == f_id).first()
            db.delete(del_record)
            db.commit()
            db.close()

        results_cloudvault["put"][sz] = calc_stats(put_times, sz)
        results_cloudvault["get"][sz] = calc_stats(get_times, sz)
        print(f"  {sz}MB: CloudVault PUT Mean={results_cloudvault['put'][sz]['mean_ms']:.2f}ms ({results_cloudvault['put'][sz]['throughput_mb_s']:.2f} MB/s) | GET Mean={results_cloudvault['get'][sz]['mean_ms']:.2f}ms ({results_cloudvault['get'][sz]['throughput_mb_s']:.2f} MB/s)")

    # -------------------------------------------------------------
    # 4. Multi-Tier Migrations (Hot -> Warm & Warm -> Archive)
    # -------------------------------------------------------------
    print("\n--- Running Multi-Tier Lifecycle Migrations ---")
    results_migration["hot_to_warm"] = {}
    results_migration["warm_to_archive"] = {}

    for sz in SIZES_MB:
        data = payloads[sz]
        chk = hashlib.sha256(data).hexdigest()
        h2w_times = []
        w2a_times = []

        for rep in range(REPETITIONS):
            file_uuid = f"bench-mig-{sz}mb-{rep}-{uuid.uuid4()}"

            # Setup initial file in Hot tier
            storage_service.upload_file(data, file_uuid, "hot")
            db = SessionLocal()
            test_file = File(
                name=f"mig_{sz}mb.dat",
                original_name=f"mig_{sz}mb.dat",
                uuid=file_uuid,
                size=len(data),
                current_tier="hot",
                current_backend="minio",
                checksum=chk,
                status="active",
                owner_id=user_id
            )
            db.add(test_file)
            db.commit()
            db.refresh(test_file)
            file_id = test_file.id
            db.close()

            # Hot -> Warm Migration
            t0 = time.perf_counter()
            res_h2w = migrate_file_task(file_id, "warm")
            t1 = time.perf_counter()
            assert res_h2w is True
            h2w_times.append((t1 - t0) * 1000.0)

            # Warm -> Archive Migration
            t0 = time.perf_counter()
            res_w2a = migrate_file_task(file_id, "archive")
            t1 = time.perf_counter()
            assert res_w2a is True
            w2a_times.append((t1 - t0) * 1000.0)

            # Cleanup
            storage_service.delete_file(file_uuid, "archive")
            db = SessionLocal()
            from app.models.migration import MigrationHistory
            from app.models.activity import ActivityLog
            db.query(MigrationHistory).filter(MigrationHistory.file_id == file_id).delete()
            db.query(ActivityLog).filter(ActivityLog.file_id == file_id).delete()
            del_f = db.query(File).filter(File.id == file_id).first()
            if del_f:
                db.delete(del_f)
            db.commit()
            db.close()

        results_migration["hot_to_warm"][sz] = calc_stats(h2w_times, sz)
        results_migration["warm_to_archive"][sz] = calc_stats(w2a_times, sz)
        print(f"  {sz}MB: Hot->Warm Mean={results_migration['hot_to_warm'][sz]['mean_ms']:.2f}ms ({results_migration['hot_to_warm'][sz]['throughput_mb_s']:.2f} MB/s) | Warm->Archive Mean={results_migration['warm_to_archive'][sz]['mean_ms']:.2f}ms ({results_migration['warm_to_archive'][sz]['throughput_mb_s']:.2f} MB/s)")

    # -------------------------------------------------------------
    # 5. Output Markdown Tables
    # -------------------------------------------------------------
    lines = []
    lines.append("======================================================================")
    lines.append("               FINAL BENCHMARK REPORT TABLES")
    lines.append("======================================================================")

    lines.append("\n### Table 1: Multi-Tier Migration Performance (N=5 repetitions)")
    lines.append("| Transition | Object Size | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Throughput (MB/s) |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for sz in SIZES_MB:
        st = results_migration["hot_to_warm"][sz]
        lines.append(f"| Hot -> Warm (MinIO -> SeaweedFS) | {sz} MB | {st['mean_ms']:.2f} | {st['median_ms']:.2f} | {st['p95_ms']:.2f} | {st['throughput_mb_s']:.2f} |")
    for sz in SIZES_MB:
        st = results_migration["warm_to_archive"][sz]
        lines.append(f"| Warm -> Archive (SeaweedFS -> Garage) | {sz} MB | {st['mean_ms']:.2f} | {st['median_ms']:.2f} | {st['p95_ms']:.2f} | {st['throughput_mb_s']:.2f} |")

    lines.append("\n### Table 2: Direct Storage Baseline vs. CloudVault-Mediated Operations (N=5 repetitions)")
    lines.append("| Layer / Storage Target | Operation | Size | Mean Latency (ms) | Median Latency (ms) | P95 Latency (ms) | Throughput (MB/s) |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
    for sz in SIZES_MB:
        p = results_direct["hot"]["put"][sz]
        g = results_direct["hot"]["get"][sz]
        lines.append(f"| Direct MinIO (Hot Baseline) | PUT | {sz} MB | {p['mean_ms']:.2f} | {p['median_ms']:.2f} | {p['p95_ms']:.2f} | {p['throughput_mb_s']:.2f} |")
        lines.append(f"| Direct MinIO (Hot Baseline) | GET | {sz} MB | {g['mean_ms']:.2f} | {g['median_ms']:.2f} | {g['p95_ms']:.2f} | {g['throughput_mb_s']:.2f} |")

    for sz in SIZES_MB:
        p = results_direct["warm"]["put"][sz]
        g = results_direct["warm"]["get"][sz]
        lines.append(f"| Direct SeaweedFS (Warm Baseline) | PUT | {sz} MB | {p['mean_ms']:.2f} | {p['median_ms']:.2f} | {p['p95_ms']:.2f} | {p['throughput_mb_s']:.2f} |")
        lines.append(f"| Direct SeaweedFS (Warm Baseline) | GET | {sz} MB | {g['mean_ms']:.2f} | {g['median_ms']:.2f} | {g['p95_ms']:.2f} | {g['throughput_mb_s']:.2f} |")

    for sz in SIZES_MB:
        p = results_direct["archive"]["put"][sz]
        g = results_direct["archive"]["get"][sz]
        lines.append(f"| Direct Garage S3 (Archive Baseline) | PUT | {sz} MB | {p['mean_ms']:.2f} | {p['median_ms']:.2f} | {p['p95_ms']:.2f} | {p['throughput_mb_s']:.2f} |")
        lines.append(f"| Direct Garage S3 (Archive Baseline) | GET | {sz} MB | {g['mean_ms']:.2f} | {g['median_ms']:.2f} | {g['p95_ms']:.2f} | {g['throughput_mb_s']:.2f} |")

    for sz in SIZES_MB:
        p = results_cloudvault["put"][sz]
        g = results_cloudvault["get"][sz]
        lines.append(f"| CloudVault-Mediated (Hot Tier) | PUT (+DB+SHA256) | {sz} MB | {p['mean_ms']:.2f} | {p['median_ms']:.2f} | {p['p95_ms']:.2f} | {p['throughput_mb_s']:.2f} |")
        lines.append(f"| CloudVault-Mediated (Hot Tier) | GET (+DB+SHA256) | {sz} MB | {g['mean_ms']:.2f} | {g['median_ms']:.2f} | {g['p95_ms']:.2f} | {g['throughput_mb_s']:.2f} |")

    lines.append("\n### Table 3: Application Overhead (CloudVault vs. Direct Baseline)")
    lines.append("| Operation | Size | Direct Baseline (ms) | CloudVault-Mediated (ms) | Absolute Overhead (ms) | Relative Overhead (%) |")
    lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
    for sz in SIZES_MB:
        d_put = results_direct["hot"]["put"][sz]["mean_ms"]
        cv_put = results_cloudvault["put"][sz]["mean_ms"]
        diff_put = cv_put - d_put
        pct_put = (diff_put / d_put * 100.0) if d_put > 0 else 0.0
        lines.append(f"| PUT | {sz} MB | {d_put:.2f} | {cv_put:.2f} | +{diff_put:.2f} | +{pct_put:.1f}% |")

        d_get = results_direct["hot"]["get"][sz]["mean_ms"]
        cv_get = results_cloudvault["get"][sz]["mean_ms"]
        diff_get = cv_get - d_get
        pct_get = (diff_get / d_get * 100.0) if d_get > 0 else 0.0
        lines.append(f"| GET | {sz} MB | {d_get:.2f} | {cv_get:.2f} | +{diff_get:.2f} | +{pct_get:.1f}% |")

    report_text = "\n".join(lines)
    print(report_text)
    with open("BENCHMARK_RESULTS.md", "w", encoding="utf-8") as f:
        f.write(report_text)
    print("\n[SUCCESS] Benchmark report saved to BENCHMARK_RESULTS.md")

if __name__ == "__main__":
    main()
