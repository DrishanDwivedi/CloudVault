import os
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "CloudVault"

    # CORS Origins
    BACKEND_CORS_ORIGINS: Union[str, List[str]] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    DATABASE_URL: str = "sqlite:///./cloudvault.db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = ""

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def assemble_redis_url(cls, v: str, info) -> str:
        if v:
            return v
        data = info.data
        return f"redis://{data.get('REDIS_HOST', 'localhost')}:{data.get('REDIS_PORT', 6379)}/0"

    # Celery Eager Mode (Synchronous development mode, no Redis required)
    CELERY_TASK_ALWAYS_EAGER: bool = True

    # Mock Storage Fallback
    MOCK_STORAGE: bool = True
    MOCK_STORAGE_DIR: str = "./storage/mock"

    # JWT
    JWT_SECRET_KEY: str = "super_secret_jwt_key_change_me_in_production_1234567890"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    # MinIO (Hot Storage)
    MINIO_ENDPOINT: str = "http://localhost:9000"
    MINIO_ROOT_USER: str = "cloudvault_admin"
    MINIO_ROOT_PASSWORD: str = "minio_secure_password_123"
    MINIO_BUCKET_NAME: str = "cloudvault-hot"

    # SeaweedFS (Warm Storage)
    SEAWEEDFS_FILER_URL: str = "http://localhost:8333"
    SEAWEEDFS_BUCKET_NAME: str = "cloudvault-warm"

    # Scality S3 Server (Archive Storage)
    SCALITY_ENDPOINT: str = "http://localhost:18000"
    SCALITY_ACCESS_KEY_ID: str = "scality_admin"
    SCALITY_SECRET_ACCESS_KEY: str = "scality_secret_key_123"
    SCALITY_BUCKET_NAME: str = "cloudvault-archive"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

settings = Settings()
