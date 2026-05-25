# app/tools/user_analytics_tools.py
#
# User analytics tools — api_doc/user_analytics_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("user-analytics-tools")


# =========================================================
# GET ANALYTICS REPORTING
# GET /api/v1/workspaces/{workspace_id}/analytics/reporting
# =========================================================
async def get_analytics_reporting(
    workspace_id: int,
    start_date: str,
    end_date: str,
):
    logger.info("Getting analytics reporting", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/reporting",
        params={"start_date": start_date, "end_date": end_date},
    )


# =========================================================
# GET ANALYTICS GOALS
# GET /api/v1/workspaces/{workspace_id}/analytics/goals
# =========================================================
async def get_analytics_goals(
    workspace_id: int,
    start_month: str,
    end_month: str,
):
    logger.info("Getting analytics goals", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/goals",
        params={"start_month": start_month, "end_month": end_month},
    )


# =========================================================
# GET ANALYTICS TASKS
# GET /api/v1/workspaces/{workspace_id}/analytics/tasks
# =========================================================
async def get_analytics_tasks(workspace_id: int):
    logger.info("Getting analytics tasks", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/tasks"
    )


# =========================================================
# SEND MEMBER REPORT
# POST /api/v1/workspaces/{workspace_id}/analytics/member-report/send
# =========================================================
async def send_member_report(
    workspace_id: int,
    target_user_id: int,
    start_month: str,
    end_month: str,
):
    logger.info("Sending member report", workspace_id=workspace_id, target_user_id=target_user_id)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/analytics/member-report/send",
        params={
            "target_user_id": target_user_id,
            "start_month": start_month,
            "end_month": end_month,
        },
    )
