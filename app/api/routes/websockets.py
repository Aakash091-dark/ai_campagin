# app/api/routes/websockets.py
#
# WebSocket endpoint for streaming AI responses.
#
# Auth: client must send {"token": "<jwt>"} as the first message.
#       The server validates it before processing any chat messages.
#
# Protocol:
#   Client → {"token": "<jwt>"}                          (handshake)
#   Server → {"type": "auth_ok", "user_id": N}
#
#   Client → {"message": "...", "conversation_id": "..."}
#   Server → {"type": "chunk",  "content": "..."}  (repeated)
#   Server → {"type": "done",   "openui_response": "...", ...}
#   Server → {"type": "error",  "content": "..."}  (on failure)

import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt as jose_jwt, JWTError

from app.config.settings import settings
from app.config.database import get_db
from app.core.streaming.websocket_manager import manager
from app.core.streaming.ai_streamer import stream_ws
from app.core.memory.conversation_memory import ensure_conversation, save_message_memory
from app.core.memory.context_builder import build_context
from app.api.routes.chat import resolve_workspace_id
from app.config.logging import get_logger

router = APIRouter()
logger = get_logger("websocket-routes")


# =========================================================
# AI STREAM SOCKET
# =========================================================
@router.websocket("/chat/{client_id}")
async def websocket_chat(
    websocket: WebSocket,
    client_id: str,
):
    await manager.connect(websocket, client_id)
    user_info: dict | None = None

    try:
        # ── Step 1: auth handshake ─────────────────────────────────
        raw = await websocket.receive_json()
        token = raw.get("token", "")

        try:
            payload = jose_jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
            )
            user_id = int(payload["sub"])
            user_info = {
                "user_id": user_id,
                "email": payload.get("email", ""),
                "role": payload.get("role", "user"),
            }
        except (JWTError, KeyError, ValueError) as exc:
            await websocket.send_json({"type": "auth_error", "content": "Invalid token"})
            logger.warning("WS auth failed", client_id=client_id, error=str(exc))
            await websocket.close(code=4001)
            return

        await websocket.send_json({"type": "auth_ok", "user_id": user_info["user_id"]})
        logger.info("WS authenticated", client_id=client_id, user_id=user_info["user_id"])

        # ── Step 2: message loop ───────────────────────────────────
        async for db in get_db():
            while True:
                try:
                    data = await websocket.receive_json()
                except WebSocketDisconnect:
                    raise

                message = data.get("message", "").strip()
                if not message:
                    continue

                conversation_id = data.get("conversation_id") or str(uuid.uuid4())

                # Resolve workspace from DB
                try:
                    workspace_id = await resolve_workspace_id(
                        db=db,
                        user_id=user_info["user_id"],
                        provided_workspace_id=data.get("workspace_id"),
                    )
                except Exception as exc:
                    await websocket.send_json({"type": "error", "content": str(exc)})
                    continue

                # Ensure conversation exists
                await ensure_conversation(
                    db=db,
                    workspace_id=workspace_id,
                    conversation_id=conversation_id,
                    user_id=user_info["user_id"],
                )

                # Save user message
                await save_message_memory(
                    db=db,
                    workspace_id=workspace_id,
                    conversation_id=conversation_id,
                    role="user",
                    content=message,
                    user_id=user_info["user_id"],
                )

                # Build memory context
                memory_context = await build_context(
                    db=db,
                    workspace_id=workspace_id,
                    conversation_id=conversation_id,
                    user_message=message,
                )

                logger.info(
                    "WS chat request",
                    client_id=client_id,
                    workspace_id=workspace_id,
                    conversation_id=conversation_id,
                )

                # Stream response (full pipeline)
                await stream_ws(
                    websocket=websocket,
                    workspace_id=workspace_id,
                    message=message,
                    conversation_id=conversation_id,
                    user_id=user_info["user_id"],
                    memory_context=memory_context,
                    db=db,
                )

    except WebSocketDisconnect:
        manager.disconnect(client_id)
        logger.info("WS disconnected", client_id=client_id)
    except Exception as exc:
        logger.error("WS error", client_id=client_id, error=str(exc))
        try:
            await websocket.send_json({"type": "error", "content": str(exc)})
        except Exception:
            pass
        manager.disconnect(client_id)
