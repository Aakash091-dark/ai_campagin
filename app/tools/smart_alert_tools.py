# app/tools/smart_alert_tools.py
#
# Smart alert tools — api_doc/smart_alert_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("smart-alert-tools")


# =========================================================
# CREATE SMART ALERT
# POST /api/v1/workspaces/{workspace_id}/smart-alerts/
# =========================================================
async def create_smart_alert(workspace_id: int, payload: dict):
    logger.info("Creating smart alert", workspace_id=workspace_id, name=payload.get("alert_name"))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/smart-alerts/",
        data=payload,
    )


# =========================================================
# LIST SMART ALERTS
# GET /api/v1/workspaces/{workspace_id}/smart-alerts/
# =========================================================
async def list_smart_alerts(
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
    logger.info("Listing smart alerts", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/smart-alerts/",
        params=params,
    )


# =========================================================
# GET SMART ALERT
# GET /api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}
# =========================================================
async def get_smart_alert(workspace_id: int, alert_id: int):
    logger.info("Getting smart alert", alert_id=alert_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}"
    )


# =========================================================
# UPDATE SMART ALERT
# PATCH /api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}
# =========================================================
async def update_smart_alert(workspace_id: int, alert_id: int, payload: dict):
    logger.info("Updating smart alert", alert_id=alert_id)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}",
        data=payload,
    )


# =========================================================
# DELETE SMART ALERT
# DELETE /api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}
# =========================================================
async def delete_smart_alert(workspace_id: int, alert_id: int):
    logger.info("Deleting smart alert", alert_id=alert_id)
    return await backend_client.delete(
        endpoint=f"/api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}"
    )


# =========================================================
# TOGGLE SMART ALERT
# POST /api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}/toggle
# =========================================================
async def toggle_smart_alert(workspace_id: int, alert_id: int):
    logger.info("Toggling smart alert", alert_id=alert_id)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}/toggle"
    )


# =========================================================
# GET ALERT LOGS
# GET /api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}/logs
# =========================================================
async def get_smart_alert_logs(
    workspace_id: int, alert_id: int, page: int = 1, limit: int = 10
):
    logger.info("Getting smart alert logs", alert_id=alert_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/smart-alerts/{alert_id}/logs",
        params={"page": page, "limit": limit},
    )


# =========================================================
# LIST ALL ALERT LOGS
# GET /api/v1/workspaces/{workspace_id}/smart-alerts-logs/
# =========================================================
async def list_all_smart_alert_logs(
    workspace_id: int,
    platform: str | None = None,
    has_matches: bool | None = None,
    page: int = 1,
    limit: int = 50,
):
    params: dict = {"page": page, "limit": limit}
    if platform:
        params["platform"] = platform
    if has_matches is not None:
        params["has_matches"] = has_matches
    logger.info("Listing all smart alert logs", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/smart-alerts-logs/",
        params=params,
    )
