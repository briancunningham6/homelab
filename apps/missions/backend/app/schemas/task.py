"""Task schemas."""
from pydantic import BaseModel
from datetime import date, datetime
from uuid import UUID
from typing import Optional, Literal


TaskStatus = Literal["open", "in_progress", "done"]


class TaskCreate(BaseModel):
    title: str
    due_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None


class TaskReorderItem(BaseModel):
    id: UUID
    sort_order: int


class TaskResponse(BaseModel):
    id: UUID
    mission_id: UUID
    title: str
    due_date: Optional[date] = None
    status: str
    sort_order: int
    reminder_sent: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
