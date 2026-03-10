"""Tool for creating mission tasks from the agent."""
from datetime import date
from typing import List, Optional
from .base import BaseTool, ToolParameter, ToolResult


class CreateTaskTool(BaseTool):
    """Tool that lets the agent create a task in the mission task list."""

    @property
    def name(self) -> str:
        return "create_task"

    @property
    def description(self) -> str:
        return (
            "Create a task in the mission's task list. "
            "Use this when the user asks you to remember something, create a reminder, "
            "add a to-do item, or track an action that needs to be done. "
            "Always confirm the task details with the user before creating."
        )

    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter(
                name="title",
                type="string",
                description="Brief description of the task (what needs to be done)",
                required=True,
            ),
            ToolParameter(
                name="due_date",
                type="string",
                description="Optional due date in YYYY-MM-DD format (e.g. '2026-03-15'). Only set if the user specified a date or time.",
                required=False,
            ),
        ]

    async def execute(self, **kwargs) -> ToolResult:
        title: str = kwargs.get("title", "").strip()
        due_date_str: Optional[str] = kwargs.get("due_date")
        db_session = kwargs.get("db_session")
        mission_id = kwargs.get("mission_id")

        if not title:
            return ToolResult(success=False, error="Task title is required")
        if not db_session or not mission_id:
            return ToolResult(success=False, error="Internal error: missing db_session or mission_id")

        try:
            from app.models.mission_task import MissionTask
            from sqlalchemy import func

            # Parse due_date if provided
            parsed_due: Optional[date] = None
            if due_date_str:
                try:
                    parsed_due = date.fromisoformat(due_date_str)
                except ValueError:
                    return ToolResult(success=False, error=f"Invalid due_date format: '{due_date_str}'. Use YYYY-MM-DD.")

            # Determine sort_order (place at end of active list)
            max_order = (
                db_session.query(MissionTask.sort_order)
                .filter(MissionTask.mission_id == mission_id, MissionTask.status != "done")
                .order_by(MissionTask.sort_order.desc())
                .limit(1)
                .scalar()
            )

            task = MissionTask(
                mission_id=mission_id,
                title=title,
                due_date=parsed_due,
                status="open",
                sort_order=(max_order or 0) + 1,
            )
            db_session.add(task)
            db_session.commit()
            db_session.refresh(task)

            result = {
                "task_id": str(task.id),
                "title": task.title,
                "due_date": str(task.due_date) if task.due_date else None,
                "status": task.status,
            }
            return ToolResult(success=True, data=result)

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to create task: {str(e)}")
