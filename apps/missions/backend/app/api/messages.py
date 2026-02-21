"""Message API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.models.message import Message
from app.models.mission import Mission


router = APIRouter(prefix="/api/missions/{mission_id}/messages", tags=["messages"])


# Schemas
class MessageCreate(BaseModel):
    role: str
    content: str


class MessageResponse(BaseModel):
    id: UUID
    mission_id: UUID
    role: str
    content: str
    tool_name: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    model_used: str | None = None
    created_at: str

    class Config:
        from_attributes = True


# Endpoints
@router.get("/", response_model=List[MessageResponse])
async def get_messages(mission_id: UUID, db: Session = Depends(get_db)):
    """Get all messages for a mission."""
    # Verify mission exists
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    messages = (
        db.query(Message)
        .filter(Message.mission_id == mission_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    return [
        MessageResponse(
            id=msg.id,
            mission_id=msg.mission_id,
            role=msg.role,
            content=msg.content,
            tool_name=msg.tool_name,
            input_tokens=msg.input_tokens,
            output_tokens=msg.output_tokens,
            model_used=msg.model_used,
            created_at=msg.created_at.isoformat() if msg.created_at else "",
        )
        for msg in messages
    ]


@router.post("/", response_model=MessageResponse, status_code=201)
async def create_message(
    mission_id: UUID,
    message_data: MessageCreate,
    db: Session = Depends(get_db),
):
    """Create a new message (for direct message creation, not via chat)."""
    # Verify mission exists
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    message = Message(
        mission_id=mission_id,
        role=message_data.role,
        content=message_data.content,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return MessageResponse(
        id=message.id,
        mission_id=message.mission_id,
        role=message.role,
        content=message.content,
        tool_name=message.tool_name,
        input_tokens=message.input_tokens,
        output_tokens=message.output_tokens,
        model_used=message.model_used,
        created_at=message.created_at.isoformat() if message.created_at else "",
    )


@router.delete("/{message_id}")
async def delete_message(
    mission_id: UUID,
    message_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a message."""
    message = (
        db.query(Message)
        .filter(Message.id == message_id, Message.mission_id == mission_id)
        .first()
    )

    if not message:
        raise HTTPException(status_code=404, detail="Message not found")

    db.delete(message)
    db.commit()

    return {"message": "Message deleted"}
