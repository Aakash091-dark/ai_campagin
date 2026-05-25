# app/agents/smart_alerts/agent.py
#
# Smart alerts agent — full CRUD + toggle + logs.
# Validates all write operations against strict Pydantic schemas.

import json

from pydantic import ValidationError

from app.core.orchestrator.state import AgentState
from app.tools.smart_alert_tools import (
    create_smart_alert,
    list_smart_alerts,
    get_smart_alert,
    update_smart_alert,
    delete_smart_alert,
    toggle_smart_alert,
    get_smart_alert_logs,
    list_all_smart_alert_logs,
)
from app.tools.schemas import (
    CreateSmartAlertSchema,
    UpdateSmartAlertSchema,
)
from app.services.db_context import (
    resolve_smart_alert_id_from_name,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("smart-alerts-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
CREATE_KEYWORDS = ["create alert", "new alert", "add alert", "set up alert", "smart alert"]
UPDATE_KEYWORDS = ["update alert", "edit alert", "modify alert", "change alert"]
DELETE_KEYWORDS = ["delete alert", "remove alert"]
TOGGLE_KEYWORDS = ["toggle alert", "enable alert", "disable alert", "pause alert"]
LOGS_KEYWORDS = ["alert logs", "alert history", "alert activity", "triggered alerts"]
LIST_KEYWORDS = ["list alerts", "show alerts", "my alerts", "all alerts"]


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
# SMART ALERTS AGENT
# =========================================================
async def run_smart_alerts_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}
        db_ctx = state.get("db_context") or {}

        logger.info("Running smart alerts agent", workspace_id=workspace_id)

        # ─────────────────────────────────────────────────────
        # AUTO-RESOLVE IDs FROM DB CONTEXT
        # ─────────────────────────────────────────────────────

        # Resolve alert_id from alert name
        if extra.get("alert_name") and not extra.get("alert_id"):
            resolved = resolve_smart_alert_id_from_name(db_ctx, str(extra["alert_name"]))
            if resolved:
                extra = {**extra, "alert_id": resolved}

        tool_result = {}
        action_taken = "none"

        # =====================================================
        # CREATE SMART ALERT
        # =====================================================
        if any(kw in message_lower for kw in CREATE_KEYWORDS):

            try:
                schema = CreateSmartAlertSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateSmartAlertSchema",
                    [
                        "alert_name — Alert name",
                        "scope — e.g. Campaign Level, Ad Set Level",
                        "target — e.g. platform or specific",
                        "platform — facebook | google | tiktok",
                        "entity_target — all | specific",
                        "entity_ids — List of entity IDs (if entity_target=specific)",
                        "conditions — List of {metric, condition, value, unit?, period?, logical_operator?}",
                        "timezone — e.g. America/New_York",
                        "notify_in_app — true | false",
                        "notify_email — true | false",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await create_smart_alert(
                workspace_id=workspace_id,
                payload=schema.model_dump(exclude_none=True),
            )
            action_taken = "create_smart_alert"

        # =====================================================
        # UPDATE SMART ALERT
        # =====================================================
        elif any(kw in message_lower for kw in UPDATE_KEYWORDS):

            alert_id = extra.get("alert_id")
            if not alert_id:
                state["ui_json"] = _missing_fields_response(
                    "UpdateSmartAlertSchema",
                    ["alert_id — ID of the alert to update"],
                )
                state["success"] = True
                return state

            try:
                schema = UpdateSmartAlertSchema(
                    **{k: v for k, v in extra.items() if k != "alert_id"}
                )
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await update_smart_alert(
                workspace_id=workspace_id,
                alert_id=int(alert_id),
                payload=schema.model_dump(exclude_none=True),
            )
            action_taken = "update_smart_alert"

        # =====================================================
        # DELETE SMART ALERT
        # =====================================================
        elif any(kw in message_lower for kw in DELETE_KEYWORDS):

            alert_id = extra.get("alert_id")
            if not alert_id:
                state["ui_json"] = _missing_fields_response(
                    "DeleteSmartAlert",
                    ["alert_id — ID of the alert to delete"],
                )
                state["success"] = True
                return state

            tool_result = await delete_smart_alert(
                workspace_id=workspace_id,
                alert_id=int(alert_id),
            )
            action_taken = "delete_smart_alert"

        # =====================================================
        # TOGGLE SMART ALERT
        # =====================================================
        elif any(kw in message_lower for kw in TOGGLE_KEYWORDS):

            alert_id = extra.get("alert_id")
            if not alert_id:
                state["ui_json"] = _missing_fields_response(
                    "ToggleSmartAlert",
                    ["alert_id — ID of the alert to toggle"],
                )
                state["success"] = True
                return state

            tool_result = await toggle_smart_alert(
                workspace_id=workspace_id,
                alert_id=int(alert_id),
            )
            action_taken = "toggle_smart_alert"

        # =====================================================
        # ALERT LOGS
        # =====================================================
        elif any(kw in message_lower for kw in LOGS_KEYWORDS):

            alert_id = extra.get("alert_id")
            if alert_id:
                tool_result = await get_smart_alert_logs(
                    workspace_id=workspace_id,
                    alert_id=int(alert_id),
                )
                action_taken = "get_smart_alert_logs"
            else:
                tool_result = await list_all_smart_alert_logs(
                    workspace_id=workspace_id,
                    platform=extra.get("platform"),
                )
                action_taken = "list_all_smart_alert_logs"

        # =====================================================
        # LIST SMART ALERTS (default)
        # =====================================================
        else:

            tool_result = await list_smart_alerts(
                workspace_id=workspace_id,
                platform=extra.get("platform"),
                is_active=extra.get("is_active"),
            )
            action_taken = "list_smart_alerts"

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

        logger.error("Smart alerts agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Smart Alerts Error",
            "message": str(e),
        })

        return state
