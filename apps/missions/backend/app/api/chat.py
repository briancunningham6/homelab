"""Chat WebSocket endpoint."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from uuid import UUID
import json

from app.database import get_db
from app.services.chat import ChatService


router = APIRouter(tags=["chat"])


@router.websocket("/api/missions/{mission_id}/chat")
async def chat_websocket(
    websocket: WebSocket,
    mission_id: UUID,
    db: Session = Depends(get_db),
):
    """WebSocket endpoint for streaming chat.

    Protocol:
        Client sends: {"type": "message", "content": "user message"}
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
            if not user_content:
                await websocket.send_json(
                    {"type": "error", "content": "Empty message"}
                )
                continue

            # Stream response
            try:
                async for chunk in chat_service.stream_chat(mission_id, user_content):
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
