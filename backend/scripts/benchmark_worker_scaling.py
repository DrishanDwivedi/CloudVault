import os
import sys
import time
import uuid
import hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# Ensure backend directory is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.file import File
from app.models.migration import MigrationHistory
from app.models.activity import ActivityLog
from app.adapters.service import storage_service
from app.tasks.migration import migrate_file_task

def run_worker_scaling_benchmark():
    print("=" * 80)
    print("        CLOUDVAULT WORKER SCALING BENCHMARK")
    print("=" * 80)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    user = db.query(User).first()
    if not user:
        user = User(
            email=f"scale_{uuid.uuid4().hex[:6]}@example.com",
            hashed_password="hash",
            full_name="Scale Benchmark User",
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    user_id = user.id
    db.close()

    NUM_FILES = 16
    FILE_SIZE_MB = 5
    WORKER_COUNTS = [1, 2, 4, 8]
    TOTAL_DATA_MB = NUM_FILES * FILE_SIZE_MB

    print(f"\nConfiguration:")
    print(f"  - Batch Size per Run: {NUM_FILES} files")
    print(f"  - File Size: {FILE_SIZE_MB} MB ({FILE_SIZE_MB * 1024 * 1024} bytes)")
    print(f"  - Total Data Volume per Run: {TOTAL_DATA_MB} MB")
    print(f"  - Worker Concurrency Levels: {WORKER_COUNTS}")
    print(f"  - Transition: Hot (MinIO) -> Warm (SeaweedFS)\n")

    payload = os.urandom(FILE_SIZE_MB * 1024 * 1024)
    chk = hashlib.sha256(payload).hexdigest()

    scaling_results = []
    baseline_time = None

    for workers in WORKER_COUNTS:
        print(f"\n--- Running Batch Migration with W = {workers} Worker(s) ---")
        
        # 1. Prepare batch of files in Hot tier
        print(f"  [1/3] Uploading {NUM_FILES} files to Hot tier (MinIO)...")
        file_ids = []
        file_uuids = []
        for i in range(NUM_FILES):
            fuuid = f"scale-w{workers}-f{i}-{uuid.uuid4().hex[:8]}"
            fname = f"scale_f{i}_{workers}w.dat"
            storage_service.upload_file(payload, fuuid, "hot")
            
            db = SessionLocal()
            frec = File(
                name=fname,
                original_name=fname,
                uuid=fuuid,
                size=len(payload),
                current_tier="hot",
                current_backend="minio",
                checksum=chk,
                status="active",
                owner_id=user_id
            )
            db.add(frec)
            db.commit()
            db.refresh(frec)
            file_ids.append(frec.id)
            file_uuids.append(fuuid)
            db.close()

        # 2. Execute parallel migration batch
        print(f"  [2/3] Executing parallel migrations across {workers} worker thread(s)...")
        t_start = time.perf_counter()
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(migrate_file_task, fid, "warm") for fid in file_ids]
            results = [f.result() for f in futures]
            
        t_end = time.perf_counter()
        total_time_s = t_end - t_start
        success_count = results.count(True)
        
        if baseline_time is None:
            baseline_time = total_time_s
            speedup = 1.0
            efficiency = 100.0
        else:
            speedup = baseline_time / total_time_s if total_time_s > 0 else 0.0
            efficiency = (speedup / workers) * 100.0

        throughput_mb_s = TOTAL_DATA_MB / total_time_s if total_time_s > 0 else 0.0
        avg_latency_per_file_ms = (total_time_s * 1000.0) / NUM_FILES

        print(f"  [3/3] Done: {success_count}/{NUM_FILES} files migrated in {total_time_s:.2f}s")
        print(f"        Throughput: {throughput_mb_s:.2f} MiB/s | Speedup: {speedup:.2f}x | Efficiency: {efficiency:.1f}%")

        scaling_results.append({
            "workers": workers,
            "total_time_s": total_time_s,
            "avg_latency_ms": avg_latency_per_file_ms,
            "throughput_mb_s": throughput_mb_s,
            "speedup": speedup,
            "efficiency": efficiency,
            "success_rate": f"{success_count}/{NUM_FILES}"
        })

        # Cleanup created files
        for fuuid, fid in zip(file_uuids, file_ids):
            storage_service.delete_file(fuuid, "warm")
            db = SessionLocal()
            db.query(MigrationHistory).filter(MigrationHistory.file_id == fid).delete()
            db.query(ActivityLog).filter(ActivityLog.file_id == fid).delete()
            f_del = db.query(File).filter(File.id == fid).first()
            if f_del:
                db.delete(f_del)
            db.commit()
            db.close()

    # Print Final Markdown Report Table
    print("\n" + "=" * 80)
    print("                    WORKER SCALING RESULTS REPORT")
    print("=" * 80)
    print(f"\n### Benchmark Setup: {NUM_FILES} Files x {FILE_SIZE_MB} MB ({TOTAL_DATA_MB} MB Total Workload)")
    print("| Concurrent Workers (W) | Total Duration (s) | Avg Latency/File (ms) | Throughput (MiB/s) | Speedup Factor | Parallel Efficiency (%) | Success Rate |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for r in scaling_results:
        print(f"| **{r['workers']}** | {r['total_time_s']:.2f} s | {r['avg_latency_ms']:.1f} ms | {r['throughput_mb_s']:.2f} MiB/s | **{r['speedup']:.2f}x** | **{r['efficiency']:.1f}%** | {r['success_rate']} |")

if __name__ == "__main__":
    run_worker_scaling_benchmark()
