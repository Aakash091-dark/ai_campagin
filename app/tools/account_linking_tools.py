# app/tools/account_linking_tools.py
#
# OAuth account linking tools — api_doc/acc_linking.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("account-linking-tools")


# =========================================================
# GET OAUTH AUTH URL
# GET /account-linking/{platform}/auth-url
# =========================================================
async def get_auth_url(platform: str, workspace_id: int):
    logger.info("Getting auth URL", platform=platform, workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/account-linking/{platform}/auth-url",
        params={"workspace_id": workspace_id},
    )


# =========================================================
# LIST AD ACCOUNTS FOR LINKED ACCOUNT
# GET /workspaces/{workspace_id}/accounts/{account_id}/adaccounts
# =========================================================
async def list_linked_adaccounts(workspace_id: int, account_id: int):
    logger.info("Listing linked ad accounts", workspace_id=workspace_id, account_id=account_id)
    return await backend_client.get(
        endpoint=f"/workspaces/{workspace_id}/accounts/{account_id}/adaccounts"
    )


# =========================================================
# GET RUNTIME ACCOUNTS (from session)
# POST /integration/runtime-accounts
# =========================================================
async def get_runtime_accounts(session: str):
    logger.info("Getting runtime accounts")
    return await backend_client.post(
        endpoint="/integration/runtime-accounts",
        data={"session": session},
    )


# =========================================================
# LINK PLATFORM AD ACCOUNTS
# POST /platform/adaccounts
# =========================================================
async def link_platform_adaccounts(payload: dict):
    logger.info("Linking platform ad accounts", platform=payload.get("platform"))
    return await backend_client.post(endpoint="/platform/adaccounts", data=payload)


# =========================================================
# MANUAL INTEGRATION
# POST /integration/manual
# =========================================================
async def manual_integration(items: list[dict]):
    logger.info("Manual integration", count=len(items))
    return await backend_client.post(endpoint="/integration/manual", data=items)
