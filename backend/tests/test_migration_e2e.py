import uuid
import hashlib
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
    user = db.query(User).filter(User.email == "e2e_migration@example.com").first()
    if not user:
        user = User(
            email="e2e_migration@example.com",
            hashed_password="hash",
            full_name="E2E Migration Tester",
            role="user",
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    yield
    db.close()

def test_full_hot_to_warm_to_archive_flow():
    """
    Test full end-to-end migration lifecycle:
    1. Upload to Hot tier (MinIO)
    2. Migrate Hot -> Warm tier (SeaweedFS)
    3. Migrate Warm -> Archive tier (Garage S3)
    4. Verify final content integrity, checksum, and database tier/backend tracking.
    """
    db = SessionLocal()
    user = db.query(User).filter(User.email == "e2e_migration@example.com").first()

    # 1. Setup file payload
    file_content = b"CloudVault E2E multi-tier migration content: Hot -> Warm -> Garage Archive."
    file_checksum = hashlib.sha256(file_content).hexdigest()
    file_uuid = f"e2e-{uuid.uuid4()}"

    # Upload to Hot tier
    assert storage_service.upload_file(file_content, file_uuid, "hot") is True
    assert storage_service.exists_file(file_uuid, "hot") is True

    test_file = File(
        name="lifecycle_test.dat",
        original_name="lifecycle_test.dat",
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

    # 2. Migrate Hot -> Warm
    res_warm = migrate_file_task(file_id, "warm")
    assert res_warm is True

    db.refresh(test_file)
    assert test_file.current_tier == "warm"
    assert test_file.current_backend == "seaweedfs"
    assert test_file.status == "active"
    assert storage_service.exists_file(file_uuid, "warm") is True
    # Source in hot should be removed
    assert storage_service.exists_file(file_uuid, "hot") is False

    # 3. Migrate Warm -> Archive (Garage)
    res_archive = migrate_file_task(file_id, "archive")
    assert res_archive is True

    db.refresh(test_file)
    assert test_file.current_tier == "archive"
    assert test_file.current_backend == "garage"
    assert test_file.status == "active"
    assert storage_service.exists_file(file_uuid, "archive") is True
    # Source in warm should be removed
    assert storage_service.exists_file(file_uuid, "warm") is False

    # 4. Download from Archive and verify content integrity
    downloaded_content = storage_service.download_file(file_uuid, "archive")
    assert downloaded_content == file_content
    assert hashlib.sha256(downloaded_content).hexdigest() == file_checksum

    db.close()
