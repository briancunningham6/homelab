"""Category model."""
from sqlalchemy import Column, String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Category(Base):
    """Mission category model."""

    __tablename__ = "categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    color = Column(String(7))  # Hex color code
    icon = Column(String(50))  # MDI icon name
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    missions = relationship("Mission", back_populates="category")
