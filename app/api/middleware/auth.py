# app/api/middleware/auth.py
#
# JWT auth middleware.
#
# In development (ENVIRONMENT=development) a DEV_TOKEN bypass is active.
# Set DEV_TOKEN in .env as AUTH_TOKEN, or use the hardcoded fallback below.
# Remove / disable the dev token before deploying to production.
#
# Token payload expected:
#   { "sub": "<user_id>", "email": "<email>", "role": "<role>", "exp": <unix> }

import json

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt as jose_jwt, JWTError

from app.config.settings import settings
from app.config.logging import get_logger
from app.core.context import request_token_var

logger = get_logger("auth-middleware")

# ── paths that skip auth entirely ─────────────────────────────────
_PUBLIC_PATHS = {"/", "/health", "/health/"}
_PUBLIC_PREFIXES = ("/health/", "/api/v1/test", "/api/v1/ai")

# ── dev token ─────────────────────────────────────────────────────
# Two accepted dev tokens in development mode:
#   1. AUTH_TOKEN from .env  (the real JWT used by the backend)
#   2. "lemonmaxx-dev-token" (legacy hardcoded string for the chat UI)
# Only active when ENVIRONMENT=development.
_DEV_TOKENS: set[str] = {
    t for t in [settings.AUTH_TOKEN, "lemonmaxx-dev-token"] if t
}

# Hardcoded fallback dev user — matches the JWT sub in AUTH_TOKEN
_DEV_USER = {
    "user_id": 103,
    "email": "aakash.cognitivepixel@gmail.com",
    "role": "admin",
}


def _json_401(detail: str) -> JSONResponse:
    """Return a proper JSON 401 so the frontend never sees plain-text errors."""
    return JSONResponse(
        status_code=401,
        content={"detail": detail},
    )


class AuthMiddleware(BaseHTTPMiddleware):

    async def dispatch(self, request: Request, call_next):

        path = request.url.path

        # ── extract Authorization header for backend API calls ─────
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            request_token_var.set(token)
            
        # ── try to decode & validate JWT (optional for public routes) ──
        user_assigned = False
        if token:
            if settings.ENVIRONMENT == "development" and token in _DEV_TOKENS:
                request.state.user = _DEV_USER
                user_assigned = True
            else:
                try:
                    # In some setups, you may want to skip signature verification if you just want to extract the sub
                    # But for security on non-public routes, we keep it fully validated.
                    payload = jose_jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=[settings.JWT_ALGORITHM],
                    )
                    user_id = payload.get("sub")
                    if user_id:
                        request.state.user = {
                            "user_id": int(user_id),
                            "email": payload.get("email", ""),
                            "role": payload.get("role", "user"),
                        }
                        user_assigned = True
                except JWTError:
                    pass

        # ── skip public routes ─────────────────────────────────────
        is_public = path in _PUBLIC_PATHS or any(path.startswith(p) for p in _PUBLIC_PREFIXES)
        
        if is_public:
            if not user_assigned:
                request.state.user = _DEV_USER
            return await call_next(request)

        # ── require Authorization header for non-public routes ─────
        if not user_assigned:
            if not token:
                return _json_401("Authorization header missing or malformed")
            return _json_401("Invalid or expired token")

        return await call_next(request)
