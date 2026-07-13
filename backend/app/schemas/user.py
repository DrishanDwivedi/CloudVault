import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, validator
from email_validator import validate_email, EmailNotValidError

class UserBase(BaseModel):
    # Allow local/special-use domains in dev by validating without deliverability checks
    email: str
    full_name: Optional[str] = None

    @validator('email')
    def allow_local_email(cls, v):
        try:
            # check_deliverability=False avoids rejecting special-use domains like 'localhost'
            validate_email(v, check_deliverability=False)
        except EmailNotValidError:
            raise ValueError('Invalid email')
        return v

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    id: int
    uuid: str
    role: str
    is_active: bool
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None
