"""Suggested action model."""
from sqlalchemy import Column, String, Text, Enum, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, ENUM as PG_ENUM
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base


class ActionType(str, enum.Enum):
    """Type of suggested action."""
    USER_ACTION = "user_action"
    AGENT_ACTION = "agent_action"
    INFO_REQUEST = "info_request"


class ActionPriority(str, enum.Enum):
    """Priority level of action."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ActionStatus(str, enum.Enum):
    """Status of suggested action."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DEFERRED = "deferred"
    DISMISSED = "dismissed"
    COMPLETED = "completed"


class SuggestedAction(Base):
    """Suggested actions for mission progress."""

    __tablename__ = "suggested_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)

    # Action details
    type = Column(PG_ENUM(ActionType, name='actiontype', create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False, default=ActionType.AGENT_ACTION)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    reasoning = Column(Text)  # Why the agent suggests this

    # Organization
    priority = Column(PG_ENUM(ActionPriority, name='actionpriority', create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False, default=ActionPriority.MEDIUM)
    status = Column(PG_ENUM(ActionStatus, name='actionstatus', create_type=False, values_callable=lambda x: [e.value for e in x]), nullable=False, default=ActionStatus.PENDING)
    related_goal = Column(Text)  # Link to specific mission goal

    # Timestamps
    suggested_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    accepted_at = Column(DateTime(timezone=True))  # When user accepted the action
    completed_at = Column(DateTime(timezone=True))  # When action was marked complete

    # Relationships
    mission = relationship("Mission", back_populates="suggested_actions")
