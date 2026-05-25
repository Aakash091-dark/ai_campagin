# app/tools/registry.py
#
# Central tool registry.
# Every callable tool is registered here with its metadata so that:
#   - Agents can look up tools by name without hard-coded imports
#   - Observability layer can log which tool ran, its args, and its result
#   - Future LLM function-calling can enumerate available tools automatically
#
# Usage:
#   from app.tools.registry import tool_registry
#   result = await tool_registry.call("get_live_campaign_insights", workspace_id=1)

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from app.config.logging import get_logger

logger = get_logger("tool-registry")


# =========================================================
# TOOL DESCRIPTOR
# =========================================================
@dataclass
class ToolDescriptor:
    name: str
    fn: Callable[..., Awaitable[Any]]
    description: str
    agent: str          # which agent owns this tool
    tags: list[str] = field(default_factory=list)


# =========================================================
# REGISTRY
# =========================================================
class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDescriptor] = {}

    # ── registration ──────────────────────────────────────────────
    def register(
        self,
        name: str,
        fn: Callable,
        description: str,
        agent: str,
        tags: list[str] | None = None,
    ) -> None:
        if name in self._tools:
            logger.warning("Tool already registered — overwriting", tool=name)
        self._tools[name] = ToolDescriptor(
            name=name,
            fn=fn,
            description=description,
            agent=agent,
            tags=tags or [],
        )

    # ── lookup ────────────────────────────────────────────────────
    def get(self, name: str) -> ToolDescriptor | None:
        return self._tools.get(name)

    def list_tools(self, agent: str | None = None) -> list[ToolDescriptor]:
        tools = list(self._tools.values())
        if agent:
            tools = [t for t in tools if t.agent == agent]
        return tools

    def names(self) -> list[str]:
        return list(self._tools.keys())

    # ── execution with observability ──────────────────────────────
    async def call(self, name: str, **kwargs: Any) -> Any:
        descriptor = self._tools.get(name)
        if descriptor is None:
            raise KeyError(f"Tool '{name}' not found in registry")

        start = time.perf_counter()
        logger.info("Tool call start", tool=name, agent=descriptor.agent, kwargs=list(kwargs.keys()))

        try:
            result = await descriptor.fn(**kwargs)
            elapsed = round((time.perf_counter() - start) * 1000, 1)
            logger.info("Tool call success", tool=name, elapsed_ms=elapsed)
            return result
        except Exception as exc:
            elapsed = round((time.perf_counter() - start) * 1000, 1)
            logger.error("Tool call failed", tool=name, elapsed_ms=elapsed, error=str(exc))
            raise


# ── singleton ─────────────────────────────────────────────────────
tool_registry = ToolRegistry()


# =========================================================
# REGISTER ALL TOOLS
# Called once at startup from main.py lifespan.
# =========================================================
def register_all_tools() -> None:
    """Import and register every tool function."""

    # ── analytics ─────────────────────────────────────────────────
    from app.tools.analytics_tools import (
        get_live_campaign_insights,
        get_historical_campaign_insights,
        get_cross_platform_historical_insights,
        get_historical_breakdown,
        get_historical_insights_by_user,
        get_team_members_analytics,
        create_analytics_export,
        list_analytics_exports,
        get_export_status,
        get_dynamic_matrix,
        get_creatives_cards,
        get_creatives_graph,
        get_historical_offers,
        get_vertical_offers_all_platforms,
        get_connected_ad_accounts,
    )

    _r = tool_registry.register
    _r("get_live_campaign_insights",            get_live_campaign_insights,            "Live campaign performance",                    "analytics", ["read", "analytics"])
    _r("get_historical_campaign_insights",      get_historical_campaign_insights,      "Historical campaign insights by platform",      "analytics", ["read", "analytics"])
    _r("get_cross_platform_historical_insights",get_cross_platform_historical_insights,"Cross-platform historical insights",            "analytics", ["read", "analytics"])
    _r("get_historical_breakdown",              get_historical_breakdown,              "Hourly/daily breakdown of campaign metrics",    "analytics", ["read", "analytics"])
    _r("get_historical_insights_by_user",       get_historical_insights_by_user,       "Historical insights filtered by user",          "analytics", ["read", "analytics"])
    _r("get_team_members_analytics",            get_team_members_analytics,            "Team member performance analytics",             "analytics", ["read", "analytics"])
    _r("create_analytics_export",               create_analytics_export,               "Create an analytics report export job",         "analytics", ["write", "analytics"])
    _r("list_analytics_exports",                list_analytics_exports,                "List analytics export jobs",                    "analytics", ["read", "analytics"])
    _r("get_export_status",                     get_export_status,                     "Get status of an export job",                   "analytics", ["read", "analytics"])
    _r("get_dynamic_matrix",                    get_dynamic_matrix,                    "Dynamic cross-dimension analytics matrix",      "analytics", ["read", "analytics"])
    _r("get_creatives_cards",                   get_creatives_cards,                   "Creative performance cards",                    "analytics", ["read", "analytics"])
    _r("get_creatives_graph",                   get_creatives_graph,                   "Creative performance graph",                    "analytics", ["read", "analytics"])
    _r("get_historical_offers",                 get_historical_offers,                 "Historical offer performance",                  "analytics", ["read", "analytics"])
    _r("get_vertical_offers_all_platforms",     get_vertical_offers_all_platforms,     "Vertical offers across all platforms",          "analytics", ["read", "analytics"])
    _r("get_connected_ad_accounts",             get_connected_ad_accounts,             "List connected ad accounts",                    "analytics", ["read"])

    # ── dashboard ─────────────────────────────────────────────────
    from app.tools.dashboard_tools import (
        get_dashboard_summary,
        get_dashboard_timeseries,
        get_dashboard_user_trends,
        get_dashboard_accounts_ads,
        get_dashboard_tl_users,
        get_dashboard_account_drilldown,
    )
    _r("get_dashboard_summary",         get_dashboard_summary,         "Workspace dashboard summary",              "dashboard", ["read", "dashboard"])
    _r("get_dashboard_timeseries",      get_dashboard_timeseries,      "Dashboard spend/revenue timeseries",       "dashboard", ["read", "dashboard"])
    _r("get_dashboard_user_trends",     get_dashboard_user_trends,     "Per-user performance trends",              "dashboard", ["read", "dashboard"])
    _r("get_dashboard_accounts_ads",    get_dashboard_accounts_ads,    "Accounts and ads overview",                "dashboard", ["read", "dashboard"])
    _r("get_dashboard_tl_users",        get_dashboard_tl_users,        "Team lead user performance",               "dashboard", ["read", "dashboard"])
    _r("get_dashboard_account_drilldown",get_dashboard_account_drilldown,"Account-level drilldown",                "dashboard", ["read", "dashboard"])

    # ── campaigns ─────────────────────────────────────────────────
    from app.tools.campaign_status_tools import (
        bulk_change_campaign_status,
        bulk_change_campaign_budget,
        bulk_change_adset_budget,
        bulk_change_adset_bid,
        bulk_change_adset_status,
        bulk_change_ad_status,
        bulk_delete_campaigns,
        bulk_delete_adsets,
        bulk_delete_ads,
        bulk_change_ad_material_status,
        bulk_change_google_adset_bid,
        bulk_change_google_enhanced_cpc,
    )
    _r("bulk_change_campaign_status",   bulk_change_campaign_status,   "Bulk pause/resume/delete campaigns",       "campaigns", ["write", "campaigns"])
    _r("bulk_change_campaign_budget",   bulk_change_campaign_budget,   "Bulk change campaign budgets",             "campaigns", ["write", "campaigns"])
    _r("bulk_change_adset_budget",      bulk_change_adset_budget,      "Bulk change adset budgets",                "campaigns", ["write", "campaigns"])
    _r("bulk_change_adset_bid",         bulk_change_adset_bid,         "Bulk change adset bids (Facebook)",        "campaigns", ["write", "campaigns"])
    _r("bulk_change_adset_status",      bulk_change_adset_status,      "Bulk change adset statuses",               "campaigns", ["write", "campaigns"])
    _r("bulk_change_ad_status",         bulk_change_ad_status,         "Bulk change ad statuses",                  "campaigns", ["write", "campaigns"])
    _r("bulk_delete_campaigns",         bulk_delete_campaigns,         "Bulk delete campaigns",                    "campaigns", ["write", "campaigns"])
    _r("bulk_delete_adsets",            bulk_delete_adsets,            "Bulk delete adsets",                       "campaigns", ["write", "campaigns"])
    _r("bulk_delete_ads",               bulk_delete_ads,               "Bulk delete ads",                          "campaigns", ["write", "campaigns"])
    _r("bulk_change_ad_material_status",bulk_change_ad_material_status,"Bulk change TikTok ad material status",    "campaigns", ["write", "campaigns"])
    _r("bulk_change_google_adset_bid",  bulk_change_google_adset_bid,  "Bulk change Google adset bids",            "campaigns", ["write", "campaigns"])
    _r("bulk_change_google_enhanced_cpc",bulk_change_google_enhanced_cpc,"Bulk change Google enhanced CPC",        "campaigns", ["write", "campaigns"])

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
    _r("create_campaign",           create_campaign,           "Create a new campaign",                    "campaigns", ["write", "campaigns"])
    _r("create_adset",              create_adset,              "Create a new adset",                       "campaigns", ["write", "campaigns"])
    _r("create_ad",                 create_ad,                 "Create a new ad",                          "campaigns", ["write", "campaigns"])
    _r("launch_campaign",           launch_campaign,           "Launch a full campaign (campaign+adset+ad)","campaigns", ["write", "campaigns"])
    _r("launch_campaign_batch",     launch_campaign_batch,     "Launch multiple campaigns in batch",       "campaigns", ["write", "campaigns"])
    _r("get_launch_job_status",     get_launch_job_status,     "Get status of a campaign launch job",      "campaigns", ["read", "campaigns"])
    _r("list_launch_jobs",          list_launch_jobs,          "List campaign launch jobs",                "campaigns", ["read", "campaigns"])
    _r("get_campaign_history",      get_campaign_history,      "Get campaign change history",              "campaigns", ["read", "campaigns"])
    _r("list_campaign_templates",   list_campaign_templates,   "List saved campaign templates",            "campaigns", ["read", "campaigns"])
    _r("create_campaign_template",  create_campaign_template,  "Save a campaign template",                 "campaigns", ["write", "campaigns"])
    _r("delete_campaign_template",  delete_campaign_template,  "Delete a campaign template",               "campaigns", ["write", "campaigns"])

    # ── automations ───────────────────────────────────────────────
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
    _r("create_automation_rule",    create_automation_rule,    "Create an automation rule",                "automations", ["write", "automations"])
    _r("list_automation_rules",     list_automation_rules,     "List automation rules",                    "automations", ["read", "automations"])
    _r("get_automation_rule",       get_automation_rule,       "Get a single automation rule",             "automations", ["read", "automations"])
    _r("update_automation_rule",    update_automation_rule,    "Update an automation rule",                "automations", ["write", "automations"])
    _r("delete_automation_rule",    delete_automation_rule,    "Delete an automation rule",                "automations", ["write", "automations"])
    _r("toggle_automation_rule",    toggle_automation_rule,    "Toggle automation rule on/off",            "automations", ["write", "automations"])
    _r("get_automation_rule_logs",  get_automation_rule_logs,  "Get logs for a specific automation rule",  "automations", ["read", "automations"])
    _r("list_all_automation_logs",  list_all_automation_logs,  "List all automation execution logs",       "automations", ["read", "automations"])

    # ── smart alerts ──────────────────────────────────────────────
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
    _r("create_smart_alert",        create_smart_alert,        "Create a smart alert rule",                "smart_alerts", ["write", "alerts"])
    _r("list_smart_alerts",         list_smart_alerts,         "List smart alert rules",                   "smart_alerts", ["read", "alerts"])
    _r("get_smart_alert",           get_smart_alert,           "Get a single smart alert rule",            "smart_alerts", ["read", "alerts"])
    _r("update_smart_alert",        update_smart_alert,        "Update a smart alert rule",                "smart_alerts", ["write", "alerts"])
    _r("delete_smart_alert",        delete_smart_alert,        "Delete a smart alert rule",                "smart_alerts", ["write", "alerts"])
    _r("toggle_smart_alert",        toggle_smart_alert,        "Toggle smart alert on/off",                "smart_alerts", ["write", "alerts"])
    _r("get_smart_alert_logs",      get_smart_alert_logs,      "Get logs for a specific smart alert",      "smart_alerts", ["read", "alerts"])
    _r("list_all_smart_alert_logs", list_all_smart_alert_logs, "List all smart alert trigger logs",        "smart_alerts", ["read", "alerts"])

    # ── tasks ─────────────────────────────────────────────────────
    from app.tools.task_tools import (
        create_task_category, list_task_categories, delete_task_category,
        create_task_tag, list_task_tags, delete_task_tag,
        create_task, list_tasks, get_task_stats, get_task,
        update_task, delete_task, update_task_status,
        add_task_comment, list_task_comments, get_task_activity,
    )
    _r("create_task_category",  create_task_category,  "Create a task category",   "tasks", ["write", "tasks"])
    _r("list_task_categories",  list_task_categories,  "List task categories",     "tasks", ["read",  "tasks"])
    _r("delete_task_category",  delete_task_category,  "Delete a task category",   "tasks", ["write", "tasks"])
    _r("create_task_tag",       create_task_tag,       "Create a task tag",        "tasks", ["write", "tasks"])
    _r("list_task_tags",        list_task_tags,        "List task tags",           "tasks", ["read",  "tasks"])
    _r("delete_task_tag",       delete_task_tag,       "Delete a task tag",        "tasks", ["write", "tasks"])
    _r("create_task",           create_task,           "Create a task",            "tasks", ["write", "tasks"])
    _r("list_tasks",            list_tasks,            "List tasks",               "tasks", ["read",  "tasks"])
    _r("get_task_stats",        get_task_stats,        "Get task statistics",      "tasks", ["read",  "tasks"])
    _r("get_task",              get_task,              "Get a single task",        "tasks", ["read",  "tasks"])
    _r("update_task",           update_task,           "Update a task",            "tasks", ["write", "tasks"])
    _r("delete_task",           delete_task,           "Delete a task",            "tasks", ["write", "tasks"])
    _r("update_task_status",    update_task_status,    "Update task status",       "tasks", ["write", "tasks"])
    _r("add_task_comment",      add_task_comment,      "Add a comment to a task",  "tasks", ["write", "tasks"])
    _r("list_task_comments",    list_task_comments,    "List task comments",       "tasks", ["read",  "tasks"])
    _r("get_task_activity",     get_task_activity,     "Get task activity log",    "tasks", ["read",  "tasks"])

    # ── reporting ─────────────────────────────────────────────────
    from app.tools.reporting_tools import (
        generate_workspace_report,
        get_analytics_reporting,
        set_reporting_config,
        get_reporting_slots,
        submit_report,
        submit_zero_report,
    )
    _r("generate_workspace_report", generate_workspace_report, "Generate workspace summary report",    "reporting", ["read",  "reporting"])
    _r("get_analytics_reporting",   get_analytics_reporting,   "Get analytics reporting data",         "reporting", ["read",  "reporting"])
    _r("set_reporting_config",      set_reporting_config,      "Configure reporting slots",            "reporting", ["write", "reporting"])
    _r("get_reporting_slots",       get_reporting_slots,       "Get reporting time slots",             "reporting", ["read",  "reporting"])
    _r("submit_report",             submit_report,             "Submit a slot report",                 "reporting", ["write", "reporting"])
    _r("submit_zero_report",        submit_zero_report,        "Submit a zero/no-data report",         "reporting", ["write", "reporting"])

    # ── rejected ads ──────────────────────────────────────────────
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
    _r("get_rejected_ads",       get_rejected_ads,       "List rejected ads",                    "rejected_ads", ["read",  "ads"])
    _r("appeal_rejected_ads",    appeal_rejected_ads,    "Appeal rejected ads",                  "rejected_ads", ["write", "ads"])
    _r("update_rejected_ad",     update_rejected_ad,     "Update rejected ad creative",          "rejected_ads", ["write", "ads"])
    _r("get_auto_swap_logs",     get_auto_swap_logs,     "Get auto-swap execution logs",         "rejected_ads", ["read",  "ads"])
    _r("get_auto_swap_summary",  get_auto_swap_summary,  "Get auto-swap summary",                "rejected_ads", ["read",  "ads"])
    _r("get_auto_delete_logs",   get_auto_delete_logs,   "Get auto-delete execution logs",       "rejected_ads", ["read",  "ads"])
    _r("get_auto_delete_summary",get_auto_delete_summary,"Get auto-delete summary",              "rejected_ads", ["read",  "ads"])
    _r("toggle_auto_swap",       toggle_auto_swap,       "Enable/disable auto-swap for account", "rejected_ads", ["write", "ads"])
    _r("toggle_auto_delete",     toggle_auto_delete,     "Enable/disable auto-delete for account","rejected_ads",["write", "ads"])

    # ── workspace ─────────────────────────────────────────────────
    from app.tools.workspace_tools import (
        create_workspace, update_workspace,
        toggle_workspace_status, list_workspaces, delete_workspaces,
    )
    _r("create_workspace",          create_workspace,          "Create a workspace",               "workspace", ["write", "workspace"])
    _r("update_workspace",          update_workspace,          "Update a workspace",               "workspace", ["write", "workspace"])
    _r("toggle_workspace_status",   toggle_workspace_status,   "Toggle workspace active status",   "workspace", ["write", "workspace"])
    _r("list_workspaces",           list_workspaces,           "List all workspaces",              "workspace", ["read",  "workspace"])
    _r("delete_workspaces",         delete_workspaces,         "Delete workspaces",                "workspace", ["write", "workspace"])

    # ── user management ───────────────────────────────────────────
    from app.tools.user_management_tools import (
        create_admin, create_team_lead, create_user,
        assign_team_lead, list_workspace_users, list_tl_users,
        get_user, delete_user,
    )
    _r("create_admin",          create_admin,          "Create an admin user",             "user_management", ["write", "users"])
    _r("create_team_lead",      create_team_lead,      "Create a team lead user",          "user_management", ["write", "users"])
    _r("create_user",           create_user,           "Create a regular user",            "user_management", ["write", "users"])
    _r("assign_team_lead",      assign_team_lead,      "Assign a team lead to a user",     "user_management", ["write", "users"])
    _r("list_workspace_users",  list_workspace_users,  "List all workspace users",         "user_management", ["read",  "users"])
    _r("list_tl_users",         list_tl_users,         "List users under a team lead",     "user_management", ["read",  "users"])
    _r("get_user",              get_user,              "Get a single user",                "user_management", ["read",  "users"])
    _r("delete_user",           delete_user,           "Delete a user",                    "user_management", ["write", "users"])

    # ── balance ───────────────────────────────────────────────────
    from app.tools.balance_tools import get_facebook_balances, get_google_balances
    _r("get_facebook_balances", get_facebook_balances, "Get Facebook ad account balances", "dashboard", ["read", "balance"])
    _r("get_google_balances",   get_google_balances,   "Get Google ad account balances",   "dashboard", ["read", "balance"])

    # ── campaign workflows ────────────────────────────────────────
    from app.tools.campaign_workflow import (
        workflow_launch_full_campaign,
        workflow_bulk_scale_campaigns,
        workflow_pause_all_for_account,
    )
    _r("workflow_launch_full_campaign",   workflow_launch_full_campaign,   "Launch campaign+adset+ad in one workflow with rollback", "campaigns", ["write", "campaigns", "workflow"])
    _r("workflow_bulk_scale_campaigns",   workflow_bulk_scale_campaigns,   "Scale campaign budgets by a multiplier",                 "campaigns", ["write", "campaigns", "workflow"])
    _r("workflow_pause_all_for_account",  workflow_pause_all_for_account,  "Pause all campaigns for an account",                    "campaigns", ["write", "campaigns", "workflow"])

    total = len(tool_registry.names())
    logger.info("Tool registry initialised", total_tools=total)
