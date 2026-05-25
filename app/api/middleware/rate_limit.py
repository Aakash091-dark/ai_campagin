# app/api/middleware/rate_limit.py

from fastapi import Request
from fastapi import HTTPException

from starlette.middleware.base import (
    BaseHTTPMiddleware,
)

from app.config.settings import (
    settings,
)

from app.config.redis import (
    get_user_active_requests,
    increment_user_requests,
)

from app.config.logging import (
    get_logger,
)


logger = get_logger("rate-limit")


# =========================================================
# RATE LIMIT MIDDLEWARE
# =========================================================
class RateLimitMiddleware(
    BaseHTTPMiddleware
):

    async def dispatch(
        self,
        request: Request,
        call_next,
    ):

        # =============================================
        # GET USER ID
        # =============================================
        user_id = request.headers.get(
            "X-User-ID"
        )

        # =============================================
        # SKIP IF NO USER
        # =============================================
        if not user_id:

            return await call_next(request)

        user_id = int(user_id)

        # =============================================
        # ACTIVE REQUESTS
        # =============================================
        active_requests = (
            await get_user_active_requests(
                user_id
            )
        )

        # =============================================
        # LIMIT CHECK
        # =============================================
        if (
            active_requests
            >= settings.MAX_PER_USER_CONCURRENT
        ):

            logger.warning(
                "User concurrency exceeded",
                user_id=user_id,
            )

            raise HTTPException(
                status_code=429,
                detail=(
                    "Too many active AI requests"
                ),
            )

        # =============================================
        # INCREMENT
        # =============================================
        await increment_user_requests(
            user_id
        )

        try:

            response = await call_next(
                request
            )

            return response

        finally:

            from app.config.redis import (
                decrement_user_requests,
            )

            await decrement_user_requests(
                user_id
            )