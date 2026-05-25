# app/tools/analytics_tools.py
#
# Full analytics tool set — api_doc/analytics_api.txt
# and api_doc/camp_linking.txt (insights)

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("analytics-tools")


# =========================================================
# LIVE CAMPAIGN INSIGHTS
# GET /api/v1/workspaces/{workspace_id}/insights/live/campaigns
# =========================================================
async def get_live_campaign_insights(
    workspace_id: int,
    platform: str | None = None,
    partial: bool = False,
):
    params: dict = {"partial": partial}
    if platform:
        params["platform"] = platform
    logger.info("Fetching live insights", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/insights/live/campaigns",
        params=params,
    )


# =========================================================
# HISTORICAL CAMPAIGN INSIGHTS
# GET /api/v1/workspaces/{workspace_id}/insights/historical/campaigns
# =========================================================
async def get_historical_campaign_insights(
    workspace_id: int,
    platform: str,
    start_date: str,
    end_date: str,
):
    logger.info("Fetching historical insights", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/insights/historical/campaigns",
        params={"platform": platform, "start_date": start_date, "end_date": end_date},
    )


# =========================================================
# CROSS-PLATFORM HISTORICAL INSIGHTS
# GET /api/v1/workspaces/{workspace_id}/insights/cphistorical/campaigns
# =========================================================
async def get_cross_platform_historical_insights(
    workspace_id: int,
    start_date: str,
    end_date: str,
):
    logger.info("Fetching cross-platform historical insights", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/insights/cphistorical/campaigns",
        params={"start_date": start_date, "end_date": end_date},
    )


# =========================================================
# HISTORICAL BREAKDOWN
# GET /api/v1/workspaces/{workspace_id}/insights/historical/breakdown
# =========================================================
async def get_historical_breakdown(
    workspace_id: int,
    platform: str,
    start_date: str,
    end_date: str,
    granularity: str = "hour",
    campaign_id: str | None = None,
):
    params: dict = {
        "platform": platform,
        "start_date": start_date,
        "end_date": end_date,
        "granularity": granularity,
    }
    if campaign_id:
        params["campaign_id"] = campaign_id
    logger.info("Fetching historical breakdown", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/insights/historical/breakdown",
        params=params,
    )


# =========================================================
# HISTORICAL INSIGHTS BY USER
# GET /api/v1/workspaces/{workspace_id}/insights/historical/campaigns/by-user
# =========================================================
async def get_historical_insights_by_user(
    workspace_id: int,
    platform: str,
    start_date: str,
    end_date: str,
    user_id: int,
):
    logger.info("Fetching historical insights by user", workspace_id=workspace_id, user_id=user_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/insights/historical/campaigns/by-user",
        params={
            "platform": platform,
            "start_date": start_date,
            "end_date": end_date,
            "user_id": user_id,
        },
    )


# =========================================================
# TEAM MEMBERS ANALYTICS
# GET /api/v1/workspaces/{workspace_id}/analytics/team-members
# =========================================================
async def get_team_members_analytics(
    workspace_id: int,
    platform: str,
    from_date: str,
    to_date: str,
):
    logger.info("Fetching team members analytics", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/team-members",
        params={"platform": platform, "from_date": from_date, "to_date": to_date},
    )


# =========================================================
# CREATE ANALYTICS REPORT EXPORT
# POST /api/v1/workspaces/{workspace_id}/analytics/reports/exports
# =========================================================
async def create_analytics_export(
    workspace_id: int,
    platform: str,
    date_from: str,
    date_to: str,
    full: bool = False,
):
    logger.info("Creating analytics export", workspace_id=workspace_id)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/reports/exports",
        params={"platform": platform, "date_from": date_from, "date_to": date_to, "full": full},
    )


# =========================================================
# LIST ANALYTICS EXPORTS
# GET /api/v1/workspaces/{workspace_id}/analytics/reports/exports
# =========================================================
async def list_analytics_exports(workspace_id: int, date_from: str, date_to: str):
    logger.info("Listing analytics exports", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/reports/exports",
        params={"date_from": date_from, "date_to": date_to},
    )


# =========================================================
# GET EXPORT STATUS
# GET /api/v1/workspaces/{workspace_id}/analytics/reports/exports/{export_id}/status
# =========================================================
async def get_export_status(workspace_id: int, export_id: int):
    logger.info("Getting export status", export_id=export_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/reports/exports/{export_id}/status"
    )


# =========================================================
# DYNAMIC MATRIX
# GET /api/v1/workspaces/{workspace_id}/analytics/dynamic-matrix
# =========================================================
async def get_dynamic_matrix(
    workspace_id: int,
    platform: str,
    start_date: str,
    end_date: str,
    dim1: str | None = None,
    dim2: str | None = None,
    dim3: str | None = None,
):
    params: dict = {
        "platform": platform,
        "start_date": start_date,
        "end_date": end_date,
    }
    if dim1:
        params["dim1"] = dim1
    if dim2:
        params["dim2"] = dim2
    if dim3:
        params["dim3"] = dim3
    logger.info("Fetching dynamic matrix", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/dynamic-matrix",
        params=params,
    )


# =========================================================
# CREATIVES ANALYTICS
# GET /api/v1/workspaces/{workspace_id}/analytics/creatives/cards
# GET /api/v1/workspaces/{workspace_id}/analytics/creatives/graph
# =========================================================
async def get_creatives_cards(
    workspace_id: int,
    platform: str,
    start_date: str,
    end_date: str,
    view_mode: str = "workspace",
):
    logger.info("Fetching creatives cards", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/creatives/cards",
        params={
            "platform": platform,
            "start_date": start_date,
            "end_date": end_date,
            "view_mode": view_mode,
        },
    )


async def get_creatives_graph(
    workspace_id: int,
    platform: str,
    start_date: str,
    end_date: str,
    view_mode: str = "workspace",
):
    logger.info("Fetching creatives graph", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/creatives/graph",
        params={
            "platform": platform,
            "start_date": start_date,
            "end_date": end_date,
            "view_mode": view_mode,
        },
    )


# =========================================================
# HISTORICAL OFFERS
# =========================================================
async def get_historical_offers(
    workspace_id: int, platform: str, start_date: str, end_date: str
):
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/insights/historical/offers",
        params={"platform": platform, "start_date": start_date, "end_date": end_date},
    )


async def get_vertical_offers_all_platforms(
    workspace_id: int, start_date: str, end_date: str
):
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/insights/vertical-offers/all-platforms",
        params={"start_date": start_date, "end_date": end_date},
    )


# =========================================================
# CONNECTED AD ACCOUNTS
# GET /api/v1/workspaces/{workspace_id}/ad-accounts
# =========================================================
async def get_connected_ad_accounts(workspace_id: int):
    endpoint = f"/api/v1/workspaces/{workspace_id}/ad-accounts"
    logger.info("Fetching connected ad accounts", workspace_id=workspace_id)
    return await backend_client.get(endpoint=endpoint)
