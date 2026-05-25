# app/tools/tracker_tools.py
#
# Tracker tools — api_doc/trackers.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("tracker-tools")


# =========================================================
# CREATE TRACKERS
# POST /workspaces/{workspace_id}/trackers
# =========================================================
async def create_trackers(workspace_id: int, items: list[dict]):
    logger.info("Creating trackers", workspace_id=workspace_id, count=len(items))
    return await backend_client.post(
        endpoint=f"/workspaces/{workspace_id}/trackers", data=items
    )


# =========================================================
# LIST TRACKERS
# GET /workspaces/{workspace_id}/trackers
# =========================================================
async def list_trackers(
    workspace_id: int,
    platform: str | None = None,
    only_active: bool = False,
):
    params: dict = {"only_active": only_active}
    if platform:
        params["platform"] = platform
    logger.info("Listing trackers", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/workspaces/{workspace_id}/trackers", params=params
    )


# =========================================================
# UPDATE TRACKER
# PATCH /workspaces/{workspace_id}/trackers/{tracker_id}
# =========================================================
async def update_tracker(workspace_id: int, tracker_id: int, payload: dict):
    logger.info("Updating tracker", tracker_id=tracker_id)
    return await backend_client.patch(
        endpoint=f"/workspaces/{workspace_id}/trackers/{tracker_id}",
        data=payload,
    )


# =========================================================
# DELETE TRACKER
# DELETE /workspaces/{workspace_id}/trackers/{tracker_id}
# =========================================================
async def delete_tracker(workspace_id: int, tracker_id: int):
    logger.info("Deleting tracker", tracker_id=tracker_id)
    return await backend_client.delete(
        endpoint=f"/workspaces/{workspace_id}/trackers/{tracker_id}"
    )


# =========================================================
# GET REDTRACK SOURCES
# GET /workspaces/{workspace_id}/trackers/redtrack-sources
# =========================================================
async def get_redtrack_sources(
    workspace_id: int,
    tracker_id: int | None = None,
    api_key: str | None = None,
):
    params: dict = {}
    if tracker_id:
        params["tracker_id"] = tracker_id
    if api_key:
        params["api_key"] = api_key
    logger.info("Getting RedTrack sources", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/workspaces/{workspace_id}/trackers/redtrack-sources",
        params=params or None,
    )
