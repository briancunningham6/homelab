"""LLM Provider schemas."""
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional


class LLMProviderResponse(BaseModel):
    """Schema for LLM provider response (without API key)."""

    id: UUID
    name: str
    display_name: str
    default_model: Optional[str] = None
    is_enabled: bool
    has_api_key: bool = False  # Computed field
    created_at: datetime

    class Config:
        from_attributes = True
