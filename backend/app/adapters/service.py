import hashlib
from typing import Dict
from app.adapters.base import StorageAdapter
from app.adapters.minio import MinIOAdapter
from app.adapters.seaweedfs import SeaweedFSAdapter
from app.adapters.scality import ScalityAdapter
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.adapters: Dict[str, StorageAdapter] = {
            "hot": MinIOAdapter(),
            "warm": SeaweedFSAdapter(),
            "archive": ScalityAdapter()
        }
        
        self.buckets: Dict[str, str] = {
            "hot": settings.MINIO_BUCKET_NAME,
            "warm": settings.SEAWEEDFS_BUCKET_NAME,
            "archive": settings.SCALITY_BUCKET_NAME
        }

    def _get_adapter_and_bucket(self, tier: str):
        tier_lower = tier.lower()
        if tier_lower not in self.adapters:
            raise ValueError(f"Invalid storage tier: {tier}. Must be 'hot', 'warm', or 'archive'")
        return self.adapters[tier_lower], self.buckets[tier_lower]

    def upload_file(self, file_data: bytes, file_name: str, tier: str) -> bool:
        adapter, bucket = self._get_adapter_and_bucket(tier)
        return adapter.upload(file_data, file_name, bucket)

    def download_file(self, file_name: str, tier: str) -> bytes:
        adapter, bucket = self._get_adapter_and_bucket(tier)
        return adapter.download(file_name, bucket)

    def delete_file(self, file_name: str, tier: str) -> bool:
        adapter, bucket = self._get_adapter_and_bucket(tier)
        return adapter.delete(file_name, bucket)

    def exists_file(self, file_name: str, tier: str) -> bool:
        adapter, bucket = self._get_adapter_and_bucket(tier)
        return adapter.exists(file_name, bucket)

    def migrate_file(self, file_name: str, source_tier: str, dest_tier: str, expected_checksum: str) -> bool:
        """
        Migrates a file from source_tier to dest_tier:
        1. Downloads file bytes from source.
        2. Uploads file bytes to destination.
        3. Verifies checksum of destination file.
        4. If verified, deletes the source file.
        Raises an exception if any step fails.
        """
        src_adapter, src_bucket = self._get_adapter_and_bucket(source_tier)
        dest_adapter, dest_bucket = self._get_adapter_and_bucket(dest_tier)

        # 1. Download from source
        try:
            file_data = src_adapter.download(file_name, src_bucket)
        except Exception as e:
            raise RuntimeError(f"Migration failed during download from source {source_tier}: {str(e)}")

        # Verify download checksum before copying
        local_checksum = hashlib.sha256(file_data).hexdigest()
        if local_checksum.lower() != expected_checksum.lower():
            raise ValueError(f"Migration aborted: Source file checksum mismatch. Expected: {expected_checksum}, calculated: {local_checksum}")

        # 2. Upload to destination
        try:
            upload_success = dest_adapter.upload(file_data, file_name, dest_bucket)
            if not upload_success:
                raise RuntimeError("Upload returned False")
        except Exception as e:
            raise RuntimeError(f"Migration failed during upload to destination {dest_tier}: {str(e)}")

        # 3. Verify destination checksum
        try:
            checksum_verified = dest_adapter.verify_checksum(file_name, dest_bucket, expected_checksum)
            if not checksum_verified:
                raise ValueError("Verification returned False")
        except Exception as e:
            # Cleanup destination copy if validation failed
            dest_adapter.delete(file_name, dest_bucket)
            raise RuntimeError(f"Migration failed: Destination checksum verification failed: {str(e)}")

        # 4. Delete source file
        try:
            delete_success = src_adapter.delete(file_name, src_bucket)
            if not delete_success:
                print(f"[WARNING] Migrated file copied, but failed to clean up source {source_tier} object '{file_name}'")
        except Exception as e:
            print(f"[WARNING] Migrated file copied, but failed to delete source {source_tier} file: {str(e)}")

        return True

# Singleton instance of the storage service
storage_service = StorageService()
