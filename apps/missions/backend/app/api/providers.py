"""LLM Provider API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.models.llm_provider import LLMProvider
from app.utils.encryption import encrypt_api_key, decrypt_api_key


router = APIRouter(prefix="/api/providers", tags=["providers"])


# Schemas
class ProviderBase(BaseModel):
    name: str
    display_name: str
    default_model: str | None = None
    is_enabled: bool = True


class ProviderCreate(ProviderBase):
    api_key: str  # Plain text - will be encrypted


class ProviderUpdate(BaseModel):
    api_key: str | None = None
    default_model: str | None = None
    is_enabled: bool | None = None


class ProviderResponse(ProviderBase):
    id: UUID
    has_api_key: bool  # Don't expose the actual key
    created_at: str
    updated_at: str | None

    class Config:
        from_attributes = True


# Endpoints
@router.get("/", response_model=List[ProviderResponse])
async def list_providers(db: Session = Depends(get_db)):
    """List all LLM providers."""
    providers = db.query(LLMProvider).all()

    # Transform to response format
    response = []
    for provider in providers:
        response.append(
            ProviderResponse(
                id=provider.id,
                name=provider.name,
                display_name=provider.display_name,
                default_model=provider.default_model,
                is_enabled=provider.is_enabled,
                has_api_key=bool(provider.api_key_encrypted),
                created_at=provider.created_at.isoformat() if provider.created_at else "",
                updated_at=provider.updated_at.isoformat() if provider.updated_at else None,
            )
        )

    return response


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: UUID, db: Session = Depends(get_db)):
    """Get a specific provider."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        default_model=provider.default_model,
        is_enabled=provider.is_enabled,
        has_api_key=bool(provider.api_key_encrypted),
        created_at=provider.created_at.isoformat() if provider.created_at else "",
        updated_at=provider.updated_at.isoformat() if provider.updated_at else None,
    )


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: UUID,
    update_data: ProviderUpdate,
    db: Session = Depends(get_db),
):
    """Update provider settings (API key, model, enabled status)."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Update fields
    if update_data.api_key is not None:
        provider.api_key_encrypted = encrypt_api_key(update_data.api_key)

    if update_data.default_model is not None:
        provider.default_model = update_data.default_model

    if update_data.is_enabled is not None:
        provider.is_enabled = update_data.is_enabled

    db.commit()
    db.refresh(provider)

    return ProviderResponse(
        id=provider.id,
        name=provider.name,
        display_name=provider.display_name,
        default_model=provider.default_model,
        is_enabled=provider.is_enabled,
        has_api_key=bool(provider.api_key_encrypted),
        created_at=provider.created_at.isoformat() if provider.created_at else "",
        updated_at=provider.updated_at.isoformat() if provider.updated_at else None,
    )


@router.delete("/{provider_id}/api-key")
async def delete_api_key(provider_id: UUID, db: Session = Depends(get_db)):
    """Remove API key from provider."""
    provider = db.query(LLMProvider).filter(LLMProvider.id == provider_id).first()

    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    provider.api_key_encrypted = None
    db.commit()

    return {"message": "API key removed"}
