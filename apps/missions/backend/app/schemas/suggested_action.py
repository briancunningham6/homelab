"""Suggested action schemas."""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional
from enum import Enum


class ActionType(str, Enum):
    """Type of suggested action."""
    USER_ACTION = "user_action"
    AGENT_ACTION = "agent_action"
    INFO_REQUEST = "info_request"


class ActionPriority(str, Enum):
    """Priority level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionStatus(str, Enum):
    """Status of action."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    DISMISSED = "dismissed"
    COMPLETED = "completed"


class SuggestedActionCreate(BaseModel):
    """Schema for creating a suggested action."""
    type: ActionType
    title: str
    description: str
    reasoning: Optional[str] = None
    priority: ActionPriority = ActionPriority.MEDIUM
    related_goal: Optional[str] = None


class SuggestedActionUpdate(BaseModel):
    """Schema for updating a suggested action."""
    status: Optional[ActionStatus] = None
    completed_at: Optional[datetime] = None


class SuggestedActionResponse(BaseModel):
    """Schema for suggested action response."""
    id: UUID
    mission_id: UUID
    type: ActionType
    title: str
    description: str
    reasoning: Optional[str] = None
    priority: ActionPriority
    status: ActionStatus
    related_goal: Optional[str] = None
    suggested_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True
