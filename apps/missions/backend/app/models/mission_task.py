"""Mission task model."""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Date, Integer, Boolean, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base


class MissionTask(Base):
    """A task belonging to a mission."""

    __tablename__ = "mission_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)

    title = Column(Text, nullable=False)
    due_date = Column(Date, nullable=True)

    # open | in_progress | done
    status = Column(String(20), nullable=False, default="open")

    # Lower = higher in the list; only meaningful for open/in_progress tasks
    sort_order = Column(Integer, nullable=False, default=0)

    # Set to True once a due-date reminder notification has been sent
    reminder_sent = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    mission = relationship("Mission", back_populates="tasks")
