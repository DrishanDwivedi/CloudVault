import hashlib
import mimetypes
import io
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File as FastAPIFile, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.file import File as DBFile
from app.models.folder import Folder
from app.schemas.file import FileResponse, FileRename
from app.crud.base import create_file_record, get_file, update_file_backend, delete_file_record, increment_download, log_activity
from app.adapters.service import storage_service

router = APIRouter()

@router.post("/upload", response_model=FileResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = FastAPIFile(...),
    folder_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify folder_id belongs to the current user
    if folder_id is not None:
        folder = db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == current_user.id).first()
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Target folder with ID {folder_id} not found."
            )
            
    # Read file and calculate SHA-256 on the fly
    sha256_hash = hashlib.sha256()
    file_bytes = b""
    
    # Read in chunks of 64KB to avoid loading huge files into memory at once
    while chunk := await file.read(65536):
        sha256_hash.update(chunk)
        file_bytes += chunk
        
    checksum = sha256_hash.hexdigest()
    size = len(file_bytes)
    
    # Parse extension and mime type
    filename = file.filename or "unnamed_file"
    _, ext = os.path.splitext(filename)
    extension = ext.lstrip(".").lower() if ext else None
    
    mime_type, _ = mimetypes.guess_type(filename)
    if not mime_type:
        mime_type = "application/octet-stream"

    # Generate metadata record to obtain UUID filename
    db_file = create_file_record(
        db,
        name=filename,
        original_name=filename,
        extension=extension,
        mime_type=mime_type,
        size=size,
        checksum=checksum,
        owner_id=current_user.id,
        folder_id=folder_id
    )
    
    # Upload physical bytes named by UUID to Hot Tier (MinIO)
    upload_success = storage_service.upload_file(file_bytes, db_file.uuid, "hot")
    if not upload_success:
        # Rollback DB metadata if storage upload fails
        db.delete(db_file)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to backend storage services."
        )
        
    log_activity(
        db,
        user_id=current_user.id,
        action="upload",
        file_id=db_file.id,
        details=f"Uploaded file '{db_file.name}' to Hot storage (Size: {size} bytes, Checksum: {checksum})"
    )
    
    return db_file

@router.get("/download/{id}")
def download_file(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_file = get_file(db, id, current_user.id)
    if not db_file or db_file.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {id} not found."
        )
        
    # Download bytes from the file's current storage tier
    try:
        file_data = storage_service.download_file(db_file.uuid, db_file.current_tier)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch file from storage: {str(e)}"
        )
        
    # Increment download counter and access date
    increment_download(db, db_file.id)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="download",
        file_id=db_file.id,
        details=f"Downloaded file '{db_file.name}' from {db_file.current_tier} tier."
    )
    
    # Return as StreamingResponse to avoid loading large payloads in browser RAM
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=db_file.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{db_file.name}"'}
    )

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_file = get_file(db, id, current_user.id)
    if not db_file or db_file.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {id} not found."
        )
        
    # Delete from active storage tier
    try:
        storage_service.delete_file(db_file.uuid, db_file.current_tier)
    except Exception as e:
        print(f"[WARNING] Failed to purge file {db_file.uuid} from storage: {str(e)}")
        
    # Soft delete in database
    delete_file_record(db, db_file.id, current_user.id)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="delete_file",
        details=f"Deleted file '{db_file.name}'"
    )
    
    return None

@router.patch("/{id}", response_model=FileResponse)
def rename_file(
    id: int,
    file_in: FileRename,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_file = get_file(db, id, current_user.id)
    if not db_file or db_file.status == "deleted":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File with ID {id} not found."
        )
        
    old_name = db_file.name
    db_file.name = file_in.name
    # Update extension if it changed
    _, ext = os.path.splitext(file_in.name)
    db_file.extension = ext.lstrip(".").lower() if ext else None
    db.commit()
    db.refresh(db_file)
    
    log_activity(
        db,
        user_id=current_user.id,
        action="rename_file",
        file_id=db_file.id,
        details=f"Renamed file '{old_name}' to '{db_file.name}'"
    )
    
    return db_file

@router.get("", response_model=List[FileResponse])
def list_files(
    folder_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify folder_id belongs to the current user
    if folder_id is not None:
        folder = db.query(Folder).filter(Folder.id == folder_id, Folder.owner_id == current_user.id).first()
        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Folder with ID {folder_id} not found."
            )
            
    files = db.query(DBFile).filter(
        DBFile.owner_id == current_user.id,
        DBFile.folder_id == folder_id,
        DBFile.status != "deleted"
    ).all()
    
    return files
