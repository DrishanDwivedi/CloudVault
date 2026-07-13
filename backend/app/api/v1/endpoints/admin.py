from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.core.security import get_current_admin
from app.models.user import User
from app.models.policy import LifecyclePolicy
from app.models.file import File as DBFile
from app.models.migration import MigrationHistory
from app.models.activity import ActivityLog
from app.schemas.policy import PolicyResponse, PolicyUpdate
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.migration import MigrationResponse
from app.schemas.activity import ActivityResponse
from app.tasks.migration import apply_lifecycle_policies_task

router = APIRouter()

@router.post("/lifecycle/trigger", status_code=status.HTTP_200_OK)
def trigger_lifecycle_policies(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Trigger Celery task (runs synchronously inline since Celery is eager)
    triggered_count = apply_lifecycle_policies_task()
    return {
        "message": "Lifecycle policy sweep execution complete.",
        "migrations_triggered": triggered_count
    }

@router.get("/lifecycle/policies", response_model=List[PolicyResponse])
def get_policies(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    policies = db.query(LifecyclePolicy).all()
    return policies

@router.patch("/lifecycle/policies/{id}", response_model=PolicyResponse)
def update_policy(
    id: int,
    policy_in: PolicyUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    policy = db.query(LifecyclePolicy).filter(LifecyclePolicy.id == id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Lifecycle policy with ID {id} not found."
        )
        
    policy.duration_days = policy_in.duration_days
    policy.is_active = policy_in.is_active
    db.commit()
    db.refresh(policy)
    return policy

@router.get("/analytics", response_model=Dict[str, Any])
def get_storage_analytics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    tiers_stats = {
        "hot": {"file_count": 0, "total_size_bytes": 0},
        "warm": {"file_count": 0, "total_size_bytes": 0},
        "archive": {"file_count": 0, "total_size_bytes": 0}
    }
    
    results = db.query(
        DBFile.current_tier,
        func.count(DBFile.id),
        func.sum(DBFile.size)
    ).filter(DBFile.status != "deleted").group_by(DBFile.current_tier).all()
    
    total_files = 0
    total_size_bytes = 0
    
    for tier, count, total_size in results:
        t_lower = (tier or "hot").lower()
        if t_lower in tiers_stats:
            tiers_stats[t_lower]["file_count"] = count
            tiers_stats[t_lower]["total_size_bytes"] = total_size or 0
            total_files += count
            total_size_bytes += total_size or 0
            
    return {
        "tiers": tiers_stats,
        "total_files": total_files,
        "total_size_bytes": total_size_bytes
    }

# --- USER MANAGEMENT ---

@router.get("/users", response_model=List[UserResponse])
def list_users(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from app.crud.base import get_all_users
    return get_all_users(db)

@router.patch("/users/{id}", response_model=UserResponse)
def update_user(
    id: int,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from app.crud.base import update_user
    updated = update_user(db, id, role=user_in.role, is_active=user_in.is_active)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated

# --- MIGRATION QUEUE ---

@router.get("/migrations", response_model=List[MigrationResponse])
def list_migrations(
    status_filter: Optional[str] = Query(None, alias="status"),
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from app.crud.base import get_all_migrations
    return get_all_migrations(db, status_filter=status_filter, limit=limit)

# --- ADMIN ACTIVITY LOGS (all users) ---

@router.get("/activities", response_model=List[ActivityResponse])
def list_all_activities(
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from app.crud.base import get_all_activities
    return get_all_activities(db, limit=limit)
