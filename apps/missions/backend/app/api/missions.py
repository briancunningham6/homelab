"""Mission CRUD endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from pydantic import BaseModel

from app.database import get_db
from app.models.mission import Mission
from app.schemas.mission import MissionCreate, MissionUpdate, MissionResponse

router = APIRouter()


@router.get("/", response_model=List[MissionResponse])
async def list_missions(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    """List all missions."""
    query = db.query(Mission)

    if status:
        query = query.filter(Mission.status == status)

    missions = query.order_by(Mission.created_at.desc()).all()

    # Add counts
    result = []
    for mission in missions:
        mission_dict = mission.__dict__.copy()
        mission_dict["file_count"] = len(mission.files)
        mission_dict["message_count"] = len(mission.messages)
        result.append(MissionResponse(**mission_dict))

    return result


@router.post("/", response_model=MissionResponse, status_code=201)
async def create_mission(
    mission_data: MissionCreate,
    db: Session = Depends(get_db),
):
    """Create a new mission."""
    mission = Mission(**mission_data.model_dump())
    db.add(mission)
    db.commit()
    db.refresh(mission)

    mission_dict = mission.__dict__.copy()
    mission_dict["file_count"] = 0
    mission_dict["message_count"] = 0

    return MissionResponse(**mission_dict)


@router.get("/{mission_id}", response_model=MissionResponse)
async def get_mission(
    mission_id: UUID,
    db: Session = Depends(get_db),
):
    """Get mission by ID."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission_dict = mission.__dict__.copy()
    mission_dict["file_count"] = len(mission.files)
    mission_dict["message_count"] = len(mission.messages)

    return MissionResponse(**mission_dict)


@router.put("/{mission_id}", response_model=MissionResponse)
async def update_mission(
    mission_id: UUID,
    mission_data: MissionUpdate,
    db: Session = Depends(get_db),
):
    """Update a mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Update fields
    for field, value in mission_data.model_dump(exclude_unset=True).items():
        setattr(mission, field, value)

    db.commit()
    db.refresh(mission)

    mission_dict = mission.__dict__.copy()
    mission_dict["file_count"] = len(mission.files)
    mission_dict["message_count"] = len(mission.messages)

    return MissionResponse(**mission_dict)


class ResetOptions(BaseModel):
    messages: bool = False
    suggested_actions: bool = False
    tasks: bool = False
    notes: bool = False


@router.post("/{mission_id}/reset")
async def reset_mission_data(
    mission_id: UUID,
    options: ResetOptions,
    db: Session = Depends(get_db),
):
    """Selectively clear mission data (messages, suggested actions, tasks, notes)."""
    from app.models.message import Message
    from app.models.suggested_action import SuggestedAction
    from app.models.mission_task import MissionTask

    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    cleared = []

    if options.messages:
        db.query(Message).filter(Message.mission_id == mission_id).delete()
        cleared.append("messages")

    if options.suggested_actions:
        db.query(SuggestedAction).filter(SuggestedAction.mission_id == mission_id).delete()
        cleared.append("suggested_actions")

    if options.tasks:
        db.query(MissionTask).filter(MissionTask.mission_id == mission_id).delete()
        cleared.append("tasks")

    if options.notes:
        mission.notes = None
        cleared.append("notes")

    db.commit()
    return {"cleared": cleared}


@router.delete("/{mission_id}", status_code=204)
async def delete_mission(
    mission_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a mission."""
    mission = db.query(Mission).filter(Mission.id == mission_id).first()

    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    db.delete(mission)
    db.commit()

    return None
