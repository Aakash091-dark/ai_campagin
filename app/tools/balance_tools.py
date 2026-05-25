# app/tools/balance_tools.py
#
# Balance tools — api_doc/balance_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("balance-tools")


# =========================================================
# GET FACEBOOK BALANCES
# GET /api/v1/workspaces/{workspace_id}/balances/facebook
# =========================================================
async def get_facebook_balances(workspace_id: int):
    logger.info("Getting Facebook balances", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/balances/facebook"
    )


# =========================================================
# GET GOOGLE BALANCES
# GET /api/v1/workspaces/{workspace_id}/balances/google
# =========================================================
async def get_google_balances(workspace_id: int):
    logger.info("Getting Google balances", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/balances/google"
    )
