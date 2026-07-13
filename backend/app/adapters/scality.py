import os
import boto3
from botocore.config import Config
from app.adapters.base import StorageAdapter
from app.core.config import settings

class ScalityAdapter(StorageAdapter):
    def __init__(self):
        self.endpoint = settings.SCALITY_ENDPOINT
        self.access_key = settings.SCALITY_ACCESS_KEY_ID
        self.secret_key = settings.SCALITY_SECRET_ACCESS_KEY
        self.mock_dir = os.path.join(settings.MOCK_STORAGE_DIR, "scality")
        os.makedirs(self.mock_dir, exist_ok=True)

    def _get_s3_client(self):
        if settings.MOCK_STORAGE:
            raise ConnectionError("Mock mode active")

        return boto3.client(
            "s3",
            endpoint_url=self.endpoint,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            config=Config(signature_version="s3v4", connect_timeout=2.0, read_timeout=5.0, retries={"max_attempts": 1}),
            region_name="us-east-1"
        )

    def _mock_path(self, bucket_name: str, file_name: str) -> str:
        bucket_dir = os.path.join(self.mock_dir, bucket_name)
        os.makedirs(bucket_dir, exist_ok=True)
        return os.path.join(bucket_dir, file_name)

    def upload(self, file_data: bytes, file_name: str, bucket_name: str) -> bool:
        try:
            s3 = self._get_s3_client()
            try:
                s3.head_bucket(Bucket=bucket_name)
            except Exception:
                s3.create_bucket(Bucket=bucket_name)

            s3.put_object(Bucket=bucket_name, Key=file_name, Body=file_data)
            return True
        except Exception:
            try:
                path = self._mock_path(bucket_name, file_name)
                with open(path, "wb") as f:
                    f.write(file_data)
                return True
            except Exception:
                return False

    def download(self, file_name: str, bucket_name: str) -> bytes:
        try:
            s3 = self._get_s3_client()
            response = s3.get_object(Bucket=bucket_name, Key=file_name)
            return response["Body"].read()
        except Exception:
            path = self._mock_path(bucket_name, file_name)
            if os.path.exists(path):
                with open(path, "rb") as f:
                    return f.read()
            raise FileNotFoundError(f"File {file_name} not found in Scality S3 bucket {bucket_name}")

    def delete(self, file_name: str, bucket_name: str) -> bool:
        try:
            s3 = self._get_s3_client()
            s3.delete_object(Bucket=bucket_name, Key=file_name)
            return True
        except Exception:
            try:
                path = self._mock_path(bucket_name, file_name)
                if os.path.exists(path):
                    os.remove(path)
                return True
            except Exception:
                return False

    def exists(self, file_name: str, bucket_name: str) -> bool:
        try:
            s3 = self._get_s3_client()
            s3.head_object(Bucket=bucket_name, Key=file_name)
            return True
        except Exception:
            path = self._mock_path(bucket_name, file_name)
            return os.path.exists(path)
