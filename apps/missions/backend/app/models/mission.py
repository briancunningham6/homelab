"""Mission model."""
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Mission(Base):
    """Mission model."""

    __tablename__ = "missions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    goals = Column(Text, nullable=False)

    # Foreign keys
    category_id = Column(UUID(as_uuid=True), ForeignKey("categories.id"))
    llm_provider_id = Column(UUID(as_uuid=True), ForeignKey("llm_providers.id"))

    # Agent configuration
    model_override = Column(String(100))  # Override provider's default model
    autonomy_level = Column(String(20), default="balanced")

    # Scheduling
    check_interval = Column(String(20), default="daily")  # hourly, daily, weekly, manual
    last_checked_at = Column(DateTime(timezone=True))
    next_check_at = Column(DateTime(timezone=True))

    # Notes — freeform markdown, included verbatim in the agent's system prompt
    notes = Column(Text)

    # Status
    status = Column(String(20), default="active")  # active, paused, completed, archived

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="missions")
    llm_provider = relationship("LLMProvider", back_populates="missions")
    files = relationship("MissionFile", back_populates="mission", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="mission", cascade="all, delete-orphan")
    suggested_actions = relationship("SuggestedAction", back_populates="mission", cascade="all, delete-orphan")
    tasks = relationship("MissionTask", back_populates="mission", cascade="all, delete-orphan")
