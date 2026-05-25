# app/agents/campaigns/agent.py
#
# Campaign agent — handles status, budget, bid, delete, and
# campaign-launcher operations.  For any write operation the
# agent validates the user-supplied data against the strict
# Pydantic schemas before calling the backend.

import json
from typing import Any

from pydantic import ValidationError

from app.core.orchestrator.state import AgentState
from app.tools.campaign_status_tools import (
    pause_campaigns,
    resume_campaigns,
    bulk_change_campaign_status,
    bulk_change_campaign_budget,
    bulk_change_adset_budget,
    bulk_change_adset_bid,
    bulk_change_adset_status,
    bulk_change_ad_status,
    bulk_delete_campaigns,
)
from app.tools.campaign_launcher_tools import (
    create_campaign,
    create_adset,
    create_ad,
    launch_campaign,
    launch_campaign_batch,
    get_launch_job_status,
    list_launch_jobs,
    get_campaign_history,
    list_campaign_templates,
    create_campaign_template,
    delete_campaign_template,
)
from app.tools.campaign_workflow import (
    workflow_launch_full_campaign,
    workflow_bulk_scale_campaigns,
    workflow_pause_all_for_account,
)
from app.tools.schemas import (
    CampaignStatusItem,
    CampaignBudgetItem,
    AdsetBudgetItem,
    AdsetBidItem,
    AdsetStatusItem,
    AdStatusItem,
    CampaignDeleteItem,
    CreateCampaignSchema,
    CreateAdsetSchema,
    CreateAdSchema,
    LaunchCampaignSchema,
    CampaignTemplateSchema,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("campaign-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
PAUSE_KEYWORDS = ["pause", "stop campaign", "disable campaign"]
RESUME_KEYWORDS = ["resume", "activate campaign", "enable campaign", "unpause"]
BUDGET_KEYWORDS = ["budget", "change budget", "update budget", "set budget"]
BID_KEYWORDS = ["bid", "change bid", "update bid", "set bid"]
DELETE_KEYWORDS = ["delete campaign", "remove campaign"]
LAUNCH_KEYWORDS = ["launch campaign", "create campaign", "new campaign", "start campaign"]
CREATE_ADSET_KEYWORDS = ["create adset", "new adset", "add adset"]
CREATE_AD_KEYWORDS = ["create ad", "new ad", "add ad"]
HISTORY_KEYWORDS = ["campaign history", "launch history", "past campaigns"]
TEMPLATE_KEYWORDS = ["template", "campaign template"]
SCALE_KEYWORDS = ["scale campaign", "scale budget", "increase budget by", "decrease budget by", "scale by"]
PAUSE_ALL_KEYWORDS = ["pause all", "pause all campaigns", "stop all campaigns"]


def _missing_fields_response(schema_name: str, fields: list[str]) -> str:
    """Return a structured JSON asking the user for missing fields."""
    return json.dumps({
        "type": "missing_fields",
        "title": f"More information needed",
        "message": (
            f"To complete this action I need the following details. "
            f"Please provide them:"
        ),
        "schema": schema_name,
        "required_fields": fields,
    })


def _validation_error_response(e: ValidationError) -> str:
    missing = [err["loc"][0] for err in e.errors() if err["type"] == "missing"]
    invalid = [
        f"{err['loc'][0]}: {err['msg']}"
        for err in e.errors()
        if err["type"] != "missing"
    ]
    return json.dumps({
        "type": "validation_error",
        "title": "Invalid input",
        "missing_fields": missing,
        "invalid_fields": invalid,
        "message": "Please correct the above fields and try again.",
    })


# =========================================================
# CAMPAIGN AGENT
# =========================================================
async def run_campaign_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}

        logger.info("Running campaign agent", workspace_id=workspace_id)

        tool_result: Any = {}
        action_taken = "none"

        # =====================================================
        # PAUSE CAMPAIGNS
        # =====================================================
        if any(kw in message_lower for kw in PAUSE_KEYWORDS):

            items = extra.get("items", [])
            if not items:
                state["ui_json"] = _missing_fields_response(
                    "CampaignStatusItem",
                    ["items: list of {account_id, campaign_id, platform}"],
                )
                state["success"] = True
                return state

            try:
                validated = [CampaignStatusItem(**{**i, "status": "PAUSED"}) for i in items]
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await pause_campaigns(
                workspace_id=workspace_id,
                items=[v.model_dump() for v in validated],
            )
            action_taken = "pause_campaigns"

        # =====================================================
        # RESUME CAMPAIGNS
        # =====================================================
        elif any(kw in message_lower for kw in RESUME_KEYWORDS):

            items = extra.get("items", [])
            if not items:
                state["ui_json"] = _missing_fields_response(
                    "CampaignStatusItem",
                    ["items: list of {account_id, campaign_id, platform}"],
                )
                state["success"] = True
                return state

            try:
                validated = [CampaignStatusItem(**{**i, "status": "ACTIVE"}) for i in items]
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await resume_campaigns(
                workspace_id=workspace_id,
                items=[v.model_dump() for v in validated],
            )
            action_taken = "resume_campaigns"

        # =====================================================
        # CHANGE CAMPAIGN BUDGET
        # =====================================================
        elif any(kw in message_lower for kw in BUDGET_KEYWORDS):

            items = extra.get("items", [])
            if not items:
                state["ui_json"] = _missing_fields_response(
                    "CampaignBudgetItem",
                    ["items: list of {account_id, campaign_id, budget, budget_type (DAILY|LIFETIME), status}"],
                )
                state["success"] = True
                return state

            try:
                validated = [CampaignBudgetItem(**i) for i in items]
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await bulk_change_campaign_budget(
                workspace_id=workspace_id,
                items=[v.model_dump() for v in validated],
            )
            action_taken = "bulk_change_campaign_budget"

        # =====================================================
        # DELETE CAMPAIGNS
        # =====================================================
        elif any(kw in message_lower for kw in DELETE_KEYWORDS):

            items = extra.get("items", [])
            if not items:
                state["ui_json"] = _missing_fields_response(
                    "CampaignDeleteItem",
                    ["items: list of {account_id, campaign_id, platform}"],
                )
                state["success"] = True
                return state

            try:
                validated = [CampaignDeleteItem(**i) for i in items]
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await bulk_delete_campaigns(
                workspace_id=workspace_id,
                items=[v.model_dump() for v in validated],
            )
            action_taken = "bulk_delete_campaigns"

        # =====================================================
        # LAUNCH CAMPAIGN (full flow)
        # =====================================================
        elif any(kw in message_lower for kw in LAUNCH_KEYWORDS):

            try:
                schema = LaunchCampaignSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "LaunchCampaignSchema",
                    [
                        "account_id — Ad account ID",
                        "campaign_name — Campaign name",
                        "objective — e.g. OUTCOME_SALES, OUTCOME_TRAFFIC",
                        "campaign_status — ACTIVE or PAUSED",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await launch_campaign(
                workspace_id=workspace_id,
                payload=schema.model_dump(),
            )
            action_taken = "launch_campaign"

        # =====================================================
        # CREATE CAMPAIGN (step-by-step)
        # =====================================================
        elif any(kw in message_lower for kw in CREATE_ADSET_KEYWORDS):

            try:
                schema = CreateAdsetSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateAdsetSchema",
                    [
                        "campaign_id — Parent campaign ID",
                        "account_id — Ad account ID",
                        "name — Ad set name",
                        "status — ACTIVE or PAUSED",
                        "optimization_goal — e.g. OFFSITE_CONVERSIONS",
                        "daily_budget — Budget amount as string",
                        "targeting — Targeting spec dict",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await create_adset(
                workspace_id=workspace_id,
                payload=schema.model_dump(),
            )
            action_taken = "create_adset"

        # =====================================================
        # CAMPAIGN HISTORY
        # =====================================================
        elif any(kw in message_lower for kw in HISTORY_KEYWORDS):

            account_id = extra.get("account_id")
            if not account_id:
                state["ui_json"] = _missing_fields_response(
                    "CampaignHistoryParams",
                    ["account_id — Ad account ID"],
                )
                state["success"] = True
                return state

            tool_result = await get_campaign_history(
                workspace_id=workspace_id,
                account_id=account_id,
            )
            action_taken = "get_campaign_history"

        # =====================================================
        # CAMPAIGN TEMPLATES
        # =====================================================
        elif any(kw in message_lower for kw in TEMPLATE_KEYWORDS):

            if "list" in message_lower or "show" in message_lower:
                tool_result = await list_campaign_templates(workspace_id=workspace_id)
                action_taken = "list_campaign_templates"
            elif "create" in message_lower or "save" in message_lower:
                try:
                    schema = CampaignTemplateSchema(**extra)
                except ValidationError as e:
                    missing = [err["loc"][0] for err in e.errors()]
                    state["ui_json"] = _missing_fields_response(
                        "CampaignTemplateSchema",
                        [
                            "template_name — Template name",
                            "description — Optional description",
                            "data — Template data payload (dict)",
                        ] if not extra else [f"{f}" for f in missing],
                    )
                    state["success"] = True
                    return state

                tool_result = await create_campaign_template(
                    workspace_id=workspace_id,
                    payload=schema.model_dump(),
                )
                action_taken = "create_campaign_template"

        # =====================================================
        # SCALE CAMPAIGNS (workflow)
        # =====================================================
        elif any(kw in message_lower for kw in SCALE_KEYWORDS):

            items = extra.get("items", [])
            scale_factor = extra.get("scale_factor")

            if not items or scale_factor is None:
                state["ui_json"] = _missing_fields_response(
                    "BulkScaleCampaigns",
                    [
                        "items: list of {account_id, campaign_id, budget, budget_type, status}",
                        "scale_factor: float — e.g. 1.5 for +50%, 0.8 for -20%",
                    ],
                )
                state["success"] = True
                return state

            wf = await workflow_bulk_scale_campaigns(
                workspace_id=workspace_id,
                items=items,
                scale_factor=float(scale_factor),
            )
            tool_result = wf.to_dict()
            action_taken = "workflow_bulk_scale_campaigns"

        # =====================================================
        # PAUSE ALL CAMPAIGNS FOR ACCOUNT (workflow)
        # =====================================================
        elif any(kw in message_lower for kw in PAUSE_ALL_KEYWORDS):

            account_id = extra.get("account_id")
            platform = extra.get("platform")
            campaign_ids = extra.get("campaign_ids", [])

            if not account_id or not platform or not campaign_ids:
                state["ui_json"] = _missing_fields_response(
                    "PauseAllForAccount",
                    [
                        "account_id — Ad account ID",
                        "platform — facebook | google | tiktok",
                        "campaign_ids — list of campaign IDs to pause",
                    ],
                )
                state["success"] = True
                return state

            wf = await workflow_pause_all_for_account(
                workspace_id=workspace_id,
                account_id=account_id,
                platform=platform,
                campaign_ids=campaign_ids,
            )
            tool_result = wf.to_dict()
            action_taken = "workflow_pause_all_for_account"

        # =====================================================
        # STORE TOOL INFO
        # =====================================================
        state["tools_used"].append(action_taken)
        state["tool_results"].append(tool_result)

        # =====================================================
        # AI RESPONSE
        # =====================================================
        ai_result = await generate_ai_response(
            user_message=message,
            tool_data=tool_result,
            db_context=state.get("db_context"),
        )

        state["ui_json"] = ai_result["ui_json"]
        state["tokens_used"] = ai_result["tokens_used"]
        state["success"] = True

        return state

    except Exception as e:

        logger.error("Campaign agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Campaign Error",
            "message": str(e),
        })

        return state
