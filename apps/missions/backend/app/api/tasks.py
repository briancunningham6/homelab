"""Tasks API — per-mission task list."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from app.database import get_db
from app.models.mission import Mission
from app.models.mission_task import MissionTask
from app.schemas.task import TaskCreate, TaskUpdate, TaskReorderItem, TaskResponse

router = APIRouter(prefix="/api/missions/{mission_id}/tasks")


def _get_mission_or_404(mission_id: UUID, db: Session) -> Mission:
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")
    return mission


@router.get("/", response_model=List[TaskResponse])
def list_tasks(mission_id: UUID, db: Session = Depends(get_db)):
    """List all tasks for a mission.

    Active tasks are sorted by sort_order ascending.
    Done tasks come after, sorted by completed_at descending.
    """
    _get_mission_or_404(mission_id, db)

    active = (
        db.query(MissionTask)
        .filter(MissionTask.mission_id == mission_id, MissionTask.status != "done")
        .order_by(MissionTask.sort_order.asc(), MissionTask.created_at.asc())
        .all()
    )
    done = (
        db.query(MissionTask)
        .filter(MissionTask.mission_id == mission_id, MissionTask.status == "done")
        .order_by(MissionTask.completed_at.desc())
        .all()
    )
    return active + done


@router.post("/", response_model=TaskResponse, status_code=201)
def create_task(mission_id: UUID, body: TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    _get_mission_or_404(mission_id, db)

    # Place at end of active list
    max_order = (
        db.query(MissionTask.sort_order)
        .filter(MissionTask.mission_id == mission_id, MissionTask.status != "done")
        .order_by(MissionTask.sort_order.desc())
        .scalar()
    )
    next_order = (max_order or 0) + 1

    task = MissionTask(
        mission_id=mission_id,
        title=body.title,
        due_date=body.due_date,
        status="open",
        sort_order=next_order,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(mission_id: UUID, task_id: UUID, body: TaskUpdate, db: Session = Depends(get_db)):
    """Update a task's title, due date, or status."""
    task = (
        db.query(MissionTask)
        .filter(MissionTask.id == task_id, MissionTask.mission_id == mission_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if body.title is not None:
        task.title = body.title
    if body.due_date is not None:
        if body.due_date != task.due_date:
            # Re-arm the reminder when the due date changes
            task.reminder_sent = False
        task.due_date = body.due_date
    if body.status is not None:
        task.status = body.status
        if body.status == "done" and task.completed_at is None:
            task.completed_at = datetime.now(timezone.utc)
        elif body.status != "done":
            task.completed_at = None

    task.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(mission_id: UUID, task_id: UUID, db: Session = Depends(get_db)):
    """Delete a task."""
    task = (
        db.query(MissionTask)
        .filter(MissionTask.id == task_id, MissionTask.mission_id == mission_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()


@router.post("/reorder", status_code=204)
def reorder_tasks(mission_id: UUID, body: List[TaskReorderItem], db: Session = Depends(get_db)):
    """Update sort_order for a list of tasks (active/in_progress only)."""
    _get_mission_or_404(mission_id, db)

    for item in body:
        db.query(MissionTask).filter(
            MissionTask.id == item.id,
            MissionTask.mission_id == mission_id,
        ).update({"sort_order": item.sort_order})

    db.commit()
