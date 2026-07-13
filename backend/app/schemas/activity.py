import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

class ActivityResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    action: str
    file_id: Optional[int] = None
    folder_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime.datetime
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
