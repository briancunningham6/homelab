"""Integration settings API endpoints (Tavily, etc.)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.models.app_setting import AppSetting
from app.utils.encryption import encrypt_api_key, decrypt_api_key


router = APIRouter(prefix="/api/integrations", tags=["integrations"])

# Registry of known integrations
INTEGRATIONS = [
    {
        "key": "tavily_api_key",
        "display_name": "Tavily",
        "description": "Web search for agents. Get your key at https://tavily.com",
    },
]


class IntegrationResponse(BaseModel):
    key: str
    display_name: str
    description: str
    has_value: bool


class IntegrationUpdate(BaseModel):
    api_key: str


@router.get("/", response_model=List[IntegrationResponse])
async def list_integrations(db: Session = Depends(get_db)):
    """List all integrations and whether they have a key configured."""
    result = []
    for integration in INTEGRATIONS:
        setting = db.query(AppSetting).filter(AppSetting.key == integration["key"]).first()
        result.append(
            IntegrationResponse(
                key=integration["key"],
                display_name=integration["display_name"],
                description=integration["description"],
                has_value=bool(setting and setting.value_encrypted),
            )
        )
    return result


@router.put("/{key}")
async def update_integration(
    key: str,
    update_data: IntegrationUpdate,
    db: Session = Depends(get_db),
):
    """Save an integration API key (encrypted)."""
    if key not in {i["key"] for i in INTEGRATIONS}:
        raise HTTPException(status_code=404, detail="Integration not found")

    if not update_data.api_key.strip():
        raise HTTPException(status_code=400, detail="API key cannot be empty")

    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        setting.value_encrypted = encrypt_api_key(update_data.api_key)
    else:
        setting = AppSetting(key=key, value_encrypted=encrypt_api_key(update_data.api_key))
        db.add(setting)

    db.commit()
    return {"message": "API key saved"}


@router.delete("/{key}/key")
async def delete_integration_key(key: str, db: Session = Depends(get_db)):
    """Remove an integration API key."""
    if key not in {i["key"] for i in INTEGRATIONS}:
        raise HTTPException(status_code=404, detail="Integration not found")

    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if setting:
        setting.value_encrypted = None
        db.commit()

    return {"message": "API key removed"}


def get_integration_value(key: str, db: Session) -> str | None:
    """Helper to retrieve and decrypt an integration key value."""
    setting = db.query(AppSetting).filter(AppSetting.key == key).first()
    if not setting or not setting.value_encrypted:
        return None
    return decrypt_api_key(setting.value_encrypted)
