# app/tools/account_assignment_tools.py
#
# Account assignment tools — api_doc/acc_assign_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("account-assignment-tools")


# =========================================================
# ASSIGN ACCOUNTS TO USER
# POST /api/v1/account-assignment/assign
# =========================================================
async def assign_accounts(workspace_id: int, account_ids: list[int], user_id: int):
    logger.info("Assigning accounts", user_id=user_id, count=len(account_ids))
    return await backend_client.post(
        endpoint="/api/v1/account-assignment/assign",
        data={"workspace_id": workspace_id, "account_ids": account_ids, "user_id": user_id},
    )


# =========================================================
# UNASSIGN ACCOUNTS FROM USER
# POST /api/v1/account-assignment/unassign
# =========================================================
async def unassign_accounts(workspace_id: int, account_ids: list[int], user_id: int):
    logger.info("Unassigning accounts", user_id=user_id, count=len(account_ids))
    return await backend_client.post(
        endpoint="/api/v1/account-assignment/unassign",
        data={"workspace_id": workspace_id, "account_ids": account_ids, "user_id": user_id},
    )


# =========================================================
# SELF-ASSIGN ACCOUNTS
# POST /api/v1/account-assignment/self/assign
# =========================================================
async def self_assign_accounts(account_ids: list[int]):
    logger.info("Self-assigning accounts", count=len(account_ids))
    return await backend_client.post(
        endpoint="/api/v1/account-assignment/self/assign",
        data={"account_ids": account_ids},
    )


# =========================================================
# BULK ASSIGN / UNASSIGN
# POST /api/v1/account-assignment/assign-un-assign
# =========================================================
async def bulk_assign_unassign(
    workspace_id: int,
    user_id: int,
    assign: list[int],
    un_assign: list[int],
):
    logger.info("Bulk assign/unassign", user_id=user_id)
    return await backend_client.post(
        endpoint="/api/v1/account-assignment/assign-un-assign",
        data={
            "workspace_id": workspace_id,
            "user_id": user_id,
            "assign": assign,
            "un_assign": un_assign,
        },
    )


# =========================================================
# GET USER ASSIGNED ACCOUNTS
# GET /api/v1/account-assignment/workspaces/{workspace_id}/users/{user_id}/accounts
# =========================================================
async def get_user_assigned_accounts(
    workspace_id: int,
    user_id: int,
    platform: str | None = None,
):
    params = {}
    if platform:
        params["platform"] = platform
    logger.info("Getting user assigned accounts", user_id=user_id)
    return await backend_client.get(
        endpoint=f"/api/v1/account-assignment/workspaces/{workspace_id}/users/{user_id}/accounts",
        params=params or None,
    )
