# app/tools/permission_tools.py
#
# UI tab permission tools — api_doc/permission_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("permission-tools")


# =========================================================
# GET ALL UI TABS
# GET /api/v1/permissions/ui-tabs
# =========================================================
async def get_all_ui_tabs():
    logger.info("Getting all UI tabs")
    return await backend_client.get(endpoint="/api/v1/permissions/ui-tabs")


# =========================================================
# GET USER UI TABS
# GET /api/v1/permissions/users/{user_id}/ui-tabs
# =========================================================
async def get_user_ui_tabs(user_id: int):
    logger.info("Getting user UI tabs", user_id=user_id)
    return await backend_client.get(
        endpoint=f"/api/v1/permissions/users/{user_id}/ui-tabs"
    )


# =========================================================
# UPDATE USER UI TABS
# PUT /api/v1/permissions/users/{user_id}/ui-tabs
# =========================================================
async def update_user_ui_tabs(user_id: int, tabs: dict):
    logger.info("Updating user UI tabs", user_id=user_id)
    return await backend_client.put(
        endpoint=f"/api/v1/permissions/users/{user_id}/ui-tabs",
        data={"tabs": tabs},
    )
