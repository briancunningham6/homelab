"""Quick Capture — add files and notes to a mission's context."""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File as FastAPIFile, Form
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID, uuid4
import shutil
from pathlib import Path

from app.database import get_db
from app.models.mission import Mission
from app.models.mission_file import MissionFile
from app.models.message import Message
from app.models.llm_provider import LLMProvider
from app.tools import tool_registry

router = APIRouter()

FILES_DIR = Path("/app/data/files")


@router.post("/api/capture")
async def quick_capture(
    mission_id: UUID = Form(...),
    note: str = Form(""),
    files: List[UploadFile] = FastAPIFile(default=[]),
    db: Session = Depends(get_db),
):
    """Upload files and an optional note into a mission's context.

    Images are automatically analysed with vision so the agent immediately
    understands what was captured. All files appear in the mission's file list
    and in future system prompts.
    """
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Resolve LLM provider for vision analysis
    provider = None
    if mission.llm_provider_id:
        provider = (
            db.query(LLMProvider)
            .filter(LLMProvider.id == mission.llm_provider_id, LLMProvider.is_enabled == True)
            .first()
        )
    if not provider:
        provider = db.query(LLMProvider).filter(LLMProvider.is_enabled == True).first()

    mission_dir = FILES_DIR / str(mission_id)
    mission_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    vision_results = []

    for upload in files:
        if not upload.filename:
            continue

        file_ext = Path(upload.filename).suffix
        unique_filename = f"{uuid4()}{file_ext}"
        file_path = mission_dir / unique_filename

        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(upload.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save {upload.filename}: {e}")

        mission_file = MissionFile(
            mission_id=mission_id,
            filename=unique_filename,
            original_name=upload.filename,
            mime_type=upload.content_type,
            size_bytes=file_path.stat().st_size,
            storage_path=f"{mission_id}/{unique_filename}",
        )
        db.add(mission_file)
        db.flush()  # get the ID before passing to vision tool
        saved_files.append(mission_file)

        # Automatically analyse images so the agent has immediate context
        if provider and upload.content_type and upload.content_type.startswith("image/"):
            try:
                result = await tool_registry.execute(
                    "analyze_image",
                    file_id=str(mission_file.id),
                    prompt=(
                        "Describe this image in detail. Extract any visible text, numbers, "
                        "dates, names, prices, or other key information."
                    ),
                    db_session=db,
                    llm_provider=provider,
                )
                if result.success:
                    description = result.data.get("description", "")
                    mission_file.extracted_text = description
                    vision_results.append({"filename": upload.filename, "description": description})
            except Exception:
                pass  # vision failure is non-fatal — file is still saved

    db.commit()

    # Build a user message that goes into the mission's chat history so the
    # agent sees what was captured and why.
    lines = ["📎 **Quick Capture**"]

    if note.strip():
        lines.append(f"\n{note.strip()}")

    if saved_files:
        lines.append(f"\n**{len(saved_files)} file(s) added to context:**")
        for f in saved_files:
            lines.append(f"- {f.original_name}")

    for vr in vision_results:
        lines.append(f"\n**Image analysis — {vr['filename']}:**\n{vr['description']}")

    user_message = Message(
        mission_id=mission_id,
        role="user",
        content="\n".join(lines),
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    return {
        "mission_id": str(mission_id),
        "mission_name": mission.name,
        "file_count": len(saved_files),
        "message_id": str(user_message.id),
    }
