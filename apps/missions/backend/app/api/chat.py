"""Chat WebSocket endpoint."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from uuid import UUID
import json
import base64
import uuid
from pathlib import Path

from app.database import get_db
from app.services.chat import ChatService
from app.models.mission_file import MissionFile
from app.models.message_attachment import MessageAttachment


router = APIRouter(tags=["chat"])


@router.websocket("/api/missions/{mission_id}/chat")
async def chat_websocket(
    websocket: WebSocket,
    mission_id: UUID,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for streaming chat.

    Protocol:
        Client sends: {"type": "message", "content": "user message", "attachments": [...]}
        Server sends: {"type": "content", "content": "streaming text"}
                     {"type": "done", "message_id": "...", "tokens": {...}}
                     {"type": "error", "content": "error message"}
    """
    await websocket.accept()

    chat_service = ChatService(db)

    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json(
                    {"type": "error", "content": "Invalid JSON format"}
                )
                continue

            if message.get("type") != "message":
                await websocket.send_json(
                    {"type": "error", "content": "Invalid message type"}
                )
                continue

            user_content = message.get("content", "")
            attachments_data = message.get("attachments", [])

            if not user_content and not attachments_data:
                await websocket.send_json(
                    {"type": "error", "content": "Empty message"}
                )
                continue

            # Handle file attachments if present
            attachment_ids = []
            if attachments_data:
                try:
                    FILES_DIR = Path("/app/data/files")
                    mission_dir = FILES_DIR / str(mission_id)
                    mission_dir.mkdir(parents=True, exist_ok=True)

                    for att in attachments_data:
                        # Save file
                        file_data = base64.b64decode(att["data"])
                        file_id = UUID(hex=uuid.uuid4().hex)
                        storage_path = f"{mission_id}/{file_id}{Path(att['filename']).suffix}"
                        file_path = FILES_DIR / storage_path

                        with open(file_path, "wb") as f:
                            f.write(file_data)

                        # Create mission file record
                        mission_file = MissionFile(
                            id=file_id,
                            mission_id=mission_id,
                            original_name=att["filename"],
                            storage_path=storage_path,
                            mime_type=att.get("mime_type"),
                            size_bytes=att.get("size", len(file_data)),
                        )
                        db.add(mission_file)
                        db.commit()

                        attachment_ids.append(str(file_id))

                        # If it's an image, add a note to the user message
                        if att.get("mime_type", "").startswith("image/"):
                            if user_content:
                                user_content += f"\n\n[Image attached: {att['filename']}]"
                            else:
                                user_content = f"[Image attached: {att['filename']}]"

                except Exception as e:
                    await websocket.send_json(
                        {"type": "error", "content": f"Error saving attachments: {str(e)}"}
                    )
                    continue

            # Stream response
            try:
                async for chunk in chat_service.stream_chat(
                    mission_id, user_content, attachment_ids=attachment_ids
                ):
                    await websocket.send_json(chunk)
            except Exception as e:
                await websocket.send_json(
                    {"type": "error", "content": f"Error processing message: {str(e)}"}
                )

    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json(
                {"type": "error", "content": f"WebSocket error: {str(e)}"}
            )
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass
