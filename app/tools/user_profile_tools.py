# app/tools/user_profile_tools.py
#
# User profile tools — api_doc/user_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("user-profile-tools")


# =========================================================
# GET USER PROFILE
# GET /api/v1/user/profile
# =========================================================
async def get_user_profile():
    logger.info("Getting user profile")
    return await backend_client.get(endpoint="/api/v1/user/profile")


# =========================================================
# UPDATE USER PROFILE
# PATCH /api/v1/user/profile
# =========================================================
async def update_user_profile(payload: dict):
    logger.info("Updating user profile")
    return await backend_client.patch(endpoint="/api/v1/user/profile", data=payload)


# =========================================================
# GET CAMPAIGN TEMPLATE
# GET /api/v1/user/camp_template
# =========================================================
async def get_campaign_template():
    logger.info("Getting campaign template")
    return await backend_client.get(endpoint="/api/v1/user/camp_template")


# =========================================================
# SAVE CAMPAIGN TEMPLATE
# POST /api/v1/user/camp_template
# =========================================================
async def save_campaign_template(payload: dict):
    logger.info("Saving campaign template")
    return await backend_client.post(endpoint="/api/v1/user/camp_template", data=payload)


# =========================================================
# GET REPORTING TEMPLATE
# GET /api/v1/user/reporting_template
# =========================================================
async def get_reporting_template():
    logger.info("Getting reporting template")
    return await backend_client.get(endpoint="/api/v1/user/reporting_template")


# =========================================================
# SAVE REPORTING TEMPLATE
# POST /api/v1/user/reporting_template
# =========================================================
async def save_reporting_template(payload: dict):
    logger.info("Saving reporting template")
    return await backend_client.post(endpoint="/api/v1/user/reporting_template", data=payload)


# =========================================================
# ADD USER TAGS
# POST /api/v1/user/tags
# =========================================================
async def add_user_tags(payload: dict):
    logger.info(
        "Adding user tags",
        entity_id=payload.get("entity_id"),
        tags=payload.get("tags"),
    )
    return await backend_client.post(endpoint="/api/v1/user/tags", data=payload)
