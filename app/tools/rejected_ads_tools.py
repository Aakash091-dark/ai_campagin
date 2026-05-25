# app/tools/rejected_ads/rejected_ads_tools.py
#
# Full rejected ads tools — api_doc/rejected_ads_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("rejected-ads-tools")


# =========================================================
# GET REJECTED ADS
# GET /api/v1/workspaces/{workspace_id}/rejected-ads
# =========================================================
async def get_rejected_ads(workspace_id: int, platform: str | None = None):
    params = {}
    if platform:
        params["platform"] = platform
    logger.info("Fetching rejected ads", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/rejected-ads",
        params=params or None,
    )


# =========================================================
# APPEAL REJECTED ADS
# POST /api/v1/workspaces/{workspace_id}/rejected-ads/appeal
# =========================================================
async def appeal_rejected_ads(workspace_id: int, items: list[dict]):
    logger.info("Appealing rejected ads", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/rejected-ads/appeal",
        data={"items": items},
    )


# =========================================================
# UPDATE REJECTED AD CREATIVE
# POST /api/v1/workspaces/{workspace_id}/rejected-ads/update
# =========================================================
async def update_rejected_ad(workspace_id: int, payload: dict):
    logger.info("Updating rejected ad", workspace_id=workspace_id)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/rejected-ads/update",
        data=payload,
    )


# =========================================================
# AUTO-SWAP LOGS
# GET /api/v1/workspaces/{workspace_id}/rejected-ads/auto-swap-logs
# =========================================================
async def get_auto_swap_logs(workspace_id: int, page: int = 1, page_size: int = 50):
    logger.info("Getting auto-swap logs", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/rejected-ads/auto-swap-logs",
        params={"page": page, "page_size": page_size},
    )


# =========================================================
# AUTO-SWAP SUMMARY
# GET /api/v1/workspaces/{workspace_id}/rejected-ads/auto-swap-summary
# =========================================================
async def get_auto_swap_summary(workspace_id: int):
    logger.info("Getting auto-swap summary", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/rejected-ads/auto-swap-summary"
    )


# =========================================================
# AUTO-DELETE LOGS
# GET /api/v1/workspaces/{workspace_id}/rejected-ads/auto-delete-logs
# =========================================================
async def get_auto_delete_logs(workspace_id: int, page: int = 1, page_size: int = 50):
    logger.info("Getting auto-delete logs", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/rejected-ads/auto-delete-logs",
        params={"page": page, "page_size": page_size},
    )


# =========================================================
# AUTO-DELETE SUMMARY
# GET /api/v1/workspaces/{workspace_id}/rejected-ads/auto-delete-summary
# =========================================================
async def get_auto_delete_summary(workspace_id: int):
    logger.info("Getting auto-delete summary", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/rejected-ads/auto-delete-summary"
    )


# =========================================================
# TOGGLE AUTO-SWAP PER ACCOUNT
# PATCH /api/v1/workspaces/{workspace_id}/accounts/{account_id}/auto-swap
# =========================================================
async def toggle_auto_swap(workspace_id: int, account_id: int, enabled: bool):
    logger.info("Toggling auto-swap", account_id=account_id, enabled=enabled)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/accounts/{account_id}/auto-swap",
        params={"enabled": enabled},
    )


# =========================================================
# TOGGLE AUTO-DELETE PER ACCOUNT
# PATCH /api/v1/workspaces/{workspace_id}/accounts/{account_id}/auto-delete
# =========================================================
async def toggle_auto_delete(workspace_id: int, account_id: int, enabled: bool):
    logger.info("Toggling auto-delete", account_id=account_id, enabled=enabled)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/accounts/{account_id}/auto-delete",
        params={"enabled": enabled},
    )
