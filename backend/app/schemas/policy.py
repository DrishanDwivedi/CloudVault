from pydantic import BaseModel, ConfigDict

class PolicyUpdate(BaseModel):
    duration_days: float
    is_active: bool

class PolicyResponse(BaseModel):
    id: int
    name: str
    source_tier: str
    dest_tier: str
    duration_days: float
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
