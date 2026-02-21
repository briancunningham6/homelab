"""Mission file model."""
from sqlalchemy import Column, String, Text, BigInteger, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class MissionFile(Base):
    """Mission file/context model."""

    __tablename__ = "mission_files"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False)

    # File metadata
    filename = Column(String(255), nullable=False)  # Unique filename on disk
    original_name = Column(String(255), nullable=False)  # Original uploaded name
    mime_type = Column(String(100))
    size_bytes = Column(BigInteger)
    storage_path = Column(Text, nullable=False)  # Relative path in ./data/files/

    # Parsed content (filled in Phase 3)
    extracted_text = Column(Text)
    parsed_metadata = Column(JSONB)

    # Timestamp
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    mission = relationship("Mission", back_populates="files")
