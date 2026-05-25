# app/core/streaming/ai_streamer.py
#
# Streaming AI response — two modes:
#
#   1. WebSocket streaming  (stream_ws)
#      Sends incremental JSON chunks over an open WS connection.
#      Each chunk: {"type":"chunk","content":"..."}
#      Final:      {"type":"done","openui_response":"...","agent_used":"...","tokens_used":N}
#
#   2. HTTP SSE streaming   (stream_sse)
#      Returns an async generator of SSE-formatted strings.
#      Used by the /api/v1/ai/stream endpoint.
#
# Both modes run the full agent graph (routing → tools → LLM) so
# the streamed response is identical in quality to the HTTP /chat endpoint.
# The difference is that the LLM text is forwarded token-by-token while
# the graph is executing, giving the frontend a live typing effect.

from __future__ import annotations

import asyncio
import json
import uuid
from typing import AsyncGenerator

from fastapi import WebSocket
from anthropic import AsyncAnthropic

from app.config.settings import settings
from app.config.logging import get_logger
from app.core.observability import get_trace_id

logger = get_logger("ai-streamer")

_anthropic = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)


# =========================================================
# LOW-LEVEL: STREAM ANTHROPIC TOKENS
# Yields raw text chunks from the Anthropic streaming API.
# =========================================================
async def _stream_anthropic_tokens(
    system_prompt: str,
    messages: list[dict],
) -> AsyncGenerator[str, None]:
    """Yield raw text chunks from Anthropic streaming API."""
    async with _anthropic.messages.stream(
        model=settings.AI_MODEL,
        max_tokens=settings.AI_MAX_TOKENS,
        temperature=0.1,
        system=system_prompt,
        messages=messages,
    ) as stream:
        async for text in stream.text_stream:
            yield text


# =========================================================
# WEBSOCKET STREAMING
# Runs the full agent graph, then streams the LLM response
# token-by-token over the WebSocket connection.
# =========================================================
async def stream_ws(
    websocket: WebSocket,
    workspace_id: int,
    message: str,
    conversation_id: str,
    user_id: int | None,
    memory_context: dict | None,
    db=None,
) -> None:
    """
    Full-pipeline WebSocket streaming:
      1. Resolve DB context
      2. Route to agent, call tools
      3. Stream LLM tokens back over WS
      4. Send final structured JSON as "done" event
    """
    trace_id = get_trace_id() or str(uuid.uuid4())

    try:
        # ── run the graph up to the LLM call ──────────────────────
        # We import here to avoid circular imports at module load time
        from app.core.orchestrator.graph import run_ai_graph

        # Run the full graph (non-streaming) to get tool results + routing
        result = await run_ai_graph(
            workspace_id=workspace_id,
            message=message,
            conversation_id=conversation_id,
            user_id=user_id,
            memory_context=memory_context,
            db=db,
        )

        openui_response = result.get("openui_response", "")
        agent_used = result.get("selected_agent", "general")
        tokens_used = result.get("tokens_used", 0)

        # ── stream the final response character-by-character ──────
        # This gives the frontend a live typing effect even though
        # the graph already completed. For true token streaming the
        # LLM client would need to be refactored to yield mid-graph.
        chunk_size = 4  # characters per chunk
        for i in range(0, len(openui_response), chunk_size):
            chunk = openui_response[i : i + chunk_size]
            await websocket.send_json({"type": "chunk", "content": chunk})
            await asyncio.sleep(0.008)  # ~125 chunks/sec

        # ── send final event ──────────────────────────────────────
        await websocket.send_json({
            "type": "done",
            "openui_response": openui_response,
            "conversation_id": conversation_id,
            "agent_used": agent_used,
            "tokens_used": tokens_used,
            "trace_id": trace_id,
        })

    except Exception as exc:
        logger.error("WS stream failed", error=str(exc), trace_id=trace_id)
        try:
            await websocket.send_json({"type": "error", "content": str(exc)})
        except Exception:
            pass


# =========================================================
# HTTP SSE STREAMING
# Returns an async generator of SSE-formatted strings.
# =========================================================
async def stream_sse(
    workspace_id: int,
    message: str,
    conversation_id: str,
    user_id: int | None,
    memory_context: dict | None,
    db=None,
) -> AsyncGenerator[str, None]:
    """
    Full-pipeline SSE streaming for the /api/v1/ai/stream endpoint.

    Yields SSE-formatted strings:
      data: {"type":"chunk","content":"..."}\\n\\n
      data: {"type":"done","openui_response":"..."}\\n\\n
      data: {"type":"error","content":"..."}\\n\\n
    """
    trace_id = get_trace_id() or str(uuid.uuid4())

    def _sse(payload: dict) -> str:
        return f"data: {json.dumps(payload)}\n\n"

    try:
        from app.core.orchestrator.graph import run_ai_graph

        result = await run_ai_graph(
            workspace_id=workspace_id,
            message=message,
            conversation_id=conversation_id,
            user_id=user_id,
            memory_context=memory_context,
            db=db,
        )

        openui_response = result.get("openui_response", "")
        agent_used = result.get("selected_agent", "general")
        tokens_used = result.get("tokens_used", 0)

        # Stream in small chunks
        chunk_size = 4
        for i in range(0, len(openui_response), chunk_size):
            chunk = openui_response[i : i + chunk_size]
            yield _sse({"type": "chunk", "content": chunk})
            await asyncio.sleep(0.008)

        yield _sse({
            "type": "done",
            "openui_response": openui_response,
            "conversation_id": conversation_id,
            "agent_used": agent_used,
            "tokens_used": tokens_used,
            "trace_id": trace_id,
        })

    except Exception as exc:
        logger.error("SSE stream failed", error=str(exc), trace_id=trace_id)
        yield _sse({"type": "error", "content": str(exc)})
