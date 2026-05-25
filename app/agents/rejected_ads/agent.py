# app/agents/rejected_ads/agent.py
#
# Rejected ads agent — list, appeal, update creative,
# auto-swap/delete logs and toggles.

import json

from pydantic import ValidationError

from app.core.orchestrator.state import AgentState
from app.tools.rejected_ads_tools import (
    get_rejected_ads,
    appeal_rejected_ads,
    update_rejected_ad,
    get_auto_swap_logs,
    get_auto_swap_summary,
    get_auto_delete_logs,
    get_auto_delete_summary,
    toggle_auto_swap,
    toggle_auto_delete,
)
from app.tools.schemas import (
    AppealRejectedAdsSchema,
    UpdateRejectedAdSchema,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("rejected-ads-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
APPEAL_KEYWORDS = ["appeal", "appeal ad", "appeal rejected", "request review"]
UPDATE_KEYWORDS = ["update ad", "fix ad", "update creative", "change creative"]
AUTO_SWAP_KEYWORDS = ["auto swap", "auto-swap", "swap logs", "swap summary"]
AUTO_DELETE_KEYWORDS = ["auto delete", "auto-delete", "delete logs", "delete summary"]
TOGGLE_SWAP_KEYWORDS = ["enable auto swap", "disable auto swap", "toggle auto swap"]
TOGGLE_DELETE_KEYWORDS = ["enable auto delete", "disable auto delete", "toggle auto delete"]


def _missing_fields_response(schema_name: str, fields: list[str]) -> str:
    return json.dumps({
        "type": "missing_fields",
        "title": "More information needed",
        "message": "To complete this action I need the following details. Please provide them:",
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
# REJECTED ADS AGENT
# =========================================================
async def run_rejected_ads_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}

        logger.info("Running rejected ads agent", workspace_id=workspace_id)

        tool_result = {}
        action_taken = "none"

        # =====================================================
        # APPEAL REJECTED ADS
        # =====================================================
        if any(kw in message_lower for kw in APPEAL_KEYWORDS):

            try:
                schema = AppealRejectedAdsSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "AppealRejectedAdsSchema",
                    [
                        "items — List of {ad_id, account_id} to appeal",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await appeal_rejected_ads(
                workspace_id=workspace_id,
                items=[i.model_dump() for i in schema.items],
            )
            action_taken = "appeal_rejected_ads"

        # =====================================================
        # UPDATE REJECTED AD CREATIVE
        # =====================================================
        elif any(kw in message_lower for kw in UPDATE_KEYWORDS):

            try:
                schema = UpdateRejectedAdSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "UpdateRejectedAdSchema",
                    [
                        "items — List of {ad_id, account_id}",
                        "primary_text — New ad copy (optional)",
                        "headline — New headline (optional)",
                        "description — New description (optional)",
                        "call_to_action — e.g. SHOP_NOW (optional)",
                        "link — Destination URL (optional)",
                        "image_hash — New image hash (optional)",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await update_rejected_ad(
                workspace_id=workspace_id,
                payload=schema.model_dump(exclude_none=True),
            )
            action_taken = "update_rejected_ad"

        # =====================================================
        # TOGGLE AUTO-SWAP
        # =====================================================
        elif any(kw in message_lower for kw in TOGGLE_SWAP_KEYWORDS):

            account_id = extra.get("account_id")
            enabled = extra.get("enabled")
            if account_id is None or enabled is None:
                state["ui_json"] = _missing_fields_response(
                    "ToggleAutoSwap",
                    ["account_id — Account ID", "enabled — true | false"],
                )
                state["success"] = True
                return state

            tool_result = await toggle_auto_swap(
                workspace_id=workspace_id,
                account_id=int(account_id),
                enabled=bool(enabled),
            )
            action_taken = "toggle_auto_swap"

        # =====================================================
        # TOGGLE AUTO-DELETE
        # =====================================================
        elif any(kw in message_lower for kw in TOGGLE_DELETE_KEYWORDS):

            account_id = extra.get("account_id")
            enabled = extra.get("enabled")
            if account_id is None or enabled is None:
                state["ui_json"] = _missing_fields_response(
                    "ToggleAutoDelete",
                    ["account_id — Account ID", "enabled — true | false"],
                )
                state["success"] = True
                return state

            tool_result = await toggle_auto_delete(
                workspace_id=workspace_id,
                account_id=int(account_id),
                enabled=bool(enabled),
            )
            action_taken = "toggle_auto_delete"

        # =====================================================
        # AUTO-SWAP LOGS / SUMMARY
        # =====================================================
        elif any(kw in message_lower for kw in AUTO_SWAP_KEYWORDS):

            if "summary" in message_lower:
                tool_result = await get_auto_swap_summary(workspace_id=workspace_id)
                action_taken = "get_auto_swap_summary"
            else:
                tool_result = await get_auto_swap_logs(workspace_id=workspace_id)
                action_taken = "get_auto_swap_logs"

        # =====================================================
        # AUTO-DELETE LOGS / SUMMARY
        # =====================================================
        elif any(kw in message_lower for kw in AUTO_DELETE_KEYWORDS):

            if "summary" in message_lower:
                tool_result = await get_auto_delete_summary(workspace_id=workspace_id)
                action_taken = "get_auto_delete_summary"
            else:
                tool_result = await get_auto_delete_logs(workspace_id=workspace_id)
                action_taken = "get_auto_delete_logs"

        # =====================================================
        # DEFAULT: LIST REJECTED ADS
        # =====================================================
        else:

            tool_result = await get_rejected_ads(
                workspace_id=workspace_id,
                platform=extra.get("platform"),
            )
            action_taken = "get_rejected_ads"

        state["tools_used"].append(action_taken)
        state["tool_results"].append(tool_result)

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

        logger.error("Rejected ads agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Rejected Ads Error",
            "message": str(e),
        })

        return state
