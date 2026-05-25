# app/tools/timezone_tools.py
#
# Timezone tools — api_doc/timezone_api.txt + api_doc/misc_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("timezone-tools")


# =========================================================
# GET WORKSPACE TIMEZONE
# GET /api/v1/workspaces/{workspace_id}/timezone
# =========================================================
async def get_workspace_timezone(workspace_id: int):
    logger.info("Getting workspace timezone", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/timezone"
    )


# =========================================================
# SET WORKSPACE TIMEZONE
# POST /api/v1/workspaces/{workspace_id}/timezone
# =========================================================
async def set_workspace_timezone(workspace_id: int, timezone: str):
    logger.info("Setting workspace timezone", workspace_id=workspace_id, timezone=timezone)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/timezone",
        data={"timezone": timezone},
    )


# =========================================================
# LIST ALL TIMEZONES
# GET /api/v1/misc/timezones
# =========================================================
async def list_timezones(q: str | None = None):
    params = {}
    if q:
        params["q"] = q
    logger.info("Listing timezones", q=q)
    return await backend_client.get(
        endpoint="/api/v1/misc/timezones",
        params=params or None,
    )
