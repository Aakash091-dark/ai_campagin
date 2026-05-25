# app/tools/campaign_launcher_tools.py
#
# Campaign launcher tools — api_doc/campagin_launch_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("campaign-launcher-tools")

_BASE = "/api/v1/workspaces/{wid}/camp-launcher"


def _b(workspace_id: int) -> str:
    return _BASE.format(wid=workspace_id)


# =========================================================
# LOOKUP HELPERS
# =========================================================

async def get_launcher_accounts(workspace_id: int, account_id: str):
    logger.info("Fetching launcher accounts", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/accounts",
        params={"account_id": account_id},
    )


async def get_launcher_pixels(workspace_id: int, account_id: str):
    logger.info("Fetching pixels", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/pixels",
        params={"account_id": account_id},
    )


async def get_launcher_pages(workspace_id: int, account_id: str):
    logger.info("Fetching pages", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/pages",
        params={"account_id": account_id},
    )


async def get_ads_volume(workspace_id: int):
    logger.info("Fetching ads volume", workspace_id=workspace_id)
    return await backend_client.get(endpoint=f"{_b(workspace_id)}/ads-volume")


async def get_instagram_accounts(workspace_id: int, page_id: str, account_id: str):
    logger.info("Fetching Instagram accounts", page_id=page_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/pages/{page_id}/instagram-accounts",
        params={"account_id": account_id},
    )


async def get_audiences(workspace_id: int, account_id: str):
    logger.info("Fetching audiences", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/audiences",
        params={"account_id": account_id},
    )


# =========================================================
# TARGETING SEARCH
# =========================================================

async def search_targeting_countries(workspace_id: int, account_id: str, q: str):
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/targeting/countries",
        params={"account_id": account_id, "q": q},
    )


async def search_targeting_cities(
    workspace_id: int, account_id: str, q: str, country_code: str
):
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/targeting/cities",
        params={"account_id": account_id, "q": q, "country_code": country_code},
    )


async def search_targeting_languages(workspace_id: int, account_id: str, q: str):
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/targeting/languages",
        params={"account_id": account_id, "q": q},
    )


async def search_targeting_detailed(
    workspace_id: int, account_id: str, q: str, limit: int = 10
):
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/targeting/detailed",
        params={"account_id": account_id, "q": q, "limit": limit},
    )


# =========================================================
# MEDIA
# =========================================================

async def get_media_images(workspace_id: int, account_id: str):
    logger.info("Fetching media images", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/media/images",
        params={"account_id": account_id},
    )


async def get_media_videos(workspace_id: int, account_id: str):
    logger.info("Fetching media videos", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/media/videos",
        params={"account_id": account_id},
    )


# =========================================================
# CREATE CAMPAIGN / ADSET / AD
# =========================================================

async def create_campaign(workspace_id: int, payload: dict):
    logger.info("Creating campaign", workspace_id=workspace_id, name=payload.get("name"))
    return await backend_client.post(
        endpoint=f"{_b(workspace_id)}/campaign", data=payload
    )


async def create_adset(workspace_id: int, payload: dict):
    logger.info("Creating adset", workspace_id=workspace_id, name=payload.get("name"))
    return await backend_client.post(
        endpoint=f"{_b(workspace_id)}/campaign/adset", data=payload
    )


async def create_ad(workspace_id: int, payload: dict):
    logger.info("Creating ad", workspace_id=workspace_id, name=payload.get("name"))
    return await backend_client.post(
        endpoint=f"{_b(workspace_id)}/campaign/ad", data=payload
    )


# =========================================================
# LAUNCH CAMPAIGN (full flow)
# =========================================================

async def launch_campaign(workspace_id: int, payload: dict):
    logger.info("Launching campaign", workspace_id=workspace_id)
    return await backend_client.post(
        endpoint=f"{_b(workspace_id)}/launch-campaign", data=payload
    )


async def launch_campaign_batch(workspace_id: int, campaigns: list[dict]):
    logger.info("Launching batch campaigns", workspace_id=workspace_id, count=len(campaigns))
    return await backend_client.post(
        endpoint=f"{_b(workspace_id)}/launch-campaign/batch",
        data={"campaigns": campaigns},
    )


async def get_launch_job_status(workspace_id: int, job_id: str):
    logger.info("Getting launch job status", job_id=job_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/launch-campaign/job/{job_id}"
    )


async def list_launch_jobs(workspace_id: int, page: int = 1, page_size: int = 20):
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/launch-campaign/jobs",
        params={"page": page, "page_size": page_size},
    )


async def get_campaign_history(workspace_id: int, account_id: str):
    logger.info("Getting campaign history", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"{_b(workspace_id)}/campaign/history",
        params={"account_id": account_id},
    )


# =========================================================
# TEMPLATES
# =========================================================

async def create_campaign_template(workspace_id: int, payload: dict):
    logger.info("Creating campaign template", workspace_id=workspace_id)
    return await backend_client.post(
        endpoint=f"{_b(workspace_id)}/templates", data=payload
    )


async def list_campaign_templates(workspace_id: int):
    logger.info("Listing campaign templates", workspace_id=workspace_id)
    return await backend_client.get(endpoint=f"{_b(workspace_id)}/templates")


async def update_campaign_template(workspace_id: int, template_id: int, payload: dict):
    logger.info("Updating campaign template", template_id=template_id)
    return await backend_client.put(
        endpoint=f"{_b(workspace_id)}/templates/{template_id}", data=payload
    )


async def delete_campaign_template(workspace_id: int, template_id: int):
    logger.info("Deleting campaign template", template_id=template_id)
    return await backend_client.delete(
        endpoint=f"{_b(workspace_id)}/templates/{template_id}"
    )
