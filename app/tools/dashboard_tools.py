# app/tools/dashboard_tools.py
#
# Full dashboard tool set covering all endpoints in
# api_doc/dashboard.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("dashboard-tools")


# =========================================================
# DASHBOARD SUMMARY
# GET /api/v1/workspaces/{workspace_id}/dashboard/summary
# =========================================================
async def get_dashboard_summary(
    workspace_id: int,
    from_date: str | None = None,
    to_date: str | None = None,
):
    endpoint = f"/api/v1/workspaces/{workspace_id}/dashboard/summary"
    params = {}
    if from_date:
        params["from_date"] = from_date
    if to_date:
        params["to_date"] = to_date

    logger.info("Fetching dashboard summary", workspace_id=workspace_id)
    return await backend_client.get(endpoint=endpoint, params=params or None)


# =========================================================
# DASHBOARD TIMESERIES
# GET /api/v1/workspaces/{workspace_id}/dashboard/timeseries
# =========================================================
async def get_dashboard_timeseries(
    workspace_id: int,
    granularity: str,
    from_date: str,
    to_date: str,
):
    endpoint = f"/api/v1/workspaces/{workspace_id}/dashboard/timeseries"
    params = {
        "granularity": granularity,
        "from_date": from_date,
        "to_date": to_date,
    }
    logger.info("Fetching dashboard timeseries", workspace_id=workspace_id, granularity=granularity)
    return await backend_client.get(endpoint=endpoint, params=params)


# =========================================================
# DASHBOARD USER TRENDS
# GET /api/v1/workspaces/{workspace_id}/dashboard/user-trends
# =========================================================
async def get_dashboard_user_trends(
    workspace_id: int,
    user_id: int,
    granularity: str,
    from_date: str,
    to_date: str,
):
    endpoint = f"/api/v1/workspaces/{workspace_id}/dashboard/user-trends"
    params = {
        "user_id": user_id,
        "granularity": granularity,
        "from_date": from_date,
        "to_date": to_date,
    }
    logger.info("Fetching user trends", workspace_id=workspace_id, user_id=user_id)
    return await backend_client.get(endpoint=endpoint, params=params)


# =========================================================
# DASHBOARD ACCOUNTS ADS
# GET /api/v1/workspaces/{workspace_id}/dashboard/accounts-ads
# =========================================================
async def get_dashboard_accounts_ads(
    workspace_id: int,
    from_date: str,
    to_date: str,
):
    endpoint = f"/api/v1/workspaces/{workspace_id}/dashboard/accounts-ads"
    params = {"from_date": from_date, "to_date": to_date}
    logger.info("Fetching accounts-ads", workspace_id=workspace_id)
    return await backend_client.get(endpoint=endpoint, params=params)


# =========================================================
# DASHBOARD TL USERS
# GET /api/v1/workspaces/{workspace_id}/dashboard/tl-users
# =========================================================
async def get_dashboard_tl_users(
    workspace_id: int,
    from_date: str,
    to_date: str,
):
    endpoint = f"/api/v1/workspaces/{workspace_id}/dashboard/tl-users"
    params = {"from_date": from_date, "to_date": to_date}
    logger.info("Fetching TL users", workspace_id=workspace_id)
    return await backend_client.get(endpoint=endpoint, params=params)


# =========================================================
# DASHBOARD ACCOUNT DRILLDOWN
# GET /api/v1/workspaces/{workspace_id}/dashboard/account-data
# =========================================================
async def get_dashboard_account_drilldown(
    workspace_id: int,
    platform: str,
    account_id: str,
    start_date: str,
    end_date: str,
):
    endpoint = f"/api/v1/workspaces/{workspace_id}/dashboard/account-data"
    params = {
        "platform": platform,
        "account_id": account_id,
        "start_date": start_date,
        "end_date": end_date,
    }
    logger.info("Fetching account drilldown", workspace_id=workspace_id, account_id=account_id)
    return await backend_client.get(endpoint=endpoint, params=params)
