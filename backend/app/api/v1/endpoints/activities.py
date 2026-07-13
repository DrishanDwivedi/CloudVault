from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.activity import ActivityResponse
from app.crud.base import get_user_activities

router = APIRouter()

@router.get("", response_model=List[ActivityResponse])
def read_user_activities(
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    activities = get_user_activities(db, user_id=current_user.id, limit=limit)
    return activities
