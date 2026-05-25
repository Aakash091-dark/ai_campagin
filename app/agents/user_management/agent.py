# app/agents/user_management/agent.py
#
# User management agent — create users by role, assign TLs,
# list/get/delete users, and manage user profile.

import json

from pydantic import ValidationError

from app.core.orchestrator.state import AgentState
from app.tools.user_management_tools import (
    create_admin,
    create_team_lead,
    create_ct_team_lead,
    create_ct_user,
    create_ctesting_team_lead,
    create_ctesting_user,
    create_user,
    assign_team_lead,
    list_workspace_users,
    list_tl_users,
    get_user,
    delete_user,
)
from app.tools.user_profile_tools import (
    get_user_profile,
    update_user_profile,
)
from app.tools.schemas import (
    CreateAdminSchema,
    CreateTLSchema,
    CreateUserSchema,
    AssignTLSchema,
    UpdateUserProfileSchema,
)
from app.services.db_context import (
    resolve_user_id_from_name,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("user-management-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
CREATE_ADMIN_KEYWORDS = ["create admin", "add admin", "new admin"]
CREATE_TL_KEYWORDS = ["create team lead", "add team lead", "new team lead", "create tl"]
CREATE_USER_KEYWORDS = ["create user", "add user", "new user", "invite user"]
ASSIGN_TL_KEYWORDS = ["assign team lead", "assign tl", "set team lead"]
LIST_USERS_KEYWORDS = ["list users", "show users", "all users", "workspace users"]
DELETE_USER_KEYWORDS = ["delete user", "remove user"]
PROFILE_KEYWORDS = ["my profile", "user profile", "update profile", "edit profile"]


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
# USER MANAGEMENT AGENT
# =========================================================
async def run_user_management_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}
        db_ctx = state.get("db_context") or {}

        logger.info("Running user management agent", workspace_id=workspace_id)

        # ─────────────────────────────────────────────────────
        # AUTO-RESOLVE IDs FROM DB CONTEXT
        # ─────────────────────────────────────────────────────

        # Resolve tl_id from team lead name
        if extra.get("tl_name") and not extra.get("tl_id"):
            resolved = resolve_user_id_from_name(db_ctx, str(extra["tl_name"]))
            if resolved:
                extra = {**extra, "tl_id": resolved}

        # Resolve user_id from user name for assign/delete operations
        if extra.get("user_name") and not extra.get("user_id"):
            resolved = resolve_user_id_from_name(db_ctx, str(extra["user_name"]))
            if resolved:
                extra = {**extra, "user_id": resolved}

        tool_result = {}
        action_taken = "none"

        # =====================================================
        # CREATE ADMIN
        # =====================================================
        if any(kw in message_lower for kw in CREATE_ADMIN_KEYWORDS):

            try:
                schema = CreateAdminSchema(**{**extra, "workspace_id": workspace_id})
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateAdminSchema",
                    [
                        "email — Admin email address",
                        "name — Full name",
                        "number — Phone number",
                        "password — Password (min 8 chars)",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await create_admin(payload=schema.model_dump())
            action_taken = "create_admin"

        # =====================================================
        # CREATE TEAM LEAD
        # =====================================================
        elif any(kw in message_lower for kw in CREATE_TL_KEYWORDS):

            try:
                schema = CreateTLSchema(**{**extra, "workspace_id": workspace_id})
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateTLSchema",
                    [
                        "email — Team Lead email address",
                        "name — Full name",
                        "number — Phone number",
                        "password — Password (min 8 chars)",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await create_team_lead(payload=schema.model_dump())
            action_taken = "create_team_lead"

        # =====================================================
        # CREATE USER
        # =====================================================
        elif any(kw in message_lower for kw in CREATE_USER_KEYWORDS):

            try:
                schema = CreateUserSchema(**{**extra, "workspace_id": workspace_id})
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateUserSchema",
                    [
                        "email — User email address",
                        "name — Full name",
                        "number — Phone number",
                        "password — Password (min 8 chars)",
                        "tl_id — Team Lead user ID (optional)",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await create_user(payload=schema.model_dump(exclude_none=True))
            action_taken = "create_user"

        # =====================================================
        # ASSIGN TEAM LEAD
        # =====================================================
        elif any(kw in message_lower for kw in ASSIGN_TL_KEYWORDS):

            try:
                schema = AssignTLSchema(**{**extra, "workspace_id": workspace_id})
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "AssignTLSchema",
                    [
                        "user_id — User ID to assign TL to",
                        "tl_id — Team Lead user ID",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await assign_team_lead(
                workspace_id=schema.workspace_id,
                user_id=schema.user_id,
                tl_id=schema.tl_id,
            )
            action_taken = "assign_team_lead"

        # =====================================================
        # DELETE USER
        # =====================================================
        elif any(kw in message_lower for kw in DELETE_USER_KEYWORDS):

            user_id = extra.get("user_id")
            if not user_id:
                state["ui_json"] = _missing_fields_response(
                    "DeleteUser", ["user_id — User ID to delete"]
                )
                state["success"] = True
                return state

            tool_result = await delete_user(user_id=int(user_id))
            action_taken = "delete_user"

        # =====================================================
        # USER PROFILE
        # =====================================================
        elif any(kw in message_lower for kw in PROFILE_KEYWORDS):

            if "update" in message_lower or "edit" in message_lower or "change" in message_lower:
                try:
                    schema = UpdateUserProfileSchema(**extra)
                except ValidationError as e:
                    state["ui_json"] = _validation_error_response(e)
                    state["success"] = True
                    return state

                tool_result = await update_user_profile(
                    payload=schema.model_dump(exclude_none=True)
                )
                action_taken = "update_user_profile"
            else:
                tool_result = await get_user_profile()
                action_taken = "get_user_profile"

        # =====================================================
        # LIST USERS (default)
        # =====================================================
        else:

            tool_result = await list_workspace_users(
                workspace_id=workspace_id,
                role=extra.get("role"),
                only_active=extra.get("only_active", True),
            )
            action_taken = "list_workspace_users"

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

        logger.error("User management agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "User Management Error",
            "message": str(e),
        })

        return state
