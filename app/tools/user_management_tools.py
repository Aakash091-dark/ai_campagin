# app/tools/user_management_tools.py
#
# User management tools — api_doc/user_manag_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("user-management-tools")

_BASE = "/api/v1/user-management"


# =========================================================
# CREATE USERS BY ROLE
# =========================================================

async def create_admin(payload: dict):
    logger.info("Creating admin", email=payload.get("email"))
    return await backend_client.post(
        endpoint=f"{_BASE}/workspaces/admins", data=payload
    )


async def create_team_lead(payload: dict):
    logger.info("Creating team lead", email=payload.get("email"))
    return await backend_client.post(
        endpoint=f"{_BASE}/workspaces/tls", data=payload
    )


async def create_ct_team_lead(payload: dict):
    logger.info("Creating CT team lead", email=payload.get("email"))
    return await backend_client.post(
        endpoint=f"{_BASE}/workspaces/ct_tl", data=payload
    )


async def create_ct_user(payload: dict):
    logger.info("Creating CT user", email=payload.get("email"))
    return await backend_client.post(
        endpoint=f"{_BASE}/workspaces/ct_user", data=payload
    )


async def create_ctesting_team_lead(payload: dict):
    logger.info("Creating CTesting team lead", email=payload.get("email"))
    return await backend_client.post(
        endpoint=f"{_BASE}/workspaces/ctesting_tl", data=payload
    )


async def create_ctesting_user(payload: dict):
    logger.info("Creating CTesting user", email=payload.get("email"))
    return await backend_client.post(
        endpoint=f"{_BASE}/workspaces/ctesting_users", data=payload
    )


async def create_user(payload: dict):
    logger.info("Creating user", email=payload.get("email"))
    return await backend_client.post(
        endpoint=f"{_BASE}/workspaces/users", data=payload
    )


# =========================================================
# ASSIGN TEAM LEAD TO USER
# POST /api/v1/user-management/workspaces/users/assign-tl
# =========================================================
async def assign_team_lead(workspace_id: int, user_id: int, tl_id: int):
    logger.info("Assigning TL", user_id=user_id, tl_id=tl_id)
    return await backend_client.post(
        endpoint=f"{_BASE}/workspaces/users/assign-tl",
        data={"workspace_id": workspace_id, "user_id": user_id, "tl_id": tl_id},
    )


# =========================================================
# LIST WORKSPACE USERS
# GET /api/v1/user-management/workspaces/{workspace_id}/users
# =========================================================
async def list_workspace_users(
    workspace_id: int,
    only_active: bool = True,
    role: str | None = None,
    full_data: bool = False,
):
    params: dict = {"only_active": only_active, "full_data": full_data}
    if role:
        params["role"] = role
    logger.info("Listing workspace users", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"{_BASE}/workspaces/{workspace_id}/users",
        params=params,
    )


# =========================================================
# LIST TL'S USERS
# GET /api/v1/user-management/workspaces/{workspace_id}/tls/{tl_id}/users
# =========================================================
async def list_tl_users(workspace_id: int, tl_id: int):
    logger.info("Listing TL users", tl_id=tl_id)
    return await backend_client.get(
        endpoint=f"{_BASE}/workspaces/{workspace_id}/tls/{tl_id}/users"
    )


# =========================================================
# GET USER
# GET /api/v1/user-management/users/{user_id}
# =========================================================
async def get_user(user_id: int):
    logger.info("Getting user", user_id=user_id)
    return await backend_client.get(endpoint=f"{_BASE}/users/{user_id}")


# =========================================================
# DELETE USER
# DELETE /api/v1/user-management/users/{user_id}
# =========================================================
async def delete_user(user_id: int):
    logger.info("Deleting user", user_id=user_id)
    return await backend_client.delete(endpoint=f"{_BASE}/users/{user_id}")
