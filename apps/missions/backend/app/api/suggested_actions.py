"""Suggested actions endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.mission import Mission
from app.models.suggested_action import SuggestedAction
from app.schemas.suggested_action import (
    SuggestedActionCreate,
    SuggestedActionUpdate,
    SuggestedActionResponse,
)

router = APIRouter()


@router.get("/{mission_id}/suggested-actions", response_model=List[SuggestedActionResponse])
async def list_suggested_actions(
    mission_id: UUID,
    status: str = None,
    db: Session = Depends(get_db),
):
    """List suggested actions for a mission."""
    # Check mission exists
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    query = db.query(SuggestedAction).filter(SuggestedAction.mission_id == mission_id)

    # Filter by status if provided
    if status:
        query = query.filter(SuggestedAction.status == status)

    actions = query.order_by(
        SuggestedAction.priority.desc(),
        SuggestedAction.suggested_at.desc()
    ).all()

    return actions


@router.post("/{mission_id}/suggested-actions", response_model=SuggestedActionResponse, status_code=201)
async def create_suggested_action(
    mission_id: UUID,
    action: SuggestedActionCreate,
    db: Session = Depends(get_db),
):
    """Create a new suggested action."""
    # Check mission exists
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    suggested_action = SuggestedAction(
        mission_id=mission_id,
        type=action.type,
        title=action.title,
        description=action.description,
        reasoning=action.reasoning,
        priority=action.priority,
        related_goal=action.related_goal,
    )

    db.add(suggested_action)
    db.commit()
    db.refresh(suggested_action)

    return suggested_action


@router.patch("/{mission_id}/suggested-actions/{action_id}", response_model=SuggestedActionResponse)
async def update_suggested_action(
    mission_id: UUID,
    action_id: UUID,
    update: SuggestedActionUpdate,
    db: Session = Depends(get_db),
):
    """Update a suggested action (change status, mark completed)."""
    action = (
        db.query(SuggestedAction)
        .filter(
            SuggestedAction.id == action_id,
            SuggestedAction.mission_id == mission_id,
        )
        .first()
    )

    if not action:
        raise HTTPException(status_code=404, detail="Suggested action not found")

    if update.status:
        action.status = update.status

    if update.completed_at:
        action.completed_at = update.completed_at

    db.commit()
    db.refresh(action)

    return action


@router.delete("/{mission_id}/suggested-actions/{action_id}", status_code=204)
async def delete_suggested_action(
    mission_id: UUID,
    action_id: UUID,
    db: Session = Depends(get_db),
):
    """Delete a suggested action."""
    action = (
        db.query(SuggestedAction)
        .filter(
            SuggestedAction.id == action_id,
            SuggestedAction.mission_id == mission_id,
        )
        .first()
    )

    if not action:
        raise HTTPException(status_code=404, detail="Suggested action not found")

    db.delete(action)
    db.commit()
