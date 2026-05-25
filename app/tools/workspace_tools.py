# app/tools/workspace_tools.py
#
# Workspace management tools — api_doc/workspace_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("workspace-tools")


# =========================================================
# CREATE WORKSPACE
# POST /api/v1/workspace
# =========================================================
async def create_workspace(payload: dict):
    logger.info("Creating workspace", name=payload.get("name"))
    return await backend_client.post(endpoint="/api/v1/workspace", data=payload)


# =========================================================
# UPDATE WORKSPACE
# PATCH /api/v1/workspace/{workspace_id}
# =========================================================
async def update_workspace(workspace_id: int, payload: dict):
    logger.info("Updating workspace", workspace_id=workspace_id)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspace/{workspace_id}", data=payload
    )


# =========================================================
# TOGGLE WORKSPACE STATUS
# PATCH /api/v1/workspace/{workspace_id}/status
# =========================================================
async def toggle_workspace_status(workspace_id: int, is_active: bool):
    logger.info("Toggling workspace status", workspace_id=workspace_id, is_active=is_active)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspace/{workspace_id}/status",
        data={"is_active": is_active},
    )


# =========================================================
# LIST WORKSPACES
# GET /api/v1/workspace/workspace-list
# =========================================================
async def list_workspaces():
    logger.info("Listing workspaces")
    return await backend_client.get(endpoint="/api/v1/workspace/workspace-list")


# =========================================================
# DELETE WORKSPACES
# DELETE /api/v1/workspace/delete
# =========================================================
async def delete_workspaces(workspace_ids: list[int]):
    logger.info("Deleting workspaces", workspace_ids=workspace_ids)
    return await backend_client.delete(
        endpoint="/api/v1/workspace/delete",
        data={"workspace_ids": workspace_ids},
    )
