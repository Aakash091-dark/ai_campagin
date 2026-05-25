# app/tools/reporting/reporting_tools.py
#
# Reporting tools — api_doc/reporting_config_api.txt
# and api_doc/user_analytics_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("reporting-tools")


# =========================================================
# GENERATE WORKSPACE REPORT (dashboard summary)
# GET /api/v1/workspaces/{workspace_id}/dashboard/summary
# =========================================================
async def generate_workspace_report(workspace_id: int):
    endpoint = f"/api/v1/workspaces/{workspace_id}/dashboard/summary"
    logger.info("Generating workspace report", workspace_id=workspace_id)
    return await backend_client.get(endpoint=endpoint)


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
# SET REPORTING CONFIG
# POST /api/v1/workspaces/{workspace_id}/reporting/config
# =========================================================
async def set_reporting_config(workspace_id: int, payload: dict):
    logger.info("Setting reporting config", workspace_id=workspace_id)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/reporting/config",
        data=payload,
    )


# =========================================================
# GET REPORTING SLOTS
# GET /api/v1/workspaces/{workspace_id}/reporting/slots
# =========================================================
async def get_reporting_slots(workspace_id: int):
    logger.info("Getting reporting slots", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/reporting/slots"
    )


# =========================================================
# SUBMIT REPORT
# POST /api/v1/workspaces/{workspace_id}/reporting/submit
# =========================================================
async def submit_report(workspace_id: int, payload: dict):
    logger.info(
        "Submitting report",
        workspace_id=workspace_id,
        slot_id=payload.get("slot_id"),
    )
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/reporting/submit",
        data=payload,
    )


# =========================================================
# SUBMIT ZERO REPORT
# POST /api/v1/workspaces/{workspace_id}/reporting/zero-report
# =========================================================
async def submit_zero_report(workspace_id: int):
    logger.info("Submitting zero report", workspace_id=workspace_id)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/reporting/zero-report"
    )
