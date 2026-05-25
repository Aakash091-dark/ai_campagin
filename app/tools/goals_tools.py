# app/tools/goals_tools.py
#
# Goals tools — api_doc/goals_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("goals-tools")


# =========================================================
# CREATE GOAL
# POST /api/v1/workspaces/{workspace_id}/goals
# =========================================================
async def create_goal(workspace_id: int, payload: dict):
    logger.info(
        "Creating goal",
        workspace_id=workspace_id,
        user_id=payload.get("user_id"),
        period=payload.get("target_period"),
    )
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/goals",
        data=payload,
    )


# =========================================================
# UPDATE GOAL
# PATCH /api/v1/workspaces/{workspace_id}/goals/{goal_id}
# =========================================================
async def update_goal(workspace_id: int, goal_id: int, target_profit: float):
    logger.info("Updating goal", goal_id=goal_id, target_profit=target_profit)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/goals/{goal_id}",
        data={"target_profit": target_profit},
    )
