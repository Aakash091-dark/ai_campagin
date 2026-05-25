# app/tools/campaign_status_tools.py
#
# Bulk campaign/adset/ad status, budget, bid, delete tools
# api_doc/campagin_status_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("campaign-status-tools")


# =========================================================
# PAUSE CAMPAIGNS (convenience wrapper)
# =========================================================
async def pause_campaigns(workspace_id: int, items: list[dict]):
    """Force status=PAUSED on a list of campaigns."""
    payload = [{**i, "status": "PAUSED"} for i in items]
    logger.info("Pausing campaigns", workspace_id=workspace_id, count=len(payload))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/campaign-status/change/bulk",
        data=payload,
    )


# =========================================================
# RESUME CAMPAIGNS (convenience wrapper)
# =========================================================
async def resume_campaigns(workspace_id: int, items: list[dict]):
    """Force status=ACTIVE on a list of campaigns."""
    payload = [{**i, "status": "ACTIVE"} for i in items]
    logger.info("Resuming campaigns", workspace_id=workspace_id, count=len(payload))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/campaign-status/change/bulk",
        data=payload,
    )


# =========================================================
# BULK CAMPAIGN STATUS CHANGE
# POST /api/v1/workspaces/{workspace_id}/campaign-status/change/bulk
# =========================================================
async def bulk_change_campaign_status(workspace_id: int, items: list[dict]):
    logger.info("Bulk campaign status change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/campaign-status/change/bulk",
        data=items,
    )


# =========================================================
# BULK CAMPAIGN BUDGET CHANGE
# POST /api/v1/workspaces/{workspace_id}/campaign-budget/change/bulk
# =========================================================
async def bulk_change_campaign_budget(workspace_id: int, items: list[dict]):
    logger.info("Bulk campaign budget change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/campaign-budget/change/bulk",
        data=items,
    )


# =========================================================
# BULK ADSET BUDGET CHANGE
# POST /api/v1/workspaces/{workspace_id}/adset-budget/change/bulk
# =========================================================
async def bulk_change_adset_budget(workspace_id: int, items: list[dict]):
    logger.info("Bulk adset budget change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/adset-budget/change/bulk",
        data=items,
    )


# =========================================================
# BULK ADSET BID CHANGE (Facebook)
# POST /api/v1/workspaces/{workspace_id}/adset-bid/change/bulk
# =========================================================
async def bulk_change_adset_bid(workspace_id: int, items: list[dict]):
    logger.info("Bulk adset bid change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/adset-bid/change/bulk",
        data=items,
    )


# =========================================================
# BULK ADSET BID CHANGE (Google)
# POST /api/v1/workspaces/{workspace_id}/google/adset-bid/change/bulk
# =========================================================
async def bulk_change_google_adset_bid(workspace_id: int, items: list[dict]):
    logger.info("Bulk Google adset bid change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/google/adset-bid/change/bulk",
        data=items,
    )


# =========================================================
# BULK ADSET STATUS CHANGE
# POST /api/v1/workspaces/{workspace_id}/adset-status/change/bulk
# =========================================================
async def bulk_change_adset_status(workspace_id: int, items: list[dict]):
    logger.info("Bulk adset status change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/adset-status/change/bulk",
        data=items,
    )


# =========================================================
# BULK AD STATUS CHANGE
# POST /api/v1/workspaces/{workspace_id}/ad-status/change/bulk
# =========================================================
async def bulk_change_ad_status(workspace_id: int, items: list[dict]):
    logger.info("Bulk ad status change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/ad-status/change/bulk",
        data=items,
    )


# =========================================================
# BULK DELETE ADS
# POST /api/v1/workspaces/{workspace_id}/ad/delete/bulk
# =========================================================
async def bulk_delete_ads(workspace_id: int, items: list[dict]):
    logger.info("Bulk delete ads", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/ad/delete/bulk",
        data=items,
    )


# =========================================================
# BULK DELETE CAMPAIGNS
# POST /api/v1/workspaces/{workspace_id}/campaign/delete/bulk
# =========================================================
async def bulk_delete_campaigns(workspace_id: int, items: list[dict]):
    logger.info("Bulk delete campaigns", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/campaign/delete/bulk",
        data=items,
    )


# =========================================================
# BULK DELETE ADSETS
# POST /api/v1/workspaces/{workspace_id}/adset/delete/bulk
# =========================================================
async def bulk_delete_adsets(workspace_id: int, items: list[dict]):
    logger.info("Bulk delete adsets", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/adset/delete/bulk",
        data=items,
    )


# =========================================================
# BULK AD MATERIAL STATUS CHANGE
# POST /api/v1/workspaces/{workspace_id}/ad-material-status/change/bulk
# =========================================================
async def bulk_change_ad_material_status(workspace_id: int, items: list[dict]):
    logger.info("Bulk ad material status change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/ad-material-status/change/bulk",
        data=items,
    )


# =========================================================
# BULK GOOGLE ENHANCED CPC CHANGE
# POST /api/v1/workspaces/{workspace_id}/google/campaign-bid/enhanced-cpc/change/bulk
# =========================================================
async def bulk_change_google_enhanced_cpc(workspace_id: int, items: list[dict]):
    logger.info("Bulk Google enhanced CPC change", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/google/campaign-bid/enhanced-cpc/change/bulk",
        data=items,
    )
