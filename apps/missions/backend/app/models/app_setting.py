"""App settings model for storing integration keys and configuration."""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.sql import func

from app.database import Base


class AppSetting(Base):
    """Key-value store for app-level settings (API keys, config)."""

    __tablename__ = "app_settings"

    key = Column(String(100), primary_key=True)
    value_encrypted = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
