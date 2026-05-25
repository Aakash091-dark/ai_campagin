# app/agents/reporting/agent.py
#
# Reporting agent — handles report generation, config,
# slot submission, and analytics reporting queries.

import json

from pydantic import ValidationError

from app.core.orchestrator.state import AgentState
from app.tools.reporting_tools import (
    generate_workspace_report,
    get_analytics_reporting,
    set_reporting_config,
    get_reporting_slots,
    submit_report,
    submit_zero_report,
)
from app.tools.schemas import (
    CreateReportingConfigSchema,
    SubmitReportSchema,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("reporting-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
CONFIG_KEYWORDS = ["configure reporting", "set up reporting", "reporting config", "reporting slots config"]
SLOTS_KEYWORDS = ["reporting slots", "show slots", "list slots", "get slots"]
SUBMIT_KEYWORDS = ["submit report", "log report", "report data"]
ZERO_KEYWORDS = ["zero report", "no data report", "empty report"]
ANALYTICS_KEYWORDS = ["analytics report", "reporting analytics", "performance report"]


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
# REPORTING AGENT
# =========================================================
async def run_reporting_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}

        logger.info("Running reporting agent", workspace_id=workspace_id)

        tool_result = {}
        action_taken = "none"

        # =====================================================
        # CONFIGURE REPORTING SLOTS
        # =====================================================
        if any(kw in message_lower for kw in CONFIG_KEYWORDS):

            try:
                schema = CreateReportingConfigSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateReportingConfigSchema",
                    [
                        "slots_config — {s1: 'HH:MM', s2: 'HH:MM', s3: 'HH:MM'}",
                        "timezone — e.g. Asia/Kolkata",
                        "buffer_before_min — Minutes before slot",
                        "buffer_after_min — Minutes after slot",
                        "is_active — true | false",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await set_reporting_config(
                workspace_id=workspace_id,
                payload=schema.model_dump(),
            )
            action_taken = "set_reporting_config"

        # =====================================================
        # GET REPORTING SLOTS
        # =====================================================
        elif any(kw in message_lower for kw in SLOTS_KEYWORDS):

            tool_result = await get_reporting_slots(workspace_id=workspace_id)
            action_taken = "get_reporting_slots"

        # =====================================================
        # SUBMIT ZERO REPORT
        # =====================================================
        elif any(kw in message_lower for kw in ZERO_KEYWORDS):

            tool_result = await submit_zero_report(workspace_id=workspace_id)
            action_taken = "submit_zero_report"

        # =====================================================
        # SUBMIT REPORT
        # =====================================================
        elif any(kw in message_lower for kw in SUBMIT_KEYWORDS):

            try:
                schema = SubmitReportSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "SubmitReportSchema",
                    [
                        "slot_id — e.g. s1, s2, s3",
                        "date — YYYY-MM-DD",
                        "data — {platform: {spend, revenue, leads}} e.g. {facebook: {spend: 100, revenue: 300, leads: 20}}",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await submit_report(
                workspace_id=workspace_id,
                payload=schema.model_dump(),
            )
            action_taken = "submit_report"

        # =====================================================
        # ANALYTICS REPORTING
        # =====================================================
        elif any(kw in message_lower for kw in ANALYTICS_KEYWORDS):

            start_date = extra.get("start_date")
            end_date = extra.get("end_date")

            if not start_date or not end_date:
                state["ui_json"] = _missing_fields_response(
                    "AnalyticsReportingParams",
                    ["start_date — YYYY-MM-DD", "end_date — YYYY-MM-DD"],
                )
                state["success"] = True
                return state

            tool_result = await get_analytics_reporting(
                workspace_id=workspace_id,
                start_date=start_date,
                end_date=end_date,
            )
            action_taken = "get_analytics_reporting"

        # =====================================================
        # DEFAULT: WORKSPACE REPORT SUMMARY
        # =====================================================
        else:

            tool_result = await generate_workspace_report(workspace_id=workspace_id)
            action_taken = "generate_workspace_report"

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

        logger.error("Reporting agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Reporting Error",
            "message": str(e),
        })

        return state
