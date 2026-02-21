"""File upload/download endpoints."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID, uuid4
import shutil
from pathlib import Path

from app.database import get_db
from app.models.mission import Mission
from app.models.mission_file import MissionFile
from app.schemas.file import FileUploadResponse, FileResponse as FileResponseSchema

router = APIRouter()

# Base directory for file storage
FILES_DIR = Path("/app/data/files")


@router.post("/{mission_id}/files", response_model=FileUploadResponse, status_code=201)
async def upload_file(
    mission_id: UUID,
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
):
    """Upload a file to a mission."""
    # Check mission exists
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Create mission-specific directory
    mission_dir = FILES_DIR / str(mission_id)
    mission_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    file_ext = Path(file.filename).suffix
    unique_filename = f"{uuid4()}{file_ext}"
    file_path = mission_dir / unique_filename

    # Save file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Get file size
    file_size = file_path.stat().st_size

    # Create database record
    mission_file = MissionFile(
        mission_id=mission_id,
        filename=unique_filename,
        original_name=file.filename,
        mime_type=file.content_type,
        size_bytes=file_size,
        storage_path=f"{mission_id}/{unique_filename}",
    )

    db.add(mission_file)
    db.commit()
    db.refresh(mission_file)

    return FileUploadResponse(
        id=mission_file.id,
        filename=mission_file.filename,
        original_name=mission_file.original_name,
        mime_type=mission_file.mime_type,
        size_bytes=mission_file.size_bytes,
        uploaded_at=mission_file.uploaded_at,
    )


@router.get("/{mission_id}/files", response_model=List[FileResponseSchema])
async def list_files(
    mission_id: UUID,
    db: Session = Depends(get_db),
):
    """List files for a mission."""
    # Check mission exists
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    files = db.query(MissionFile).filter(MissionFile.mission_id == mission_id).all()
    return files


@router.get("/{mission_id}/files/{file_id}")
async def download_file(
    mission_id: UUID,
    file_id: UUID,
    db: Session = Depends(get_db),
):
    """Download a file."""
    # Check file exists and belongs to mission
    mission_file = (
        db.query(MissionFile)
        .filter(
            MissionFile.id == file_id,
            MissionFile.mission_id == mission_id,
        )
        .first()
    )

    if not mission_file:
        raise HTTPException(status_code=404, detail="File not found")

    file_path = FILES_DIR / mission_file.storage_path

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")

    return FileResponse(
        path=file_path,
        filename=mission_file.original_name,
        media_type=mission_file.mime_type,
    )


@router.delete("/{mission_id}/files/{file_id}", status_code=204)
async def delete_file(
    mission_id: UUID,
    file_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a file."""
    # Check file exists and belongs to mission
    mission_file = (
        db.query(MissionFile)
        .filter(
            MissionFile.id == file_id,
            MissionFile.mission_id == mission_id,
        )
        .first()
    )

    if not mission_file:
        raise HTTPException(status_code=404, detail="File not found")

    # Delete from filesystem
    file_path = FILES_DIR / mission_file.storage_path
    if file_path.exists():
        file_path.unlink()

    # Delete from database
    db.delete(mission_file)
    db.commit()

    return None
