import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class FileRename(BaseModel):
    name: str

class FileResponse(BaseModel):
    id: int
    uuid: str
    owner_id: int
    folder_id: Optional[int] = None
    name: str
    original_name: str
    extension: Optional[str] = None
    mime_type: Optional[str] = None
    size: int
    checksum: str
    current_backend: str
    current_tier: str
    upload_date: datetime.datetime
    last_access_date: datetime.datetime
    next_migration_date: Optional[datetime.datetime] = None
    download_count: int
    migration_count: int
    status: str

    model_config = ConfigDict(from_attributes=True)
