# app/agents/workspace/agent.py
#
# Workspace agent — create, update, list, delete workspaces
# and manage workspace timezone.

import json

from pydantic import ValidationError

from app.core.orchestrator.state import AgentState
from app.tools.workspace_tools import (
    create_workspace,
    update_workspace,
    toggle_workspace_status,
    list_workspaces,
    delete_workspaces,
)
from app.tools.timezone_tools import (
    get_workspace_timezone,
    set_workspace_timezone,
    list_timezones,
)
from app.tools.schemas import (
    CreateWorkspaceSchema,
    UpdateWorkspaceSchema,
    DeleteWorkspacesSchema,
    SetWorkspaceTimezoneSchema,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("workspace-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
CREATE_KEYWORDS = ["create workspace", "new workspace", "add workspace"]
UPDATE_KEYWORDS = ["update workspace", "edit workspace", "rename workspace"]
DELETE_KEYWORDS = ["delete workspace", "remove workspace"]
LIST_KEYWORDS = ["list workspaces", "show workspaces", "my workspaces", "all workspaces"]
TIMEZONE_KEYWORDS = ["timezone", "time zone", "set timezone", "workspace timezone"]


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
# WORKSPACE AGENT
# =========================================================
async def run_workspace_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}

        logger.info("Running workspace agent", workspace_id=workspace_id)

        tool_result = {}
        action_taken = "none"

        # =====================================================
        # CREATE WORKSPACE
        # =====================================================
        if any(kw in message_lower for kw in CREATE_KEYWORDS):

            try:
                schema = CreateWorkspaceSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateWorkspaceSchema",
                    [
                        "name — Workspace name",
                        "default_timezone — e.g. Asia/Kolkata",
                        "media_buyer_code_wise — true | false",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await create_workspace(payload=schema.model_dump())
            action_taken = "create_workspace"

        # =====================================================
        # UPDATE WORKSPACE
        # =====================================================
        elif any(kw in message_lower for kw in UPDATE_KEYWORDS):

            try:
                schema = UpdateWorkspaceSchema(**extra)
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await update_workspace(
                workspace_id=workspace_id,
                payload=schema.model_dump(exclude_none=True),
            )
            action_taken = "update_workspace"

        # =====================================================
        # DELETE WORKSPACE
        # =====================================================
        elif any(kw in message_lower for kw in DELETE_KEYWORDS):

            workspace_ids = extra.get("workspace_ids")
            if not workspace_ids:
                state["ui_json"] = _missing_fields_response(
                    "DeleteWorkspacesSchema",
                    ["workspace_ids — List of workspace IDs to delete"],
                )
                state["success"] = True
                return state

            try:
                schema = DeleteWorkspacesSchema(workspace_ids=workspace_ids)
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await delete_workspaces(workspace_ids=schema.workspace_ids)
            action_taken = "delete_workspaces"

        # =====================================================
        # TIMEZONE
        # =====================================================
        elif any(kw in message_lower for kw in TIMEZONE_KEYWORDS):

            if "set" in message_lower or "change" in message_lower or "update" in message_lower:
                timezone = extra.get("timezone")
                if not timezone:
                    # Show available timezones to help user
                    tz_list = await list_timezones()
                    state["ui_json"] = _missing_fields_response(
                        "SetWorkspaceTimezoneSchema",
                        ["timezone — e.g. Asia/Kolkata, America/New_York (use 'list timezones' to see all)"],
                    )
                    state["success"] = True
                    return state

                try:
                    schema = SetWorkspaceTimezoneSchema(timezone=timezone)
                except ValidationError as e:
                    state["ui_json"] = _validation_error_response(e)
                    state["success"] = True
                    return state

                tool_result = await set_workspace_timezone(
                    workspace_id=workspace_id,
                    timezone=schema.timezone,
                )
                action_taken = "set_workspace_timezone"

            elif "list" in message_lower or "available" in message_lower:
                tool_result = await list_timezones(q=extra.get("q"))
                action_taken = "list_timezones"

            else:
                tool_result = await get_workspace_timezone(workspace_id=workspace_id)
                action_taken = "get_workspace_timezone"

        # =====================================================
        # LIST WORKSPACES (default)
        # =====================================================
        else:

            tool_result = await list_workspaces()
            action_taken = "list_workspaces"

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

        logger.error("Workspace agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Workspace Error",
            "message": str(e),
        })

        return state
