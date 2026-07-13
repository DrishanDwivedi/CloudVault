from abc import ABC, abstractmethod
import hashlib

class StorageAdapter(ABC):
    @abstractmethod
    def upload(self, file_data: bytes, file_name: str, bucket_name: str) -> bool:
        """
        Uploads file bytes to the storage backend.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def download(self, file_name: str, bucket_name: str) -> bytes:
        """
        Downloads and returns file bytes from the storage backend.
        Raises exception if downloading fails.
        """
        pass

    @abstractmethod
    def delete(self, file_name: str, bucket_name: str) -> bool:
        """
        Deletes the file from the storage backend.
        Returns True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def exists(self, file_name: str, bucket_name: str) -> bool:
        """
        Checks if the file exists in the storage backend.
        Returns True if it exists, False otherwise.
        """
        pass

    def move(self, file_name: str, source_bucket: str, dest_bucket: str) -> bool:
        """
        Moves a file from source_bucket to dest_bucket within the same backend.
        Default implementation: download then upload then delete.
        Override for backends that support server-side copy.
        """
        try:
            data = self.download(file_name, source_bucket)
            if self.upload(data, file_name, dest_bucket):
                self.delete(file_name, source_bucket)
                return True
            return False
        except Exception:
            return False

    def verify_checksum(self, file_name: str, bucket_name: str, expected_checksum: str) -> bool:
        """
        Downloads the file, computes its SHA-256 hash, and compares it with expected_checksum.
        Returns True if hashes match, False otherwise.
        """
        try:
            file_data = self.download(file_name, bucket_name)
            calculated = hashlib.sha256(file_data).hexdigest()
            return calculated.lower() == expected_checksum.lower()
        except Exception:
            return False
