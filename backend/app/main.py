import time
import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
import redis
import boto3
from botocore.config import Config

from app.core.config import settings
from app.core.database import Base, engine, get_db, SessionLocal
from app.api.v1.endpoints import auth, folders, files, activities, admin

# Import models so Base can detect them and generate tables
from app.models import user, folder, file, migration, activity, policy
from app.crud.base import create_or_update_policy
from app.core.security import get_password_hash

# 1. Automatically create database tables on startup
Base.metadata.create_all(bind=engine)

# 1.5. Seed Default Admin User
def seed_default_admin():
    db = SessionLocal()
    try:
        # Check if admin already exists
        admin_user = db.query(user.User).filter(user.User.email == "admin@example.com").first()
        if admin_user:
            print("[INFO] Default admin user already exists, skipping seed.")
            return
        
        # Create default admin user
        hashed_password = get_password_hash("Admin@123")
        default_admin = user.User(
            email="admin@example.com",
            hashed_password=hashed_password,
            full_name="CloudVault Administrator",
            role="admin",
            is_active=True
        )
        db.add(default_admin)
        db.commit()
        db.refresh(default_admin)
        print("[INFO] Default admin user created successfully!")
        print(f"[INFO] Email: admin@example.com")
        print(f"[INFO] Password: Admin@123")
        print(f"[INFO] Role: admin")
    except Exception as e:
        print(f"[WARNING] Failed to seed default admin user: {str(e)}")
    finally:
        db.close()

seed_default_admin()

# 2. Seed Default Lifecycle Policies
def seed_default_policies():
    db = SessionLocal()
    try:
        # Default Hot -> Warm (30 Days)
        create_or_update_policy(
            db,
            name="Default Hot Storage to Warm Storage",
            source_tier="hot",
            dest_tier="warm",
            duration_days=30,
            is_active=True
        )
        # Default Warm -> Archive (90 Days)
        create_or_update_policy(
            db,
            name="Default Warm Storage to Archive Storage",
            source_tier="warm",
            dest_tier="archive",
            duration_days=90,
            is_active=True
        )
        print("[INFO] Default lifecycle policies successfully seeded.")
    except Exception as e:
        print(f"[WARNING] Failed to seed default lifecycle policies: {str(e)}")
    finally:
        db.close()

seed_default_policies()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(folders.router, prefix=f"{settings.API_V1_STR}/folders", tags=["folders"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["files"])
app.include_router(activities.router, prefix=f"{settings.API_V1_STR}/activities", tags=["activities"])
app.include_router(admin.router, prefix=f"{settings.API_V1_STR}/admin", tags=["admin"])

@app.get("/")
def read_root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "status": "online",
        "timestamp": time.time()
    }

@app.get(f"{settings.API_V1_STR}/health")
def health_check(db: Session = Depends(get_db)):
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "database": "unknown",
            "redis": "unknown",
            "minio": "unknown",
            "seaweedfs": "unknown",
            "scality": "unknown"
        }
    }

    # 1. Test Database Connection
    try:
        db.execute(text("SELECT 1"))
        db_type = "SQLite" if settings.DATABASE_URL.startswith("sqlite") else "PostgreSQL"
        health_status["services"]["database"] = f"online ({db_type})"
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["services"]["database"] = f"offline: {str(e)}"

    # 2. Test Redis Connection / Celery Eager Mode
    if settings.CELERY_TASK_ALWAYS_EAGER:
        health_status["services"]["redis"] = "online (simulated / eager)"
    else:
        try:
            r = redis.Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
            r.ping()
            health_status["services"]["redis"] = "online"
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["services"]["redis"] = f"offline: {str(e)}"

    # Helper helper to verify or fall back to mock storage
    def check_tier(name, check_fn):
        if settings.MOCK_STORAGE:
            try:
                check_fn()
                health_status["services"][name] = "online"
            except Exception:
                mock_path = os.path.join(settings.MOCK_STORAGE_DIR, name)
                os.makedirs(mock_path, exist_ok=True)
                health_status["services"][name] = f"online (simulated: {mock_path})"
        else:
            try:
                check_fn()
                health_status["services"][name] = "online"
            except Exception as e:
                health_status["status"] = "unhealthy"
                health_status["services"][name] = f"offline: {str(e)}"

    # 3. Test MinIO Connection (S3)
    def check_minio():
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ROOT_USER,
            aws_secret_access_key=settings.MINIO_ROOT_PASSWORD,
            config=Config(signature_version="s3v4", connect_timeout=0.5, read_timeout=0.5, retries={"max_attempts": 0}),
            region_name="us-east-1"
        )
        s3.list_buckets()
    check_tier("minio", check_minio)

    # 4. Test SeaweedFS S3 Connection
    def check_seaweedfs():
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.SEAWEEDFS_FILER_URL,
            aws_access_key_id="dummy",
            aws_secret_access_key="dummy",
            config=Config(signature_version="s3v4", connect_timeout=0.5, read_timeout=0.5, retries={"max_attempts": 0}),
            region_name="us-east-1"
        )
        s3.list_buckets()
    check_tier("seaweedfs", check_seaweedfs)

    # 5. Test Scality S3 Server Connection
    def check_scality():
        s3 = boto3.client(
            "s3",
            endpoint_url=settings.SCALITY_ENDPOINT,
            aws_access_key_id=settings.SCALITY_ACCESS_KEY_ID,
            aws_secret_access_key=settings.SCALITY_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4", connect_timeout=0.5, read_timeout=0.5, retries={"max_attempts": 0}),
            region_name="us-east-1"
        )
        s3.list_buckets()
    check_tier("scality", check_scality)

    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=500, detail=health_status)

    return health_status
