"""Mission schemas."""
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional


class MissionBase(BaseModel):
    """Base mission schema."""

    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    goals: str = Field(..., min_length=1)
    category_id: Optional[UUID] = None
    llm_provider_id: Optional[UUID] = None
    model_override: Optional[str] = None
    check_interval: str = Field(default="daily")


class MissionCreate(MissionBase):
    """Schema for creating a mission."""

    pass


class MissionUpdate(BaseModel):
    """Schema for updating a mission."""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    goals: Optional[str] = None
    notes: Optional[str] = None
    category_id: Optional[UUID] = None
    llm_provider_id: Optional[UUID] = None
    model_override: Optional[str] = None
    check_interval: Optional[str] = None
    status: Optional[str] = None


class MissionResponse(MissionBase):
    """Schema for mission response."""

    id: UUID
    status: str
    notes: Optional[str] = None
    last_checked_at: Optional[datetime] = None
    next_check_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Include counts
    file_count: int = 0
    message_count: int = 0

    class Config:
        from_attributes = True
