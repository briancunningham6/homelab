"""Notification service for sending alerts via ntfy."""
import httpx
import os
from typing import Optional


class NotificationService:
    """Service for sending notifications via ntfy."""

    def __init__(self):
        self.ntfy_url = os.getenv("NTFY_URL", "http://ntfy:80")
        self.ntfy_topic = os.getenv("NTFY_TOPIC", "missions")

    async def send_mission_alert(
        self,
        mission_name: str,
        title: str,
        message: str,
        priority: str = "default",
        tags: Optional[list[str]] = None,
    ) -> bool:
        """Send a mission alert notification.

        Args:
            mission_name: Name of the mission
            title: Notification title
            message: Notification message
            priority: Priority level (min, low, default, high, urgent)
            tags: Optional list of tags/emojis

        Returns:
            bool: True if notification sent successfully
        """
        try:
            # Build notification payload
            headers = {
                "Title": f"Mission: {mission_name}",
                "Priority": priority,
            }

            if tags:
                headers["Tags"] = ",".join(tags)

            # Add click action to open mission detail page
            headers["Click"] = f"http://missions.home/missions/{mission_name}"

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ntfy_url}/{self.ntfy_topic}",
                    headers=headers,
                    data=f"{title}\n\n{message}",
                    timeout=5.0,
                )

                return response.status_code == 200

        except Exception as e:
            print(f"[NOTIFICATIONS] Failed to send notification: {e}")
            return False

    async def send_check_summary(
        self,
        mission_name: str,
        suggestions_count: int,
        summary: str,
    ) -> bool:
        """Send a mission check summary notification.

        Args:
            mission_name: Name of the mission
            suggestions_count: Number of new suggestions
            summary: Brief summary of the check

        Returns:
            bool: True if notification sent successfully
        """
        priority = "high" if suggestions_count > 0 else "low"
        tags = ["robot", "lightbulb"] if suggestions_count > 0 else ["robot", "white_check_mark"]

        title = f"{suggestions_count} New Suggestion{'s' if suggestions_count != 1 else ''}" if suggestions_count > 0 else "Mission Check Complete"

        return await self.send_mission_alert(
            mission_name=mission_name,
            title=title,
            message=summary,
            priority=priority,
            tags=tags,
        )
