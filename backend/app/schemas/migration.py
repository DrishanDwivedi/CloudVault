import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class MigrationResponse(BaseModel):
    id: int
    file_id: int
    source_backend: str
    dest_backend: str
    source_tier: str
    dest_tier: str
    status: str
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
