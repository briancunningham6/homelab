"""Category schemas."""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class CategoryResponse(BaseModel):
    """Schema for category response."""

    id: UUID
    name: str
    display_name: str
    color: Optional[str] = None
    icon: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
