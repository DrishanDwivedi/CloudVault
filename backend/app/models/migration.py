import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class MigrationHistory(Base):
    __tablename__ = "migration_history"

    id = Column(Integer, primary_key=True, index=True)
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, index=True)
    source_backend = Column(String, nullable=False)
    dest_backend = Column(String, nullable=False)
    source_tier = Column(String, nullable=False)
    dest_tier = Column(String, nullable=False)
    status = Column(String, default="in_progress", nullable=False) # "in_progress", "success", "failed"
    started_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(String, nullable=True)

    # Relationships
    file = relationship("File", backref="migrations")
