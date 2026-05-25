# app/tools/accounts_tools.py
#
# Ad account management tools — api_doc/accounts.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("accounts-tools")


# =========================================================
# LIST ACCOUNTS
# GET /workspaces/{workspace_id}/accounts
# =========================================================
async def list_accounts(
    workspace_id: int,
    platform: str | None = None,
    include_all: bool = False,
):
    params: dict = {"include_all": include_all}
    if platform:
        params["platform"] = platform
    logger.info("Listing accounts", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/workspaces/{workspace_id}/accounts", params=params
    )


# =========================================================
# TOGGLE ACCOUNT STATUS
# PATCH /workspaces/{workspace_id}/accounts/{account_id}/status
# =========================================================
async def toggle_account_status(
    workspace_id: int,
    account_id: int,
    is_active: bool,
):
    logger.info("Toggling account status", account_id=account_id, is_active=is_active)
    return await backend_client.patch(
        endpoint=f"/workspaces/{workspace_id}/accounts/{account_id}/status",
        params={"is_active": is_active},
    )


# =========================================================
# DELETE ACCOUNT
# DELETE /workspaces/{workspace_id}/accounts/{account_id}
# =========================================================
async def delete_account(workspace_id: int, account_id: int):
    logger.info("Deleting account", account_id=account_id)
    return await backend_client.delete(
        endpoint=f"/workspaces/{workspace_id}/accounts/{account_id}"
    )


# =========================================================
# LIST ACCOUNT USERS
# GET /workspaces/{workspace_id}/accounts/{account_id}/users
# =========================================================
async def list_account_users(workspace_id: int, account_id: int):
    logger.info("Listing account users", account_id=account_id)
    return await backend_client.get(
        endpoint=f"/workspaces/{workspace_id}/accounts/{account_id}/users"
    )


# =========================================================
# BACKFILL DATA
# POST /workspaces/{workspace_id}/backfill
# =========================================================
async def backfill_data(workspace_id: int, payload: dict):
    logger.info("Triggering backfill", workspace_id=workspace_id)
    return await backend_client.post(
        endpoint=f"/workspaces/{workspace_id}/backfill", data=payload
    )
