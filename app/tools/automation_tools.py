# app/tools/automations/automation_tools.py
#
# Full automation tools — api_doc/automation.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("automation-tools")


# =========================================================
# CREATE AUTOMATION RULE
# POST /api/v1/workspaces/{workspace_id}/automations/
# =========================================================
async def create_automation_rule(workspace_id: int, payload: dict):
    logger.info(
        "Creating automation rule",
        workspace_id=workspace_id,
        name=payload.get("name"),
    )
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/automations/",
        data=payload,
    )


# =========================================================
# LIST AUTOMATION RULES
# GET /api/v1/workspaces/{workspace_id}/automations/
# =========================================================
async def list_automation_rules(
    workspace_id: int,
    platform: str | None = None,
    is_active: bool | None = None,
    page: int = 1,
    limit: int = 20,
):
    params: dict = {"page": page, "limit": limit}
    if platform:
        params["platform"] = platform
    if is_active is not None:
        params["is_active"] = is_active
    logger.info("Listing automation rules", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/automations/",
        params=params,
    )


# =========================================================
# GET AUTOMATION RULE
# GET /api/v1/workspaces/{workspace_id}/automations/{rule_id}
# =========================================================
async def get_automation_rule(workspace_id: int, rule_id: int):
    logger.info("Getting automation rule", rule_id=rule_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/automations/{rule_id}"
    )


# =========================================================
# UPDATE AUTOMATION RULE
# PATCH /api/v1/workspaces/{workspace_id}/automations/{rule_id}
# =========================================================
async def update_automation_rule(workspace_id: int, rule_id: int, payload: dict):
    logger.info("Updating automation rule", rule_id=rule_id)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/automations/{rule_id}",
        data=payload,
    )


# =========================================================
# DELETE AUTOMATION RULE
# DELETE /api/v1/workspaces/{workspace_id}/automations/{rule_id}
# =========================================================
async def delete_automation_rule(workspace_id: int, rule_id: int):
    logger.info("Deleting automation rule", rule_id=rule_id)
    return await backend_client.delete(
        endpoint=f"/api/v1/workspaces/{workspace_id}/automations/{rule_id}"
    )


# =========================================================
# TOGGLE AUTOMATION RULE
# PATCH /api/v1/workspaces/{workspace_id}/automations/{rule_id}/toggle
# =========================================================
async def toggle_automation_rule(workspace_id: int, rule_id: int):
    logger.info("Toggling automation rule", rule_id=rule_id)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/automations/{rule_id}/toggle"
    )


# =========================================================
# GET AUTOMATION RULE LOGS
# GET /api/v1/workspaces/{workspace_id}/automations/{rule_id}/logs
# =========================================================
async def get_automation_rule_logs(
    workspace_id: int, rule_id: int, page: int = 1, limit: int = 10
):
    logger.info("Getting automation rule logs", rule_id=rule_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/automations/{rule_id}/logs",
        params={"page": page, "limit": limit},
    )


# =========================================================
# LIST ALL AUTOMATION LOGS
# GET /api/v1/workspaces/{workspace_id}/automations/logs/all
# =========================================================
async def list_all_automation_logs(
    workspace_id: int,
    platform: str | None = None,
    action_success: bool | None = None,
    page: int = 1,
    limit: int = 50,
):
    params: dict = {"page": page, "limit": limit}
    if platform:
        params["platform"] = platform
    if action_success is not None:
        params["action_success"] = action_success
    logger.info("Listing all automation logs", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/automations/logs/all",
        params=params,
    )
