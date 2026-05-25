# app/core/observability.py
#
# Lightweight observability layer.
# Provides:
#   - Structured request tracing (trace_id per HTTP request)
#   - Agent execution spans (start/end/duration/tokens)
#   - Tool call spans (name/args/duration/error)
#   - A FastAPI middleware that injects trace_id into every request
#
# No external APM dependency — uses structlog via the existing
# logging config so all output is already JSON-structured.

from __future__ import annotations

import time
import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from typing import Any

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.logging import get_logger

logger = get_logger("observability")

# ── per-request trace ID stored in a context variable ─────────────
_trace_id_var: ContextVar[str] = ContextVar("trace_id", default="")


def get_trace_id() -> str:
    return _trace_id_var.get()


def set_trace_id(tid: str) -> None:
    _trace_id_var.set(tid)


# =========================================================
# TRACING MIDDLEWARE
# Injects X-Trace-ID into every request and response.
# =========================================================
class TracingMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):
        # Honour an upstream trace ID if provided (e.g. from a gateway)
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        set_trace_id(trace_id)

        start = time.perf_counter()

        logger.info(
            "Request start",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
        )

        response = await call_next(request)

        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        logger.info(
            "Request end",
            trace_id=trace_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            elapsed_ms=elapsed_ms,
        )

        response.headers["X-Trace-ID"] = trace_id
        return response


# =========================================================
# AGENT SPAN
# Context manager that logs agent execution start/end.
# =========================================================
@asynccontextmanager
async def agent_span(agent_name: str, workspace_id: int, user_id: int | None = None):
    """
    Usage:
        async with agent_span("analytics", workspace_id=1, user_id=42):
            result = await run_analytics_agent(state)
    """
    trace_id = get_trace_id()
    start = time.perf_counter()

    logger.info(
        "Agent span start",
        trace_id=trace_id,
        agent=agent_name,
        workspace_id=workspace_id,
        user_id=user_id,
    )

    try:
        yield
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "Agent span end",
            trace_id=trace_id,
            agent=agent_name,
            workspace_id=workspace_id,
            elapsed_ms=elapsed_ms,
            status="ok",
        )
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.error(
            "Agent span error",
            trace_id=trace_id,
            agent=agent_name,
            workspace_id=workspace_id,
            elapsed_ms=elapsed_ms,
            error=str(exc),
        )
        raise


# =========================================================
# TOOL SPAN
# Wraps a single tool call with timing and error logging.
# =========================================================
@asynccontextmanager
async def tool_span(tool_name: str, **kwargs: Any):
    """
    Usage:
        async with tool_span("get_live_campaign_insights", workspace_id=1):
            result = await get_live_campaign_insights(workspace_id=1)
    """
    trace_id = get_trace_id()
    start = time.perf_counter()

    logger.info(
        "Tool span start",
        trace_id=trace_id,
        tool=tool_name,
        kwargs=list(kwargs.keys()),
    )

    try:
        yield
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "Tool span end",
            trace_id=trace_id,
            tool=tool_name,
            elapsed_ms=elapsed_ms,
            status="ok",
        )
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.error(
            "Tool span error",
            trace_id=trace_id,
            tool=tool_name,
            elapsed_ms=elapsed_ms,
            error=str(exc),
        )
        raise


# =========================================================
# LLM SPAN
# Logs LLM call with token usage.
# =========================================================
@asynccontextmanager
async def llm_span(model: str, agent: str):
    """
    Usage:
        async with llm_span(model="claude-sonnet-4", agent="analytics") as span:
            result = await generate_completion(...)
            span["tokens_used"] = result["tokens_used"]
    """
    trace_id = get_trace_id()
    start = time.perf_counter()
    span: dict[str, Any] = {}

    logger.info(
        "LLM span start",
        trace_id=trace_id,
        model=model,
        agent=agent,
    )

    try:
        yield span
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.info(
            "LLM span end",
            trace_id=trace_id,
            model=model,
            agent=agent,
            elapsed_ms=elapsed_ms,
            tokens_used=span.get("tokens_used", 0),
            status="ok",
        )
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)
        logger.error(
            "LLM span error",
            trace_id=trace_id,
            model=model,
            agent=agent,
            elapsed_ms=elapsed_ms,
            error=str(exc),
        )
        raise
