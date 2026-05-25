# app/tools/campaign_workflow.py
#
# Campaign execution workflows.
# Orchestrates multi-step operations (create campaign → adset → ad)
# with per-step logging, rollback tracking, and structured results.
#
# These are called by the campaigns agent for complex launch flows.

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from app.tools.campaign_launcher_tools import (
    create_campaign,
    create_adset,
    create_ad,
    launch_campaign,
    launch_campaign_batch,
)
from app.tools.campaign_status_tools import (
    bulk_change_campaign_status,
    bulk_change_campaign_budget,
    bulk_change_adset_budget,
    bulk_change_adset_bid,
    bulk_change_adset_status,
    bulk_change_ad_status,
    bulk_delete_campaigns,
)
from app.config.logging import get_logger

logger = get_logger("campaign-workflow")


# =========================================================
# STEP RESULT
# =========================================================
@dataclass
class StepResult:
    step: str
    success: bool
    data: Any = None
    error: str | None = None


@dataclass
class WorkflowResult:
    workflow: str
    success: bool
    steps: list[StepResult] = field(default_factory=list)
    rollback_steps: list[StepResult] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "workflow": self.workflow,
            "success": self.success,
            "summary": self.summary,
            "steps": [
                {"step": s.step, "success": s.success, "data": s.data, "error": s.error}
                for s in self.steps
            ],
            "rollback_steps": [
                {"step": s.step, "success": s.success, "error": s.error}
                for s in self.rollback_steps
            ],
        }


# =========================================================
# WORKFLOW: FULL CAMPAIGN LAUNCH
# campaign → adset → ad in sequence
# =========================================================
async def workflow_launch_full_campaign(
    workspace_id: int,
    campaign_payload: dict,
    adset_payload: dict,
    ad_payload: dict,
) -> WorkflowResult:
    """
    Three-step campaign launch:
      1. Create campaign
      2. Create adset (uses campaign_id from step 1)
      3. Create ad (uses adset_id from step 2)

    On any failure, attempts to delete already-created entities (rollback).
    """
    result = WorkflowResult(workflow="launch_full_campaign", success=False)
    created_campaign_id: str | None = None
    created_adset_id: str | None = None

    logger.info(
        "Workflow start: launch_full_campaign",
        workspace_id=workspace_id,
        account_id=campaign_payload.get("account_id"),
    )

    # ── Step 1: Create campaign ────────────────────────────────────
    try:
        camp_resp = await create_campaign(
            workspace_id=workspace_id,
            payload=campaign_payload,
        )
        if camp_resp.get("error"):
            raise RuntimeError(camp_resp.get("message", "Campaign creation failed"))

        created_campaign_id = (
            camp_resp.get("data", {}).get("campaign_id")
            or camp_resp.get("campaign_id")
        )
        result.steps.append(StepResult("create_campaign", True, data=camp_resp))
        logger.info("Step 1 OK: campaign created", campaign_id=created_campaign_id)

    except Exception as exc:
        result.steps.append(StepResult("create_campaign", False, error=str(exc)))
        result.summary = f"Failed at step 1 (create_campaign): {exc}"
        logger.error("Workflow failed at step 1", error=str(exc))
        return result

    # ── Step 2: Create adset ───────────────────────────────────────
    try:
        adset_payload = {**adset_payload, "campaign_id": created_campaign_id}
        adset_resp = await create_adset(
            workspace_id=workspace_id,
            payload=adset_payload,
        )
        if adset_resp.get("error"):
            raise RuntimeError(adset_resp.get("message", "Adset creation failed"))

        created_adset_id = (
            adset_resp.get("data", {}).get("adset_id")
            or adset_resp.get("adset_id")
        )
        result.steps.append(StepResult("create_adset", True, data=adset_resp))
        logger.info("Step 2 OK: adset created", adset_id=created_adset_id)

    except Exception as exc:
        result.steps.append(StepResult("create_adset", False, error=str(exc)))
        result.summary = f"Failed at step 2 (create_adset): {exc}"
        logger.error("Workflow failed at step 2 — rolling back campaign", error=str(exc))

        # Rollback: delete the campaign we just created
        if created_campaign_id:
            try:
                rb = await bulk_delete_campaigns(
                    workspace_id=workspace_id,
                    items=[{
                        "account_id": campaign_payload.get("account_id", ""),
                        "campaign_id": created_campaign_id,
                        "platform": campaign_payload.get("platform", "facebook"),
                    }],
                )
                result.rollback_steps.append(StepResult("rollback_delete_campaign", True, data=rb))
            except Exception as rb_exc:
                result.rollback_steps.append(StepResult("rollback_delete_campaign", False, error=str(rb_exc)))

        return result

    # ── Step 3: Create ad ──────────────────────────────────────────
    try:
        ad_payload = {**ad_payload, "adset_id": created_adset_id}
        ad_resp = await create_ad(
            workspace_id=workspace_id,
            payload=ad_payload,
        )
        if ad_resp.get("error"):
            raise RuntimeError(ad_resp.get("message", "Ad creation failed"))

        result.steps.append(StepResult("create_ad", True, data=ad_resp))
        logger.info("Step 3 OK: ad created")

    except Exception as exc:
        result.steps.append(StepResult("create_ad", False, error=str(exc)))
        result.summary = f"Failed at step 3 (create_ad): {exc}"
        logger.error("Workflow failed at step 3 — rolling back campaign", error=str(exc))

        if created_campaign_id:
            try:
                rb = await bulk_delete_campaigns(
                    workspace_id=workspace_id,
                    items=[{
                        "account_id": campaign_payload.get("account_id", ""),
                        "campaign_id": created_campaign_id,
                        "platform": campaign_payload.get("platform", "facebook"),
                    }],
                )
                result.rollback_steps.append(StepResult("rollback_delete_campaign", True, data=rb))
            except Exception as rb_exc:
                result.rollback_steps.append(StepResult("rollback_delete_campaign", False, error=str(rb_exc)))

        return result

    result.success = True
    result.summary = (
        f"Campaign launched successfully. "
        f"campaign_id={created_campaign_id}, adset_id={created_adset_id}"
    )
    logger.info("Workflow complete: launch_full_campaign", workspace_id=workspace_id)
    return result


# =========================================================
# WORKFLOW: BULK SCALE CAMPAIGNS
# Increase/decrease budgets for a list of campaigns at once
# =========================================================
async def workflow_bulk_scale_campaigns(
    workspace_id: int,
    items: list[dict],
    scale_factor: float,
) -> WorkflowResult:
    """
    Scale campaign budgets by a multiplier.
    items: list of {account_id, campaign_id, budget, budget_type, status}
    scale_factor: e.g. 1.5 = +50%, 0.8 = -20%
    """
    result = WorkflowResult(workflow="bulk_scale_campaigns", success=False)

    scaled_items = [
        {**item, "budget": round(item["budget"] * scale_factor, 2)}
        for item in items
    ]

    logger.info(
        "Workflow start: bulk_scale_campaigns",
        workspace_id=workspace_id,
        count=len(scaled_items),
        scale_factor=scale_factor,
    )

    try:
        resp = await bulk_change_campaign_budget(
            workspace_id=workspace_id,
            items=scaled_items,
        )
        if resp.get("error"):
            raise RuntimeError(resp.get("message", "Budget change failed"))

        result.steps.append(StepResult("bulk_change_campaign_budget", True, data=resp))
        result.success = True
        result.summary = (
            f"Scaled {len(scaled_items)} campaign budgets by {scale_factor}x"
        )
        logger.info("Workflow complete: bulk_scale_campaigns")

    except Exception as exc:
        result.steps.append(StepResult("bulk_change_campaign_budget", False, error=str(exc)))
        result.summary = f"Budget scale failed: {exc}"
        logger.error("Workflow failed: bulk_scale_campaigns", error=str(exc))

    return result


# =========================================================
# WORKFLOW: PAUSE ALL CAMPAIGNS FOR ACCOUNT
# =========================================================
async def workflow_pause_all_for_account(
    workspace_id: int,
    account_id: str,
    platform: str,
    campaign_ids: list[str],
) -> WorkflowResult:
    """
    Pause every campaign in a given account.
    campaign_ids: list of platform campaign IDs to pause.
    """
    result = WorkflowResult(workflow="pause_all_for_account", success=False)

    items = [
        {"account_id": account_id, "campaign_id": cid, "platform": platform}
        for cid in campaign_ids
    ]

    logger.info(
        "Workflow start: pause_all_for_account",
        workspace_id=workspace_id,
        account_id=account_id,
        count=len(items),
    )

    try:
        from app.tools.campaign_status_tools import pause_campaigns
        resp = await pause_campaigns(workspace_id=workspace_id, items=items)
        if resp.get("error"):
            raise RuntimeError(resp.get("message", "Pause failed"))

        result.steps.append(StepResult("pause_campaigns", True, data=resp))
        result.success = True
        result.summary = f"Paused {len(items)} campaigns for account {account_id}"
        logger.info("Workflow complete: pause_all_for_account")

    except Exception as exc:
        result.steps.append(StepResult("pause_campaigns", False, error=str(exc)))
        result.summary = f"Pause failed: {exc}"
        logger.error("Workflow failed: pause_all_for_account", error=str(exc))

    return result
