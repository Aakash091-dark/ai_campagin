# app/agents/tasks/agent.py
#
# Task management agent — categories, tags, tasks CRUD,
# status updates, comments, and activity.

import json

from pydantic import ValidationError

from app.core.orchestrator.state import AgentState
from app.tools.task_tools import (
    create_task_category,
    list_task_categories,
    delete_task_category,
    create_task_tag,
    list_task_tags,
    delete_task_tag,
    create_task,
    list_tasks,
    get_task_stats,
    get_task,
    update_task,
    delete_task,
    update_task_status,
    toggle_task_repeat,
    add_task_comment,
    list_task_comments,
    get_task_activity,
)
from app.tools.schemas import (
    CreateTaskSchema,
    UpdateTaskSchema,
    UpdateTaskStatusSchema,
    AddTaskCommentSchema,
    CreateTaskCategorySchema,
    CreateTaskTagSchema,
)
from app.services.db_context import (
    resolve_user_id_from_name,
    resolve_task_id_from_title,
    resolve_task_category_id_from_name,
    resolve_task_tag_id_from_name,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("tasks-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
CREATE_TASK_KEYWORDS = ["create task", "new task", "add task", "assign task"]
UPDATE_TASK_KEYWORDS = ["update task", "edit task", "modify task", "change task"]
DELETE_TASK_KEYWORDS = ["delete task", "remove task"]
STATUS_KEYWORDS = ["complete task", "mark task", "task status", "finish task", "close task"]
COMMENT_KEYWORDS = ["comment on task", "add comment", "task comment"]
ACTIVITY_KEYWORDS = ["task activity", "task history", "task log"]
STATS_KEYWORDS = ["task stats", "task statistics", "task summary"]
CATEGORY_KEYWORDS = ["task category", "categories", "task categories"]
TAG_KEYWORDS = ["task tag", "task tags"]
LIST_KEYWORDS = ["list tasks", "show tasks", "my tasks", "all tasks", "pending tasks"]


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
# TASKS AGENT
# =========================================================
async def run_tasks_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}
        db_ctx = state.get("db_context") or {}

        logger.info("Running tasks agent", workspace_id=workspace_id)

        # ─────────────────────────────────────────────────────
        # AUTO-RESOLVE IDs FROM DB CONTEXT
        # If the user/frontend passed names instead of IDs,
        # resolve them from the pre-loaded db_context.
        # ─────────────────────────────────────────────────────

        # Resolve task_id from title if a string title was given
        if extra.get("task_title") and not extra.get("task_id"):
            resolved = resolve_task_id_from_title(db_ctx, str(extra["task_title"]))
            if resolved:
                extra = {**extra, "task_id": resolved}

        # Resolve category_id from name
        if extra.get("category_name") and not extra.get("category_id"):
            resolved = resolve_task_category_id_from_name(db_ctx, str(extra["category_name"]))
            if resolved:
                extra = {**extra, "category_id": resolved}

        # Resolve tag_ids from names (list of names → list of IDs)
        if extra.get("tag_names") and not extra.get("tag_ids"):
            tag_names = extra["tag_names"]
            if isinstance(tag_names, list):
                resolved_ids = [
                    resolve_task_tag_id_from_name(db_ctx, name)
                    for name in tag_names
                ]
                resolved_ids = [i for i in resolved_ids if i is not None]
                if resolved_ids:
                    extra = {**extra, "tag_ids": resolved_ids}

        # Resolve assigned_to user IDs from names
        if extra.get("assigned_to_names") and not extra.get("assigned_to"):
            names = extra["assigned_to_names"]
            if isinstance(names, list):
                resolved_ids = [
                    resolve_user_id_from_name(db_ctx, name)
                    for name in names
                ]
                resolved_ids = [i for i in resolved_ids if i is not None]
                if resolved_ids:
                    extra = {**extra, "assigned_to": resolved_ids}

        # Resolve category_id from delete by name
        if extra.get("category_name") and not extra.get("category_id"):
            resolved = resolve_task_category_id_from_name(db_ctx, str(extra["category_name"]))
            if resolved:
                extra = {**extra, "category_id": resolved}

        tool_result = {}
        action_taken = "none"

        # =====================================================
        # TASK CATEGORIES
        # =====================================================
        if any(kw in message_lower for kw in CATEGORY_KEYWORDS):

            if "create" in message_lower or "add" in message_lower:
                name = extra.get("name")
                if not name:
                    state["ui_json"] = _missing_fields_response(
                        "CreateTaskCategorySchema", ["name — Category name"]
                    )
                    state["success"] = True
                    return state
                tool_result = await create_task_category(workspace_id, name)
                action_taken = "create_task_category"

            elif "delete" in message_lower or "remove" in message_lower:
                category_id = extra.get("category_id")
                if not category_id:
                    state["ui_json"] = _missing_fields_response(
                        "DeleteTaskCategory", ["category_id — Category ID to delete"]
                    )
                    state["success"] = True
                    return state
                tool_result = await delete_task_category(workspace_id, int(category_id))
                action_taken = "delete_task_category"

            else:
                tool_result = await list_task_categories(workspace_id)
                action_taken = "list_task_categories"

        # =====================================================
        # TASK TAGS
        # =====================================================
        elif any(kw in message_lower for kw in TAG_KEYWORDS):

            if "create" in message_lower or "add" in message_lower:
                name = extra.get("name")
                if not name:
                    state["ui_json"] = _missing_fields_response(
                        "CreateTaskTagSchema", ["name — Tag name"]
                    )
                    state["success"] = True
                    return state
                tool_result = await create_task_tag(workspace_id, name)
                action_taken = "create_task_tag"

            elif "delete" in message_lower or "remove" in message_lower:
                tag_id = extra.get("tag_id")
                if not tag_id:
                    state["ui_json"] = _missing_fields_response(
                        "DeleteTaskTag", ["tag_id — Tag ID to delete"]
                    )
                    state["success"] = True
                    return state
                tool_result = await delete_task_tag(workspace_id, int(tag_id))
                action_taken = "delete_task_tag"

            else:
                tool_result = await list_task_tags(workspace_id)
                action_taken = "list_task_tags"

        # =====================================================
        # CREATE TASK
        # =====================================================
        elif any(kw in message_lower for kw in CREATE_TASK_KEYWORDS):

            try:
                schema = CreateTaskSchema(**extra)
            except ValidationError as e:
                missing = [err["loc"][0] for err in e.errors()]
                state["ui_json"] = _missing_fields_response(
                    "CreateTaskSchema",
                    [
                        "title — Task title",
                        "priority — low | medium | high",
                        "description — Task description (optional)",
                        "assigned_to — List of user IDs (optional)",
                        "due_at — Due datetime ISO 8601 (optional)",
                        "tag_ids — List of tag IDs (optional)",
                        "category_id — Category ID (optional)",
                    ] if not extra else [f"{f}" for f in missing],
                )
                state["success"] = True
                return state

            tool_result = await create_task(
                workspace_id=workspace_id,
                payload=schema.model_dump(exclude_none=True),
            )
            action_taken = "create_task"

        # =====================================================
        # UPDATE TASK
        # =====================================================
        elif any(kw in message_lower for kw in UPDATE_TASK_KEYWORDS):

            task_id = extra.get("task_id")
            if not task_id:
                state["ui_json"] = _missing_fields_response(
                    "UpdateTaskSchema", ["task_id — Task ID to update"]
                )
                state["success"] = True
                return state

            try:
                schema = UpdateTaskSchema(**{k: v for k, v in extra.items() if k != "task_id"})
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await update_task(
                workspace_id=workspace_id,
                task_id=int(task_id),
                payload=schema.model_dump(exclude_none=True),
            )
            action_taken = "update_task"

        # =====================================================
        # DELETE TASK
        # =====================================================
        elif any(kw in message_lower for kw in DELETE_TASK_KEYWORDS):

            task_id = extra.get("task_id")
            if not task_id:
                state["ui_json"] = _missing_fields_response(
                    "DeleteTask", ["task_id — Task ID to delete"]
                )
                state["success"] = True
                return state

            tool_result = await delete_task(workspace_id=workspace_id, task_id=int(task_id))
            action_taken = "delete_task"

        # =====================================================
        # UPDATE TASK STATUS
        # =====================================================
        elif any(kw in message_lower for kw in STATUS_KEYWORDS):

            task_id = extra.get("task_id")
            status = extra.get("status")

            if not task_id or not status:
                state["ui_json"] = _missing_fields_response(
                    "UpdateTaskStatusSchema",
                    [
                        "task_id — Task ID",
                        "status — pending | in_progress | completed | cancelled",
                    ],
                )
                state["success"] = True
                return state

            try:
                schema = UpdateTaskStatusSchema(status=status)
            except ValidationError as e:
                state["ui_json"] = _validation_error_response(e)
                state["success"] = True
                return state

            tool_result = await update_task_status(
                workspace_id=workspace_id,
                task_id=int(task_id),
                status=schema.status,
            )
            action_taken = "update_task_status"

        # =====================================================
        # ADD COMMENT
        # =====================================================
        elif any(kw in message_lower for kw in COMMENT_KEYWORDS):

            task_id = extra.get("task_id")
            content = extra.get("content")

            if not task_id or not content:
                state["ui_json"] = _missing_fields_response(
                    "AddTaskCommentSchema",
                    ["task_id — Task ID", "content — Comment text"],
                )
                state["success"] = True
                return state

            tool_result = await add_task_comment(
                workspace_id=workspace_id,
                task_id=int(task_id),
                content=content,
            )
            action_taken = "add_task_comment"

        # =====================================================
        # TASK ACTIVITY
        # =====================================================
        elif any(kw in message_lower for kw in ACTIVITY_KEYWORDS):

            task_id = extra.get("task_id")
            if not task_id:
                state["ui_json"] = _missing_fields_response(
                    "TaskActivity", ["task_id — Task ID"]
                )
                state["success"] = True
                return state

            tool_result = await get_task_activity(
                workspace_id=workspace_id,
                task_id=int(task_id),
            )
            action_taken = "get_task_activity"

        # =====================================================
        # TASK STATS
        # =====================================================
        elif any(kw in message_lower for kw in STATS_KEYWORDS):

            tool_result = await get_task_stats(
                workspace_id=workspace_id,
                assigned_to=extra.get("assigned_to"),
                status=extra.get("status"),
            )
            action_taken = "get_task_stats"

        # =====================================================
        # LIST TASKS (default)
        # =====================================================
        else:

            tool_result = await list_tasks(
                workspace_id=workspace_id,
                status=extra.get("status"),
                priority=extra.get("priority"),
            )
            action_taken = "list_tasks"

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

        logger.error("Tasks agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Tasks Error",
            "message": str(e),
        })

        return state
