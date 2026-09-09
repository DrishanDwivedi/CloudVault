import uuid
import hashlib
import datetime
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.file import File
from app.models.migration import MigrationHistory
from app.tasks.migration import migrate_file_task, recover_stalled_migrations
from app.adapters.service import storage_service

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    user = db.query(User).filter(User.email == "fault_injection@example.com").first()
    if not user:
        user = User(
            email="fault_injection@example.com",
            hashed_password="hash",
            full_name="Fault Injection Tester",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    yield
    db.close()

def test_fault_checksum_mismatch(monkeypatch):
    """
    FAULT 1: Destination receives corrupted data or checksum calculation fails.
    Asserts that migration aborts, destination file is cleaned up, file status returns to 'active',
    and a 'failed' migration record is logged without data loss on source tier.
    """
    db = SessionLocal()
    user = db.query(User).filter(User.email == "fault_injection@example.com").first()

    file_content = b"Authentic uncorrupted source data."
    real_checksum = hashlib.sha256(file_content).hexdigest()
    file_uuid = f"fault-chk-{uuid.uuid4()}"

    storage_service.upload_file(file_content, file_uuid, "hot")

    test_file = File(
        name="checksum_fault.txt",
        original_name="checksum_fault.txt",
        uuid=file_uuid,
        size=len(file_content),
        current_tier="hot",
        current_backend="minio",
        checksum=real_checksum,
        status="active",
        owner_id=user.id
    )
    db.add(test_file)
    db.commit()
    db.refresh(test_file)
    file_id = test_file.id

    # Inject checksum mismatch fault: monkeypatch verify_checksum on destination to fail
    warm_adapter = storage_service.adapters["warm"]
    monkeypatch.setattr(warm_adapter, "verify_checksum", lambda fname, bname, exp_chk: False)

    # Attempt migration
    result = migrate_file_task(file_id, "warm")
    assert result is False, "Migration should fail due to checksum verification failure"

    # Assert database state
    db.refresh(test_file)
    assert test_file.status == "active", "File status must revert to 'active' on failure"
    assert test_file.current_tier == "hot", "File tier must remain in source tier 'hot'"
    assert test_file.current_backend == "minio", "Backend must remain 'minio'"

    # Assert source file still exists intact
    assert storage_service.exists_file(file_uuid, "hot") is True
    assert storage_service.download_file(file_uuid, "hot") == file_content

    # Assert destination copy was cleaned up
    assert storage_service.exists_file(file_uuid, "warm") is False

    # Assert migration record recorded as failed
    mig_entry = db.query(MigrationHistory).filter(MigrationHistory.file_id == file_id).order_by(MigrationHistory.id.desc()).first()
    assert mig_entry is not None
    assert mig_entry.status == "failed"
    assert "checksum" in mig_entry.error_message.lower()

    db.close()

def test_fault_worker_killed_mid_migration():
    """
    FAULT 2: Worker process crashes/dies after setting status='migrating' before completion.
    Asserts that stalled files are safely detected and recovered back to 'active' state.
    """
    db = SessionLocal()
    user = db.query(User).filter(User.email == "fault_injection@example.com").first()

    file_content = b"Content for crashed worker simulation."
    file_checksum = hashlib.sha256(file_content).hexdigest()
    file_uuid = f"fault-crash-{uuid.uuid4()}"

    storage_service.upload_file(file_content, file_uuid, "hot")

    # Simulate a file that was claimed by a worker 30 minutes ago that died mid-task
    stalled_date = datetime.datetime.utcnow() - datetime.timedelta(minutes=30)
    test_file = File(
        name="stalled_file.txt",
        original_name="stalled_file.txt",
        uuid=file_uuid,
        size=len(file_content),
        current_tier="hot",
        current_backend="minio",
        checksum=file_checksum,
        status="migrating",  # Worker left it in migrating
        last_access_date=stalled_date,
        owner_id=user.id
    )
    db.add(test_file)
    db.commit()
    db.refresh(test_file)
    file_id = test_file.id

    # Run recovery
    recovered_count = recover_stalled_migrations(db, timeout_minutes=15)
    assert recovered_count >= 1

    db.refresh(test_file)
    assert test_file.status == "active", "Stalled file must be recovered to 'active' status"
    assert test_file.current_tier == "hot", "File tier should remain 'hot'"

    # Confirm it can now be migrated normally
    res = migrate_file_task(file_id, "warm")
    assert res is True
    db.refresh(test_file)
    assert test_file.status == "active"
    assert test_file.current_tier == "warm"

    db.close()

def test_fault_concurrent_migration_attempts(monkeypatch):
    """
    FAULT 3: Two workers attempt to migrate the exact same active file concurrently.
    Asserts atomic conditional locking ensures only 1 worker proceeds and 1 aborts.
    """
    import time
    db = SessionLocal()
    user = db.query(User).filter(User.email == "fault_injection@example.com").first()

    file_content = b"Content for concurrency fault test."
    file_checksum = hashlib.sha256(file_content).hexdigest()
    file_uuid = f"fault-race-{uuid.uuid4()}"

    storage_service.upload_file(file_content, file_uuid, "hot")

    test_file = File(
        name="race_fault.txt",
        original_name="race_fault.txt",
        uuid=file_uuid,
        size=len(file_content),
        current_tier="hot",
        current_backend="minio",
        checksum=file_checksum,
        status="active",
        owner_id=user.id
    )
    db.add(test_file)
    db.commit()
    db.refresh(test_file)
    file_id = test_file.id
    db.close()

    orig_migrate = storage_service.migrate_file
    def delayed_migrate(*args, **kwargs):
        time.sleep(0.15)
        return orig_migrate(*args, **kwargs)
    monkeypatch.setattr(storage_service, "migrate_file", delayed_migrate)

    def run_worker():
        return migrate_file_task(file_id, "warm")

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_worker)
        f2 = executor.submit(run_worker)
        r1 = f1.result()
        r2 = f2.result()

    results = [r1, r2]
    assert results.count(True) == 1, "Exactly one worker should succeed"
    assert results.count(False) == 1, "The competing worker must abort with False"

    db_verify = SessionLocal()
    f = db_verify.query(File).filter(File.id == file_id).first()
    assert f.status == "active"
    assert f.current_tier == "warm"
    db_verify.close()

def test_fault_source_deletion_failure(monkeypatch):
    """
    FAULT 4: Upload and verification succeed on destination, but source deletion encounters an error.
    Asserts that migration is completed successfully (file active on destination tier) and source error is handled gracefully.
    """
    db = SessionLocal()
    user = db.query(User).filter(User.email == "fault_injection@example.com").first()

    file_content = b"Content for source deletion failure test."
    file_checksum = hashlib.sha256(file_content).hexdigest()
    file_uuid = f"fault-del-{uuid.uuid4()}"

    storage_service.upload_file(file_content, file_uuid, "hot")

    test_file = File(
        name="source_del_fault.txt",
        original_name="source_del_fault.txt",
        uuid=file_uuid,
        size=len(file_content),
        current_tier="hot",
        current_backend="minio",
        checksum=file_checksum,
        status="active",
        owner_id=user.id
    )
    db.add(test_file)
    db.commit()
    db.refresh(test_file)
    file_id = test_file.id

    # Inject fault into hot adapter delete
    hot_adapter = storage_service.adapters["hot"]
    def faulty_delete(file_name, bucket_name):
        raise RuntimeError("Simulated source disk I/O lock prevented immediate deletion")

    monkeypatch.setattr(hot_adapter, "delete", faulty_delete)

    # Run migration hot -> warm
    result = migrate_file_task(file_id, "warm")
    assert result is True, "Migration must still succeed because destination was verified"

    db.refresh(test_file)
    assert test_file.status == "active"
    assert test_file.current_tier == "warm"
    assert test_file.current_backend == "seaweedfs"
    assert storage_service.exists_file(file_uuid, "warm") is True
    assert storage_service.download_file(file_uuid, "warm") == file_content

    db.close()
