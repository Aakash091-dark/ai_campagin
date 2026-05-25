# app/api/dependencies/user.py

from fastapi import Request
from fastapi import HTTPException


# =========================================================
# CURRENT USER
# =========================================================
async def get_current_user(
    request: Request
):

    user = getattr(
        request.state,
        "user",
        None,
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
        )

    return user