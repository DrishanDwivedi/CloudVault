import uuid
import hashlib
import threading
from concurrent.futures import ThreadPoolExecutor
import pytest
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.file import File
from app.tasks.migration import migrate_file_task
from app.adapters.service import storage_service

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    # Create test user if not exists
    user = db.query(User).filter(User.email == "concurrency_test@example.com").first()
    if not user:
        user = User(
            email="concurrency_test@example.com",
            hashed_password="hash",
            full_name="Concurrency Tester",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    yield
    db.close()

def test_concurrent_migration_race_condition(monkeypatch):
    """
    Simulate two concurrent calls to migrate_file_task for the exact same file_id.
    Verify that atomic conditional update ensures only ONE call claims and performs migration,
    while the other call receives rows_updated == 0 and immediately aborts.
    """
    db = SessionLocal()
    user = db.query(User).filter(User.email == "concurrency_test@example.com").first()
    
    # Create test file payload
    file_content = b"Atomic test content for race condition verification."
    file_checksum = hashlib.sha256(file_content).hexdigest()
    file_uuid = f"race-test-{uuid.uuid4()}"
    
    # Upload to hot tier
    storage_service.upload_file(file_content, file_uuid, "hot")
    
    # Insert file record in DB with status='active'
    test_file = File(
        name="race_test.txt",
        original_name="race_test.txt",
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

    import time
    orig_migrate = storage_service.migrate_file
    def delayed_migrate(*args, **kwargs):
        time.sleep(0.15)
        return orig_migrate(*args, **kwargs)
    monkeypatch.setattr(storage_service, "migrate_file", delayed_migrate)

    results = []

    def run_task():
        return migrate_file_task(file_id, "warm")

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = [executor.submit(run_task), executor.submit(run_task)]
        results = [f.result() for f in futures]

    # Exactly one must succeed (True), and one must abort (False)
    assert True in results, "At least one migration attempt should succeed"
    assert False in results, "The second concurrent migration attempt must abort"
    assert results.count(True) == 1, "Only one concurrent migration should succeed"
    assert results.count(False) == 1, "Only one concurrent migration should fail/abort"

    # Verify final database state
    db_verify = SessionLocal()
    final_file = db_verify.query(File).filter(File.id == file_id).first()
    assert final_file.status == "active", "File status should return to 'active' after completion"
    assert final_file.current_tier == "warm", "File should have successfully migrated to warm tier"
    db_verify.close()
