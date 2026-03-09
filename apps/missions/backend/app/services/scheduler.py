"""Mission scheduler for autonomous checks."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from collections import defaultdict
from datetime import datetime, date, timezone
from sqlalchemy.orm import Session
import asyncio

from app.database import SessionLocal
from app.models.mission import Mission
from app.models.mission_task import MissionTask
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

        # Send task due-date reminders every day at 9am
        self.scheduler.add_job(
            func=self.check_due_tasks,
            trigger=CronTrigger(hour=9, minute=0),
            id="check_due_tasks",
            name="Send task due-date reminders",
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
                    mission_id=str(mission.id),
                )

                print(f"[SCHEDULER] Check complete for '{mission.name}': {result['suggestions_count']} suggestions")
            else:
                print(f"[SCHEDULER] Check failed for '{mission.name}': {result['summary']}")

        except Exception as e:
            print(f"[SCHEDULER] Error checking mission {mission.id}: {e}")
            import traceback
            traceback.print_exc()

    async def check_due_tasks(self):
        """Send reminder notifications for tasks due today (or overdue and not yet notified)."""
        db = SessionLocal()
        try:
            today = date.today()

            due_tasks = (
                db.query(MissionTask)
                .join(Mission, MissionTask.mission_id == Mission.id)
                .filter(
                    MissionTask.due_date <= today,
                    MissionTask.status != "done",
                    MissionTask.reminder_sent == False,  # noqa: E712
                )
                .all()
            )

            if not due_tasks:
                print("[SCHEDULER] No task reminders to send")
                return

            # Group tasks by mission so we send one notification per mission
            by_mission: dict = defaultdict(list)
            for task in due_tasks:
                by_mission[task.mission_id].append(task)

            for mission_id, tasks in by_mission.items():
                mission = db.query(Mission).filter(Mission.id == mission_id).first()
                if not mission:
                    continue

                overdue = [t for t in tasks if t.due_date < today]
                due_today = [t for t in tasks if t.due_date == today]

                lines = []
                if due_today:
                    lines.append(f"Due today: {', '.join(t.title for t in due_today)}")
                if overdue:
                    lines.append(f"Overdue: {', '.join(t.title for t in overdue)}")

                count = len(tasks)
                title = f"{count} task{'s' if count != 1 else ''} due"
                message = "\n".join(lines)

                sent = await self.notification_service.send_mission_alert(
                    mission_name=mission.name,
                    title=title,
                    message=message,
                    priority="high",
                    tags=["calendar", "red_circle"],
                    mission_id=str(mission.id),
                )

                if sent:
                    for task in tasks:
                        task.reminder_sent = True
                    db.commit()
                    print(f"[SCHEDULER] Sent task reminders for '{mission.name}': {count} task(s)")

        except Exception as e:
            print(f"[SCHEDULER] Error in check_due_tasks: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()


# Global scheduler instance
mission_scheduler = MissionScheduler()
