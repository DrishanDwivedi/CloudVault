import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.folder import Folder
from app.models.file import File
from app.models.migration import MigrationHistory
from app.models.activity import ActivityLog
from app.models.policy import LifecyclePolicy
from app.models.user import User

# --- FOLDERS CRUD ---

def create_folder(db: Session, name: str, parent_id: Optional[int], owner_id: int) -> Folder:
    db_folder = Folder(
        name=name,
        parent_id=parent_id,
        owner_id=owner_id
    )
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    return db_folder

def get_folder(db: Session, folder_id: int, owner_id: int) -> Optional[Folder]:
    return db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == owner_id).first()

def get_user_folders(db: Session, owner_id: int, parent_id: Optional[int] = None) -> List[Folder]:
    return db.query(Folder).filter(
        Folder.owner_id == owner_id,
        Folder.parent_id == parent_id
    ).all()

def delete_folder(db: Session, folder_id: int, owner_id: int) -> bool:
    db_folder = get_folder(db, folder_id, owner_id)
    if db_folder:
        db.delete(db_folder)
        db.commit()
        return True
    return False

def rename_folder(db: Session, folder_id: int, new_name: str, owner_id: int) -> Optional[Folder]:
    db_folder = get_folder(db, folder_id, owner_id)
    if db_folder:
        db_folder.name = new_name
        db.commit()
        db.refresh(db_folder)
        return db_folder
    return None


# --- FILES CRUD ---

def create_file_record(
    db: Session,
    name: str,
    original_name: str,
    extension: Optional[str],
    mime_type: Optional[str],
    size: int,
    checksum: str,
    owner_id: int,
    folder_id: Optional[int] = None
) -> File:
    # Set default next migration date to 30 days from now (Hot storage duration)
    next_migration = datetime.datetime.utcnow() + datetime.timedelta(days=30)
    
    db_file = File(
        owner_id=owner_id,
        folder_id=folder_id,
        name=name,
        original_name=original_name,
        extension=extension.lower() if extension else None,
        mime_type=mime_type,
        size=size,
        checksum=checksum,
        current_backend="minio",
        current_tier="hot",
        next_migration_date=next_migration,
        status="active"
    )
    db.add(db_file)
    db.commit()
    db.refresh(db_file)
    return db_file

def get_file(db: Session, file_id: int, owner_id: int) -> Optional[File]:
    return db.query(File).filter(File.id == file_id, File.owner_id == owner_id).first()

def get_user_files(db: Session, owner_id: int, folder_id: Optional[int] = None) -> List[File]:
    return db.query(File).filter(
        File.owner_id == owner_id,
        File.folder_id == folder_id,
        File.status != "deleted"
    ).all()

def update_file_backend(
    db: Session,
    file_id: int,
    new_backend: str,
    new_tier: str,
    next_migration_date: Optional[datetime.datetime] = None
) -> Optional[File]:
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file:
        db_file.current_backend = new_backend
        db_file.current_tier = new_tier
        db_file.migration_count += 1
        if next_migration_date:
            db_file.next_migration_date = next_migration_date
        else:
            # Clear or set based on destination tier
            if new_tier == "warm":
                # Warm tier duration: e.g. next transition to archive after 90 days from upload
                db_file.next_migration_date = db_file.upload_date + datetime.timedelta(days=90)
            else:
                # Archive tier is the final destination, no further migration scheduled
                db_file.next_migration_date = None
        db.commit()
        db.refresh(db_file)
        return db_file
    return None

def delete_file_record(db: Session, file_id: int, owner_id: int) -> bool:
    db_file = get_file(db, file_id, owner_id)
    if db_file:
        # Perform soft delete in DB, actual physical deletions are done via adapter
        db_file.status = "deleted"
        db_file.next_migration_date = None
        db.commit()
        return True
    return False

def increment_download(db: Session, file_id: int) -> Optional[File]:
    db_file = db.query(File).filter(File.id == file_id).first()
    if db_file:
        db_file.download_count += 1
        db_file.last_access_date = datetime.datetime.utcnow()
        db.commit()
        db.refresh(db_file)
        return db_file
    return None


# --- MIGRATIONS CRUD ---

def create_migration_entry(
    db: Session,
    file_id: int,
    source_backend: str,
    dest_backend: str,
    source_tier: str,
    dest_tier: str
) -> MigrationHistory:
    entry = MigrationHistory(
        file_id=file_id,
        source_backend=source_backend,
        dest_backend=dest_backend,
        source_tier=source_tier,
        dest_tier=dest_tier,
        status="in_progress"
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def complete_migration_entry(
    db: Session,
    migration_id: int,
    status: str,
    error_message: Optional[str] = None
) -> Optional[MigrationHistory]:
    entry = db.query(MigrationHistory).filter(MigrationHistory.id == migration_id).first()
    if entry:
        entry.status = status
        entry.completed_at = datetime.datetime.utcnow()
        if error_message:
            entry.error_message = error_message
        db.commit()
        db.refresh(entry)
        return entry
    return None


# --- ACTIVITY LOGS CRUD ---

def log_activity(
    db: Session,
    user_id: Optional[int],
    action: str,
    file_id: Optional[int] = None,
    folder_id: Optional[int] = None,
    details: Optional[str] = None
) -> ActivityLog:
    log = ActivityLog(
        user_id=user_id,
        action=action,
        file_id=file_id,
        folder_id=folder_id,
        details=details
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log

def _attach_user_info(activities):
    for act in activities:
        if act.user:
            act.user_email = act.user.email
            act.user_name = act.user.full_name
    return activities

def get_user_activities(db: Session, user_id: int, limit: int = 50) -> List[ActivityLog]:
    activities = db.query(ActivityLog).filter(ActivityLog.user_id == user_id).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
    return _attach_user_info(activities)


# --- ADMIN: USERS CRUD ---

def get_all_users(db: Session) -> List[User]:
    return db.query(User).order_by(User.created_at.desc()).all()

def update_user(db: Session, user_id: int, role: Optional[str] = None, is_active: Optional[bool] = None) -> Optional[User]:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user

# --- ADMIN: MIGRATIONS CRUD ---

def get_all_migrations(db: Session, status_filter: Optional[str] = None, limit: int = 50) -> List[MigrationHistory]:
    query = db.query(MigrationHistory).order_by(MigrationHistory.started_at.desc())
    if status_filter:
        query = query.filter(MigrationHistory.status == status_filter)
    return query.limit(limit).all()

# --- ADMIN: ACTIVITY LOGS CRUD ---

def get_all_activities(db: Session, limit: int = 50) -> List[ActivityLog]:
    activities = db.query(ActivityLog).order_by(ActivityLog.timestamp.desc()).limit(limit).all()
    return _attach_user_info(activities)

# --- LIFECYCLE POLICIES CRUD ---

def get_active_policies(db: Session) -> List[LifecyclePolicy]:
    return db.query(LifecyclePolicy).filter(LifecyclePolicy.is_active == True).all()

def create_or_update_policy(
    db: Session,
    name: str,
    source_tier: str,
    dest_tier: str,
    duration_days: float,
    is_active: bool = True
) -> LifecyclePolicy:
    policy = db.query(LifecyclePolicy).filter(
        LifecyclePolicy.source_tier == source_tier,
        LifecyclePolicy.dest_tier == dest_tier
    ).first()
    
    if policy:
        policy.name = name
        policy.duration_days = duration_days
        policy.is_active = is_active
    else:
        policy = LifecyclePolicy(
            name=name,
            source_tier=source_tier,
            dest_tier=dest_tier,
            duration_days=duration_days,
            is_active=is_active
        )
        db.add(policy)
        
    db.commit()
    db.refresh(policy)
    return policy
