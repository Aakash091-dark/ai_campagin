# app/api/routes/chat.py

import time
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.config.database import get_db
from app.core.orchestrator.graph import run_ai_graph
from app.core.memory.context_builder import build_context
from app.core.memory.conversation_memory import save_message_memory, ensure_conversation
from app.api.dependencies.user import get_current_user
from app.config.logging import get_logger

router = APIRouter()
logger = get_logger("chat-routes")


# =========================================================
# RESOLVE WORKSPACE
# =========================================================
async def resolve_workspace_id(
    db: AsyncSession,
    user_id: int,
    provided_workspace_id: int | None = None,
) -> int:
    """
    Use the provided workspace_id if given, otherwise look it up
    from the authenticated user's record in the database.
    """
    if provided_workspace_id is not None:
        return provided_workspace_id

    row = await db.execute(
        text('SELECT workspace_id FROM "user" WHERE id = :uid LIMIT 1'),
        {"uid": user_id},
    )
    result = row.scalar_one_or_none()
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"User {user_id} has no workspace assigned. "
                "Please provide a workspace_id or contact an admin."
            ),
        )
    return int(result)


# =========================================================
# SHARED PIPELINE HELPER
# =========================================================
async def _run_pipeline(
    db: AsyncSession,
    user_id: int,
    message: str,
    workspace_id_hint: int | None,
    conversation_id_hint: str | None,
) -> tuple[dict, str, int]:
    """
    Shared logic for both /chat and /stream:
      - resolve workspace
      - ensure conversation
      - save user message
      - build memory context
      - run agent graph
      - save assistant response

    Returns (graph_result, conversation_id, workspace_id).
    """
    workspace_id = await resolve_workspace_id(
        db=db,
        user_id=user_id,
        provided_workspace_id=workspace_id_hint,
    )

    conversation_id = conversation_id_hint or str(uuid.uuid4())

    await ensure_conversation(
        db=db,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    logger.info(
        "AI request received",
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    await save_message_memory(
        db=db,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        role="user",
        content=message,
        user_id=user_id,
    )

    memory_context = await build_context(
        db=db,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        user_message=message,
    )

    result = await run_ai_graph(
        workspace_id=workspace_id,
        message=message,
        conversation_id=conversation_id,
        user_id=user_id,
        memory_context=memory_context,
        db=db,
    )

    await save_message_memory(
        db=db,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        role="assistant",
        content=result["openui_response"],
        user_id=user_id,
        tools_used=result["tools_used"],
    )

    return result, conversation_id, workspace_id


# =========================================================
# POST /chat  — standard JSON response
# =========================================================
@router.post("/chat", response_model=ChatResponse)
async def ai_chat(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    start_time = time.time()

    try:
        result, conversation_id, _ = await _run_pipeline(
            db=db,
            user_id=current_user["user_id"],
            message=payload.message,
            workspace_id_hint=payload.workspace_id,
            conversation_id_hint=payload.conversation_id,
        )

        return ChatResponse(
            success=result["success"],
            conversation_id=conversation_id,
            openui_response=result["openui_response"],
            execution_time=round(time.time() - start_time, 2),
            agent_used=result["selected_agent"],
            tokens_used=result["tokens_used"],
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("AI chat failed", error=str(exc))
        raise HTTPException(status_code=500, detail=str(exc))


# =========================================================
# POST /stream  — Server-Sent Events streaming response
#
# Frontend usage:
#   const es = new EventSource('/api/v1/ai/stream', {method:'POST', ...})
#   es.onmessage = (e) => {
#     const msg = JSON.parse(e.data)
#     if (msg.type === 'chunk')  appendChunk(msg.content)
#     if (msg.type === 'done')   finalise(msg.openui_response)
#     if (msg.type === 'error')  showError(msg.content)
#   }
# =========================================================
@router.post("/stream")
async def ai_stream(
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """
    Streaming variant of /chat.
    Returns text/event-stream with incremental OpenUI chunks.
    """
    from app.core.streaming.ai_streamer import stream_sse

    user_id = current_user["user_id"]

    # Resolve workspace + conversation IDs before streaming starts
    workspace_id = await resolve_workspace_id(
        db=db,
        user_id=user_id,
        provided_workspace_id=payload.workspace_id,
    )
    conversation_id = payload.conversation_id or str(uuid.uuid4())

    await ensure_conversation(
        db=db,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    await save_message_memory(
        db=db,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        role="user",
        content=payload.message,
        user_id=user_id,
    )

    memory_context = await build_context(
        db=db,
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        user_message=payload.message,
    )

    logger.info(
        "SSE stream request",
        workspace_id=workspace_id,
        conversation_id=conversation_id,
        user_id=user_id,
    )

    return StreamingResponse(
        stream_sse(
            workspace_id=workspace_id,
            message=payload.message,
            conversation_id=conversation_id,
            user_id=user_id,
            memory_context=memory_context,
            db=db,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # disable nginx buffering
            "Connection": "keep-alive",
        },
    )
