# app/api/routes/health.py

from fastapi import APIRouter

from app.config.database import (
    check_db_connection,
)

from app.config.redis import (
    redis_client,
)

from app.config.settings import (
    settings,
)


router = APIRouter()


# =========================================================
# BASIC HEALTH
# =========================================================
@router.get("/")
async def health_check():

    return {
        "success": True,
        "service": "Lemonmaxx AI",
        "status": "healthy",
    }


# =========================================================
# DETAILED HEALTH
# =========================================================
@router.get("/detailed")
async def detailed_health():

    db_status = (
        await check_db_connection()
    )

    redis_status = False

    try:

        await redis_client.ping()

        redis_status = True

    except Exception:

        redis_status = False

    overall = (
        db_status
        and redis_status
    )

    return {
        "success": overall,
        "environment": (
            settings.ENVIRONMENT
        ),
        "database": db_status,
        "redis": redis_status,
        "ai_model": settings.AI_MODEL,
    }