"""Message attachment model for images and files in chat."""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class MessageAttachment(Base):
    """File attachments for chat messages (images, documents, etc)."""

    __tablename__ = "message_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)

    # File info
    filename = Column(String(255), nullable=False)  # UUID-based filename
    original_name = Column(String(255), nullable=False)  # User's filename
    mime_type = Column(String(100))
    size_bytes = Column(Integer)

    # Storage
    storage_path = Column(Text, nullable=False)  # Relative path from data/files/

    # Vision API results (for images)
    description = Column(Text)  # AI-generated description of image
    extracted_text = Column(Text)  # OCR/text from image
    vision_model = Column(String(100))  # Model used for vision analysis

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    message = relationship("Message", back_populates="attachments")
