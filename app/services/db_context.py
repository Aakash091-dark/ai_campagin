# app/services/db_context.py
#
# Database context resolver.
# Queries the shared PostgreSQL database to resolve all IDs
# the user doesn't know (workspace accounts, campaigns, users,
# tasks, automation rules, smart alerts, etc.) so agents never
# have to ask the user for internal database IDs.
#
# Tables used (from schema.sql):
#   workspace, account, user, user_account_assignment,
#   task, task_category, task_tag,
#   automation.automation_rule,
#   smart_alert.rule,
#   user_goals, reporting_config, tracker

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger

logger = get_logger("db-context")


# =========================================================
# WORKSPACE CONTEXT
# Resolves everything the AI needs for a given workspace_id
# =========================================================
async def resolve_workspace_context(
    db: AsyncSession,
    workspace_id: int,
    user_id: int | None = None,
) -> dict[str, Any]:
    """
    Returns a rich context dict that agents attach to AgentState.
    All IDs are resolved here so agents never ask the user for them.
    """

    ctx: dict[str, Any] = {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "accounts": [],
        "users": [],
        "my_accounts": [],
        "tasks": [],
        "task_categories": [],
        "task_tags": [],
        "automation_rules": [],
        "smart_alert_rules": [],
        "trackers": [],
        "goals": [],
        "reporting_config": None,
    }

    try:
        # ─────────────────────────────────────────────
        # AD ACCOUNTS for this workspace
        # ─────────────────────────────────────────────
        rows = await db.execute(
            text("""
                SELECT id, account_id, name, platform, active, currency, timezone
                FROM account
                WHERE workspace_id = :wid AND active = TRUE
                ORDER BY name
            """),
            {"wid": workspace_id},
        )
        ctx["accounts"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # ACCOUNTS ASSIGNED TO THIS USER
        # ─────────────────────────────────────────────
        if user_id:
            rows = await db.execute(
                text("""
                    SELECT a.id, a.account_id, a.name, a.platform,
                           a.currency, a.timezone
                    FROM account a
                    JOIN user_account_assignment uaa ON uaa.account_id = a.id
                    WHERE a.workspace_id = :wid
                      AND uaa.user_id    = :uid
                      AND uaa.is_out     = FALSE
                      AND uaa.end_at IS NULL
                      AND a.active = TRUE
                    ORDER BY a.name
                """),
                {"wid": workspace_id, "uid": user_id},
            )
            ctx["my_accounts"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # WORKSPACE USERS
        # ─────────────────────────────────────────────
        rows = await db.execute(
            text("""
                SELECT id, name, email, role, media_buyer_code, is_active
                FROM "user"
                WHERE workspace_id = :wid AND is_active = TRUE
                ORDER BY name
            """),
            {"wid": workspace_id},
        )
        ctx["users"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # TASKS (recent 50, open only)
        # ─────────────────────────────────────────────
        rows = await db.execute(
            text("""
                SELECT id, title, status, priority, assigned_to,
                       due_at, category_id, created_at
                FROM task
                WHERE workspace_id = :wid
                  AND status NOT IN ('completed', 'cancelled')
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {"wid": workspace_id},
        )
        ctx["tasks"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # TASK CATEGORIES
        # ─────────────────────────────────────────────
        rows = await db.execute(
            text("""
                SELECT id, name FROM task_category
                WHERE workspace_id = :wid ORDER BY name
            """),
            {"wid": workspace_id},
        )
        ctx["task_categories"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # TASK TAGS
        # ─────────────────────────────────────────────
        rows = await db.execute(
            text("""
                SELECT id, name FROM task_tag
                WHERE workspace_id = :wid ORDER BY name
            """),
            {"wid": workspace_id},
        )
        ctx["task_tags"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # AUTOMATION RULES
        # ─────────────────────────────────────────────
        rows = await db.execute(
            text("""
                SELECT id, name, action_type, platform,
                       entity_level, is_active, trigger_type
                FROM automation.automation_rule
                WHERE workspace_id = :wid
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {"wid": workspace_id},
        )
        ctx["automation_rules"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # SMART ALERT RULES
        # ─────────────────────────────────────────────
        rows = await db.execute(
            text("""
                SELECT id, name, scope, platform_tags,
                       is_active, notify_in_app, notify_email
                FROM smart_alert.rule
                WHERE workspace_id = :wid
                ORDER BY created_at DESC
                LIMIT 50
            """),
            {"wid": workspace_id},
        )
        ctx["smart_alert_rules"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # TRACKERS
        # ─────────────────────────────────────────────
        rows = await db.execute(
            text("""
                SELECT id, name, tracker_name, platform, is_active
                FROM tracker
                WHERE workspace_id = :wid AND is_active = TRUE
                ORDER BY name
            """),
            {"wid": workspace_id},
        )
        ctx["trackers"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # GOALS (current user, current year)
        # ─────────────────────────────────────────────
        if user_id:
            rows = await db.execute(
                text("""
                    SELECT id, target_period, target_profit
                    FROM user_goals
                    WHERE workspace_id = :wid
                      AND user_id = :uid
                    ORDER BY target_period DESC
                    LIMIT 12
                """),
                {"wid": workspace_id, "uid": user_id},
            )
            ctx["goals"] = [dict(r._mapping) for r in rows]

        # ─────────────────────────────────────────────
        # REPORTING CONFIG
        # ─────────────────────────────────────────────
        row = await db.execute(
            text("""
                SELECT id, slots_config, buffer_before_min,
                       buffer_after_min, is_active
                FROM reporting_config
                WHERE workspace_id = :wid
                LIMIT 1
            """),
            {"wid": workspace_id},
        )
        r = row.fetchone()
        if r:
            ctx["reporting_config"] = dict(r._mapping)

        logger.info(
            "DB context resolved",
            workspace_id=workspace_id,
            accounts=len(ctx["accounts"]),
            users=len(ctx["users"]),
            tasks=len(ctx["tasks"]),
            automation_rules=len(ctx["automation_rules"]),
            smart_alerts=len(ctx["smart_alert_rules"]),
        )

    except Exception as e:
        logger.error("DB context resolution failed", error=str(e))
        # Rollback so the session is not left in InFailedSQLTransactionError
        # state — subsequent queries in the same request would all fail otherwise.
        try:
            await db.rollback()
        except Exception:
            pass
        # Return partial context — agents degrade gracefully

    return ctx


# =========================================================
# LOOKUP HELPERS
# Used by agents to resolve a name → id without re-querying
# =========================================================

def find_account_by_name_or_id(
    ctx: dict,
    query: str,
) -> dict | None:
    """Find an account by partial name or exact account_id string."""
    q = query.lower().strip()
    for acc in ctx.get("accounts", []):
        if q == str(acc.get("account_id", "")).lower():
            return acc
        if q in str(acc.get("name", "")).lower():
            return acc
    return None


def find_user_by_name_or_email(
    ctx: dict,
    query: str,
) -> dict | None:
    """Find a workspace user by partial name or email."""
    q = query.lower().strip()
    for u in ctx.get("users", []):
        if q in str(u.get("name", "")).lower():
            return u
        if q == str(u.get("email", "")).lower():
            return u
    return None


def find_task_by_title(
    ctx: dict,
    query: str,
) -> dict | None:
    """Find a task by partial title match."""
    q = query.lower().strip()
    for t in ctx.get("tasks", []):
        if q in str(t.get("title", "")).lower():
            return t
    return None


def find_automation_rule_by_name(
    ctx: dict,
    query: str,
) -> dict | None:
    """Find an automation rule by partial name."""
    q = query.lower().strip()
    for r in ctx.get("automation_rules", []):
        if q in str(r.get("name", "")).lower():
            return r
    return None


def find_smart_alert_by_name(
    ctx: dict,
    query: str,
) -> dict | None:
    """Find a smart alert rule by partial name."""
    q = query.lower().strip()
    for r in ctx.get("smart_alert_rules", []):
        if q in str(r.get("name", "")).lower():
            return r
    return None


def find_task_category_by_name(
    ctx: dict,
    query: str,
) -> dict | None:
    q = query.lower().strip()
    for c in ctx.get("task_categories", []):
        if q in str(c.get("name", "")).lower():
            return c
    return None


def find_task_tag_by_name(
    ctx: dict,
    query: str,
) -> dict | None:
    q = query.lower().strip()
    for t in ctx.get("task_tags", []):
        if q in str(t.get("name", "")).lower():
            return t
    return None


def get_account_ids_for_platform(
    ctx: dict,
    platform: str,
) -> list[str]:
    """Return all platform account_id strings for a given platform."""
    return [
        str(a["account_id"])
        for a in ctx.get("accounts", [])
        if a.get("platform", "").lower() == platform.lower()
    ]


def get_my_account_ids_for_platform(
    ctx: dict,
    platform: str,
) -> list[str]:
    """Return account_id strings assigned to the current user for a platform."""
    return [
        str(a["account_id"])
        for a in ctx.get("my_accounts", [])
        if a.get("platform", "").lower() == platform.lower()
    ]


def resolve_user_id_from_name(
    ctx: dict,
    query: str,
) -> int | None:
    """
    Resolve a user's database ID from a partial name or email.
    Returns the integer id or None if not found.
    """
    u = find_user_by_name_or_email(ctx, query)
    return int(u["id"]) if u else None


def resolve_account_db_id_from_name(
    ctx: dict,
    query: str,
) -> int | None:
    """
    Resolve an account's database id (account.id) from a partial name
    or platform account_id string.
    Returns the integer id or None if not found.
    """
    a = find_account_by_name_or_id(ctx, query)
    return int(a["id"]) if a else None


def resolve_task_id_from_title(
    ctx: dict,
    query: str,
) -> int | None:
    """Resolve a task's database ID from a partial title match."""
    t = find_task_by_title(ctx, query)
    return int(t["id"]) if t else None


def resolve_automation_rule_id_from_name(
    ctx: dict,
    query: str,
) -> int | None:
    """Resolve an automation rule's database ID from a partial name."""
    r = find_automation_rule_by_name(ctx, query)
    return int(r["id"]) if r else None


def resolve_smart_alert_id_from_name(
    ctx: dict,
    query: str,
) -> int | None:
    """Resolve a smart alert rule's database ID from a partial name."""
    r = find_smart_alert_by_name(ctx, query)
    return int(r["id"]) if r else None


def resolve_task_category_id_from_name(
    ctx: dict,
    query: str,
) -> int | None:
    """Resolve a task category's database ID from a partial name."""
    c = find_task_category_by_name(ctx, query)
    return int(c["id"]) if c else None


def resolve_task_tag_id_from_name(
    ctx: dict,
    query: str,
) -> int | None:
    """Resolve a task tag's database ID from a partial name."""
    t = find_task_tag_by_name(ctx, query)
    return int(t["id"]) if t else None


def summarise_context(ctx: dict) -> str:
    """
    Returns a compact text summary of the resolved context.
    Injected into the LLM system prompt so the AI knows what
    accounts, users, tasks etc. exist without the user having
    to mention IDs.
    """
    lines: list[str] = []

    accounts = ctx.get("accounts", [])
    if accounts:
        lines.append("## Connected Ad Accounts")
        for a in accounts:
            lines.append(
                f"  - [{a['platform'].upper()}] {a['name']} "
                f"(account_id={a['account_id']}, db_id={a['id']})"
            )

    my_accounts = ctx.get("my_accounts", [])
    if my_accounts:
        lines.append("## Your Assigned Accounts")
        for a in my_accounts:
            lines.append(
                f"  - [{a['platform'].upper()}] {a['name']} "
                f"(account_id={a['account_id']})"
            )

    users = ctx.get("users", [])
    if users:
        lines.append("## Workspace Users")
        for u in users:
            lines.append(
                f"  - {u['name']} <{u['email']}> role={u['role']} id={u['id']}"
            )

    tasks = ctx.get("tasks", [])
    if tasks:
        lines.append("## Open Tasks (recent 50)")
        for t in tasks:
            lines.append(
                f"  - [{t['priority'].upper()}] {t['title']} "
                f"status={t['status']} id={t['id']}"
            )

    rules = ctx.get("automation_rules", [])
    if rules:
        lines.append("## Automation Rules")
        for r in rules:
            active = "active" if r["is_active"] else "inactive"
            lines.append(
                f"  - {r['name']} ({r['platform']}, {r['action_type']}, "
                f"{active}) id={r['id']}"
            )

    alerts = ctx.get("smart_alert_rules", [])
    if alerts:
        lines.append("## Smart Alert Rules")
        for a in alerts:
            active = "active" if a["is_active"] else "inactive"
            lines.append(
                f"  - {a['name']} ({active}) id={a['id']}"
            )

    cats = ctx.get("task_categories", [])
    if cats:
        lines.append("## Task Categories")
        lines.append("  " + ", ".join(f"{c['name']}(id={c['id']})" for c in cats))

    tags = ctx.get("task_tags", [])
    if tags:
        lines.append("## Task Tags")
        lines.append("  " + ", ".join(f"{t['name']}(id={t['id']})" for t in tags))

    goals = ctx.get("goals", [])
    if goals:
        lines.append("## Your Goals")
        for g in goals:
            lines.append(
                f"  - {g['target_period']}: target_profit={g['target_profit']} id={g['id']}"
            )

    rc = ctx.get("reporting_config")
    if rc:
        lines.append(f"## Reporting Config (id={rc['id']})")
        lines.append(f"  slots={rc['slots_config']}, active={rc['is_active']}")

    return "\n".join(lines) if lines else "No context data available."
