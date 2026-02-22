"""Mission scheduler for autonomous checks."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timezone
from sqlalchemy.orm import Session
import asyncio

from app.database import SessionLocal
from app.models.mission import Mission
from app.services.chat import ChatService
from app.services.notification import NotificationService


class MissionScheduler:
    """Scheduler for autonomous mission checks."""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.notification_service = NotificationService()

    def start(self):
        """Start the scheduler."""
        print("[SCHEDULER] Starting mission scheduler...")

        # Add job to check missions every minute
        # This will find missions that are due for a check
        self.scheduler.add_job(
            func=self.check_due_missions,
            trigger=IntervalTrigger(minutes=1),
            id="check_due_missions",
            name="Check due missions",
            replace_existing=True,
        )

        self.scheduler.start()
        print("[SCHEDULER] Scheduler started")

    def shutdown(self):
        """Shutdown the scheduler."""
        print("[SCHEDULER] Shutting down scheduler...")
        self.scheduler.shutdown()
        print("[SCHEDULER] Scheduler stopped")

    async def check_due_missions(self):
        """Check all missions that are due for an autonomous check."""
        db = SessionLocal()
        try:
            now = datetime.now(timezone.utc)

            # Find missions that are:
            # 1. Active status
            # 2. Not on manual check interval
            # 3. Due for a check (next_check_at is None or in the past)
            missions = (
                db.query(Mission)
                .filter(
                    Mission.status == "active",
                    Mission.check_interval.in_(["hourly", "daily", "weekly"]),
                )
                .all()
            )

            for mission in missions:
                # Check if this mission is due for a check
                is_due = False

                if mission.next_check_at is None:
                    # Never checked before - check it now
                    is_due = True
                elif mission.next_check_at <= now:
                    # Next check time has passed
                    is_due = True

                if is_due:
                    print(f"[SCHEDULER] Mission '{mission.name}' is due for check")
                    await self.perform_mission_check(mission, db)

        except Exception as e:
            print(f"[SCHEDULER] Error in check_due_missions: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

    async def perform_mission_check(self, mission: Mission, db: Session):
        """Perform an autonomous check on a mission.

        Args:
            mission: The mission to check
            db: Database session
        """
        try:
            print(f"[SCHEDULER] Performing autonomous check for: {mission.name}")

            # Create chat service and perform check
            chat_service = ChatService(db)
            result = await chat_service.autonomous_check(mission)

            # Send notification if check was successful
            if result["success"]:
                await self.notification_service.send_check_summary(
                    mission_name=mission.name,
                    suggestions_count=result["suggestions_count"],
                    summary=result["summary"],
                )

                print(f"[SCHEDULER] Check complete for '{mission.name}': {result['suggestions_count']} suggestions")
            else:
                print(f"[SCHEDULER] Check failed for '{mission.name}': {result['summary']}")

        except Exception as e:
            print(f"[SCHEDULER] Error checking mission {mission.id}: {e}")
            import traceback
            traceback.print_exc()


# Global scheduler instance
mission_scheduler = MissionScheduler()
