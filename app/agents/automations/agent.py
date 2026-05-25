# app/agents/automations/agent.py
#
# Automation agent — full CRUD + toggle + logs.
# Write operations validate against strict Pydantic schemas
# and ask the user for missing fields before proceeding.

import json

from pydantic import ValidationError

from app.core.orchestrator.state import AgentState
from app.tools.automation_tools import (
    create_automation_rule,
    list_automation_rules,
    get_automation_rule,
    update_automation_rule,
    delete_automation_rule,
    toggle_automation_rule,
    get_automation_rule_logs,
    list_all_automation_logs,
)
from app.tools.schemas import (
    CreateAutomationSchema,
    UpdateAutomationSchema,
)
from app.services.db_context import (
    resolve_automation_rule_id_from_name,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("automation-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
LIST_KEYWORDS = ["list", "show", "all automations", "my automations"]
CREATE_KEYWORDS = ["create automation", "new automation", "add automation", "set up automation"]
UPDATE_KEYWORDS = ["update automation", "edit automation", "modify automation", "change automation"]
DELETE_KEYWORDS = ["delete automation", "remove automation"]
TOGGLE_KEYWORDS = ["toggle automation", "enable automation", "disable automation", "pause automation"]
LOGS_KEYWORDS = ["automation logs", "automation history", "automation activity"]


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
# AUTOMATION AGENT
# =========================================================
async def run_automation_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}
        db_ctx = state.get("db_context") or {}

        logger.info("Running automation agent", workspace_id=workspace_id)

        # ─────────────────────────────────────────────────────
        # AUTO-RESOLVE IDs FROM DB CONTEXT
        # ─────────────────────────────────────────────────────

        # Resolve rule_id from automation rule name
        if extra.get("rule_name") and not extra.get("rule_id"):
            resolved = resolve_automation_rule_id_from_name(db_ctx, str(extra["rule_name"]))
            if resolved:
                extra = {**extra, "rule_id": resolved}

        tool_result = {}
        action_taken = "none"

        # =====================================================
        # CREATE AUTOMATION
        # =====================================================
        if any(kw in message_lower for kw in CREATE_KEYWORDS):

            try:
                schema = CreateAutomationSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateAutomationSchema",
                    [
                        "name — Rule name",
                        "action_type — pause | resume | increase_budget | decrease_budget",
                        "platform — facebook | google | tiktok",
                        "entity_level — campaign | adset | ad",
                        "entity_ids — List of entity IDs to monitor",
                        "trigger_type — interval | schedule",
                        "frequency_minutes — Check interval in minutes (for interval trigger)",
                        "conditions — List of {metric, operator, value, unit?, conjunction?}",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await create_automation_rule(
                workspace_id=workspace_id,
                payload=schema.model_dump(exclude_none=True),
            )
            action_taken = "create_automation_rule"

        # =====================================================
        # UPDATE AUTOMATION
        # =====================================================
        elif any(kw in message_lower for kw in UPDATE_KEYWORDS):

            rule_id = extra.get("rule_id")
            if not rule_id:
                state["ui_json"] = _missing_fields_response(
                    "UpdateAutomationSchema",
                    ["rule_id — ID of the automation rule to update"],
                )
                state["success"] = True
                return state

            try:
                schema = UpdateAutomationSchema(**{k: v for k, v in extra.items() if k != "rule_id"})
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await update_automation_rule(
                workspace_id=workspace_id,
                rule_id=int(rule_id),
                payload=schema.model_dump(exclude_none=True),
            )
            action_taken = "update_automation_rule"

        # =====================================================
        # DELETE AUTOMATION
        # =====================================================
        elif any(kw in message_lower for kw in DELETE_KEYWORDS):

            rule_id = extra.get("rule_id")
            if not rule_id:
                state["ui_json"] = _missing_fields_response(
                    "DeleteAutomation",
                    ["rule_id — ID of the automation rule to delete"],
                )
                state["success"] = True
                return state

            tool_result = await delete_automation_rule(
                workspace_id=workspace_id,
                rule_id=int(rule_id),
            )
            action_taken = "delete_automation_rule"

        # =====================================================
        # TOGGLE AUTOMATION
        # =====================================================
        elif any(kw in message_lower for kw in TOGGLE_KEYWORDS):

            rule_id = extra.get("rule_id")
            if not rule_id:
                state["ui_json"] = _missing_fields_response(
                    "ToggleAutomation",
                    ["rule_id — ID of the automation rule to toggle"],
                )
                state["success"] = True
                return state

            tool_result = await toggle_automation_rule(
                workspace_id=workspace_id,
                rule_id=int(rule_id),
            )
            action_taken = "toggle_automation_rule"

        # =====================================================
        # AUTOMATION LOGS
        # =====================================================
        elif any(kw in message_lower for kw in LOGS_KEYWORDS):

            rule_id = extra.get("rule_id")
            if rule_id:
                tool_result = await get_automation_rule_logs(
                    workspace_id=workspace_id,
                    rule_id=int(rule_id),
                )
                action_taken = "get_automation_rule_logs"
            else:
                tool_result = await list_all_automation_logs(
                    workspace_id=workspace_id,
                    platform=extra.get("platform"),
                )
                action_taken = "list_all_automation_logs"

        # =====================================================
        # LIST AUTOMATIONS (default)
        # =====================================================
        else:

            tool_result = await list_automation_rules(
                workspace_id=workspace_id,
                platform=extra.get("platform"),
            )
            action_taken = "list_automation_rules"

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

        logger.error("Automation agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Automation Error",
            "message": str(e),
        })

        return state
