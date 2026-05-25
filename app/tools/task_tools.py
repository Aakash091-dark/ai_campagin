# app/tools/task_tools.py
#
# Task management tools — api_doc/task_manag_api.txt

from app.services.backend.client import backend_client
from app.config.logging import get_logger

logger = get_logger("task-tools")


# =========================================================
# TASK CATEGORIES
# =========================================================

async def create_task_category(workspace_id: int, name: str):
    logger.info("Creating task category", workspace_id=workspace_id, name=name)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/categories",
        data={"name": name},
    )


async def list_task_categories(workspace_id: int):
    logger.info("Listing task categories", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/categories"
    )


async def delete_task_category(workspace_id: int, category_id: int):
    logger.info("Deleting task category", category_id=category_id)
    return await backend_client.delete(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/categories/{category_id}"
    )


# =========================================================
# TASK TAGS
# =========================================================

async def create_task_tag(workspace_id: int, name: str):
    logger.info("Creating task tag", workspace_id=workspace_id, name=name)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/tags",
        data={"name": name},
    )


async def list_task_tags(workspace_id: int):
    logger.info("Listing task tags", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/tags"
    )


async def delete_task_tag(workspace_id: int, tag_id: int):
    logger.info("Deleting task tag", tag_id=tag_id)
    return await backend_client.delete(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/tags/{tag_id}"
    )


# =========================================================
# TASKS CRUD
# =========================================================

async def create_task(workspace_id: int, payload: dict):
    logger.info("Creating task", workspace_id=workspace_id, title=payload.get("title"))
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks",
        data=payload,
    )


async def list_tasks(
    workspace_id: int,
    status: str | None = None,
    priority: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    params: dict = {"page": page, "page_size": page_size}
    if status:
        params["status"] = status
    if priority:
        params["priority"] = priority
    logger.info("Listing tasks", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks",
        params=params,
    )


async def get_task_stats(
    workspace_id: int,
    assigned_to: int | None = None,
    status: str | None = None,
):
    params: dict = {}
    if assigned_to:
        params["assigned_to"] = assigned_to
    if status:
        params["status"] = status
    logger.info("Getting task stats", workspace_id=workspace_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/stats",
        params=params or None,
    )


async def get_task(workspace_id: int, task_id: int):
    logger.info("Getting task", task_id=task_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/{task_id}"
    )


async def update_task(workspace_id: int, task_id: int, payload: dict):
    logger.info("Updating task", task_id=task_id)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/{task_id}",
        data=payload,
    )


async def delete_task(workspace_id: int, task_id: int):
    logger.info("Deleting task", task_id=task_id)
    return await backend_client.delete(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/{task_id}"
    )


async def update_task_status(workspace_id: int, task_id: int, status: str):
    logger.info("Updating task status", task_id=task_id, status=status)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/{task_id}/status",
        data={"status": status},
    )


async def toggle_task_repeat(workspace_id: int, task_id: int):
    logger.info("Toggling task repeat", task_id=task_id)
    return await backend_client.patch(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/{task_id}/repeat-toggle"
    )


# =========================================================
# TASK COMMENTS
# =========================================================

async def add_task_comment(workspace_id: int, task_id: int, content: str):
    logger.info("Adding task comment", task_id=task_id)
    return await backend_client.post(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/{task_id}/comments",
        data={"content": content},
    )


async def list_task_comments(workspace_id: int, task_id: int):
    logger.info("Listing task comments", task_id=task_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/{task_id}/comments"
    )


async def get_task_activity(workspace_id: int, task_id: int, limit: int = 50):
    logger.info("Getting task activity", task_id=task_id)
    return await backend_client.get(
        endpoint=f"/api/v1/workspaces/{workspace_id}/tasks/{task_id}/activity",
        params={"limit": limit},
    )
