import datetime
import uuid
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from app.core.database import Base

class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    extension = Column(String, nullable=True, index=True)
    mime_type = Column(String, nullable=True)
    size = Column(BigInteger, nullable=False)
    checksum = Column(String, nullable=False)
    current_backend = Column(String, default="minio", nullable=False) # "minio", "seaweedfs", "scality"
    current_tier = Column(String, default="hot", nullable=False)      # "hot", "warm", "archive"
    upload_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    last_access_date = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    next_migration_date = Column(DateTime, nullable=True)
    download_count = Column(Integer, default=0, nullable=False)
    migration_count = Column(Integer, default=0, nullable=False)
    status = Column(String, default="active", nullable=False)         # "active", "migrating", "deleted"

    # Relationships
    owner = relationship("User", backref="files")
    folder = relationship("Folder", backref=backref("files", cascade="all, delete-orphan", passive_deletes=True))
