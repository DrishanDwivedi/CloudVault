from sqlalchemy import Column, Integer, String, Boolean, Float
from app.core.database import Base

class LifecyclePolicy(Base):
    __tablename__ = "lifecycle_policies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    source_tier = Column(String, nullable=False) # "hot", "warm"
    dest_tier = Column(String, nullable=False)   # "warm", "archive"
    duration_days = Column(Float, nullable=False) # e.g. 30, 90, 0.003
    is_active = Column(Boolean, default=True, nullable=False)
