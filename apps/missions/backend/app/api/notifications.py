"""Notifications API — send and test push notifications via ntfy."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.mission import Mission
from app.services.notification import NotificationService

router = APIRouter(prefix="/api/notifications")
notification_service = NotificationService()


class TestNotificationRequest(BaseModel):
    mission_id: Optional[str] = None
    title: str = "Test Notification"
    message: str = "Missions notifications are working."
    priority: str = "default"


class SendNotificationRequest(BaseModel):
    mission_id: str
    title: str
    message: str
    priority: str = "default"
    tags: Optional[list[str]] = None


@router.post("/test")
async def send_test_notification(
    body: TestNotificationRequest,
    db: Session = Depends(get_db),
):
    """Send a test notification to verify ntfy is working."""
    mission_name = "Test"
    mission_id = body.mission_id

    if mission_id:
        mission = db.query(Mission).filter(Mission.id == mission_id).first()
        if mission:
            mission_name = mission.name

    success = await notification_service.send_mission_alert(
        mission_name=mission_name,
        title=body.title,
        message=body.message,
        priority=body.priority,
        tags=["bell", "white_check_mark"],
        mission_id=mission_id,
    )

    if not success:
        raise HTTPException(status_code=502, detail="Failed to send notification — check ntfy is running")

    return {"sent": True}


@router.post("/send")
async def send_notification(
    body: SendNotificationRequest,
    db: Session = Depends(get_db),
):
    """Send a custom notification for a mission."""
    mission = db.query(Mission).filter(Mission.id == body.mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    success = await notification_service.send_mission_alert(
        mission_name=mission.name,
        title=body.title,
        message=body.message,
        priority=body.priority,
        tags=body.tags,
        mission_id=str(mission.id),
    )

    if not success:
        raise HTTPException(status_code=502, detail="Failed to send notification")

    return {"sent": True}
