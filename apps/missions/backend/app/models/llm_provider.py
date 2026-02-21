"""LLM Provider model."""
from sqlalchemy import Column, String, Text, Boolean, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class LLMProvider(Base):
    """LLM provider configuration model."""

    __tablename__ = "llm_providers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)  # claude, openai
    display_name = Column(String(100), nullable=False)
    api_key_encrypted = Column(Text)  # Fernet encrypted API key
    default_model = Column(String(100))  # e.g., claude-sonnet-4-20250514
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    missions = relationship("Mission", back_populates="llm_provider")
