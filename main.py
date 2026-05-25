# main.py

import uvicorn

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.responses import (
    HTMLResponse,
    ORJSONResponse,
)

from app.config.settings import (
    settings,
)

from app.config.database import (
    init_db,
)

from app.config.redis import (
    init_redis,
)

from app.config.logging import (
    setup_logging,
)

from app.api.routes.chat import (
    router as chat_router,
)

from app.api.routes.health import (
    router as health_router,
)

from app.api.routes.memory import (
    router as memory_router,
)

from app.api.routes.conversations import (
    router as conversations_router,
)

from app.api.routes.websockets import (
    router as websocket_router,
)

from app.api.routes.test import (
    router as test_router,
)

from app.api.middleware.rate_limit import (
    RateLimitMiddleware,
)
from app.api.middleware.auth import (
    AuthMiddleware,
)
from app.core.observability import TracingMiddleware
from app.tools.registry import register_all_tools

from app.core.ui.chat_ui import (
    CHAT_UI_HTML,
)

# =========================================================
# APP LIFECYCLE
# =========================================================
@asynccontextmanager
async def lifespan(app: FastAPI):

    setup_logging()

    print("Starting Lemonmaxx AI...")

    await init_db()
    await init_redis()

    # Register all tools in the central registry
    register_all_tools()

    print("Lemonmaxx AI started")

    yield

    print(
        "Shutting down Lemonmaxx AI..."
    )


# =========================================================
# FASTAPI APP
# =========================================================
app = FastAPI(
    title="Lemonmaxx AI",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=ORJSONResponse,
)

# =========================================================
# CORS
# =========================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Tracing — injects X-Trace-ID, logs every request with timing
app.add_middleware(TracingMiddleware)
app.add_middleware(AuthMiddleware)
# =========================================================
# RATE LIMIT
# =========================================================
app.add_middleware(RateLimitMiddleware)

# =========================================================
# ROUTES
# =========================================================
app.include_router(
    health_router,
    prefix="/health",
    tags=["Health"],
)

app.include_router(
    chat_router,
    prefix="/api/v1/ai",
    tags=["AI"],
)

app.include_router(
    memory_router,
    prefix="/api/v1/memory",
    tags=["Memory"],
)

app.include_router(
    conversations_router,
    prefix="/api/v1/conversations",
    tags=["Conversations"],
)

app.include_router(
    websocket_router,
    prefix="/ws",
    tags=["WebSocket"],
)

app.include_router(
    test_router,
    prefix="/api/v1/test",
    tags=["Test"],
)


# =========================================================
# ROOT — CHAT UI
# =========================================================
@app.get("/")
async def root():

    return HTMLResponse(
        content=CHAT_UI_HTML,
        status_code=200,
    )


# =========================================================
# MAIN
# =========================================================
if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )