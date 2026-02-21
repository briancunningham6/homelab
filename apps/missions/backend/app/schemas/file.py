"""File schemas."""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class FileUploadResponse(BaseModel):
    """Schema for file upload response."""

    id: UUID
    filename: str
    original_name: str
    mime_type: Optional[str] = None
    size_bytes: int
    uploaded_at: datetime


class FileResponse(FileUploadResponse):
    """Schema for file details response."""

    mission_id: UUID
    extracted_text: Optional[str] = None

    class Config:
        from_attributes = True
