"""File schemas."""
from pydantic import BaseModel, computed_field
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

    @computed_field
    @property
    def size(self) -> int:
        """Alias for size_bytes for frontend compatibility."""
        return self.size_bytes


class FileResponse(FileUploadResponse):
    """Schema for file details response."""

    mission_id: UUID
    extracted_text: Optional[str] = None

    class Config:
        from_attributes = True
