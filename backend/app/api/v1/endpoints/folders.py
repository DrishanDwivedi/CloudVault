from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.folder import Folder
from app.models.file import File
from app.schemas.folder import FolderCreate, FolderResponse
from app.schemas.file import FileResponse
from app.crud.base import create_folder, get_folder, get_user_folders, delete_folder, rename_folder, log_activity
from app.adapters.service import storage_service

router = APIRouter()

@router.post("", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_new_folder(
    folder_in: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify parent folder exists and is owned by the current user
    if folder_in.parent_id is not None:
        parent = get_folder(db, folder_in.parent_id, current_user.id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent folder with ID {folder_in.parent_id} not found."
            )
            
    db_folder = create_folder(db, name=folder_in.name, parent_id=folder_in.parent_id, owner_id=current_user.id)
    log_activity(
        db,
        user_id=current_user.id,
        action="create_folder",
        folder_id=db_folder.id,
        details=f"Created folder '{db_folder.name}' (UUID: {db_folder.uuid})"
    )
    return db_folder

@router.get("/contents", response_model=Dict[str, Any])
def get_folder_contents(
    parent_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # If parent_id is specified, verify it exists and is owned by the user
    if parent_id is not None:
        parent = get_folder(db, parent_id, current_user.id)
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Folder with ID {parent_id} not found."
            )
            
    folders = get_user_folders(db, current_user.id, parent_id)
    
    # Query files inside this folder that are active
    files = db.query(File).filter(
        File.owner_id == current_user.id,
        File.folder_id == parent_id,
        File.status != "deleted"
    ).all()
    
    return {
        "folders": [FolderResponse.model_validate(f) for f in folders],
        "files": [FileResponse.model_validate(f) for f in files]
    }

def _recursive_delete_files(db: Session, folder_id: int, owner_id: int):
    # Delete child files inside the current folder
    files = db.query(File).filter(File.folder_id == folder_id, File.owner_id == owner_id, File.status != "deleted").all()
    for file in files:
        try:
            # Delete physical file from its storage tier
            storage_service.delete_file(file.uuid, file.current_tier)
        except Exception as e:
            print(f"[WARNING] Failed to delete file {file.uuid} from storage during recursive folder delete: {str(e)}")
        file.status = "deleted"
        file.next_migration_date = None
        
    # Recursively traverse into child folders
    subfolders = db.query(Folder).filter(Folder.parent_id == folder_id, Folder.owner_id == owner_id).all()
    for sub in subfolders:
        _recursive_delete_files(db, sub.id, owner_id)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_existing_folder(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_folder = get_folder(db, id, current_user.id)
    if not db_folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Folder with ID {id} not found."
        )
        
    # Delete physical objects of all files in this folder and subfolders recursively
    _recursive_delete_files(db, db_folder.id, current_user.id)
    
    # Now execute cascade DB deletes
    log_activity(
        db,
        user_id=current_user.id,
        action="delete_folder",
        details=f"Deleted folder '{db_folder.name}' and all recursive contents."
    )
    
    db.delete(db_folder)
    db.commit()
    return None

@router.patch("/{id}", response_model=FolderResponse)
def rename_existing_folder(
    id: int,
    folder_in: FolderCreate, # Reusing FolderCreate name field
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_folder = rename_folder(db, folder_id=id, new_name=folder_in.name, owner_id=current_user.id)
    if not db_folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Folder with ID {id} not found."
        )
        
    log_activity(
        db,
        user_id=current_user.id,
        action="rename_folder",
        folder_id=db_folder.id,
        details=f"Renamed folder to '{db_folder.name}'"
    )
    return db_folder
