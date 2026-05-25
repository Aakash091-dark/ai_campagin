# app/core/orchestrator/router.py

from app.config.logging import get_logger

logger = get_logger("router")


# =========================================================
# AGENT ROUTER
# =========================================================
async def route_agent(message: str) -> str:

    msg = message.lower()

    # =====================================================
    # SMART ALERTS
    # =====================================================
    smart_alert_keywords = [
        "smart alert", "alert", "create alert", "new alert",
        "alert rule", "alert condition", "alert logs",
        "triggered alert",
    ]

    # =====================================================
    # TASKS
    # =====================================================
    task_keywords = [
        "task", "tasks", "create task", "assign task",
        "task status", "task comment", "task category",
        "task tag", "task priority", "due date",
    ]

    # =====================================================
    # WORKSPACE
    # =====================================================
    workspace_keywords = [
        "workspace", "create workspace", "new workspace",
        "delete workspace", "timezone", "time zone",
    ]

    # =====================================================
    # USER MANAGEMENT
    # =====================================================
    user_mgmt_keywords = [
        "create user", "add user", "invite user",
        "create admin", "create team lead", "create tl",
        "delete user", "remove user", "assign tl",
        "user management", "manage users", "list users",
        "my profile", "user profile", "update profile",
    ]

    # =====================================================
    # ANALYTICS
    # =====================================================
    analytics_keywords = [
        "analytics", "insights", "performance",
        "roi", "roas", "cpm", "ctr", "spend",
        "top campaigns", "losing campaigns", "best campaigns",
        "metrics", "trend", "historical", "breakdown",
        "team members", "export report", "dynamic matrix",
        "creatives", "creative performance", "offers",
    ]

    # =====================================================
    # CAMPAIGNS
    # =====================================================
    campaign_keywords = [
        "pause", "resume", "launch", "campaign",
        "budget", "bid", "duplicate", "delete campaign",
        "scale campaign", "adset", "ad set", "create ad",
        "campaign template", "launch campaign",
    ]

    # =====================================================
    # AUTOMATIONS
    # =====================================================
    automation_keywords = [
        "automation", "rule", "trigger", "auto",
        "workflow", "create automation", "automation rule",
        "automation logs",
    ]

    # =====================================================
    # REJECTED ADS
    # =====================================================
    rejected_keywords = [
        "rejected", "appeal", "creative rejected",
        "ad rejected", "policy violation", "auto swap",
        "auto delete", "auto-swap", "auto-delete",
    ]

    # =====================================================
    # REPORTING
    # =====================================================
    reporting_keywords = [
        "report", "export", "download report",
        "generate report", "reporting config",
        "reporting slots", "submit report", "zero report",
    ]

    # =====================================================
    # DASHBOARD
    # =====================================================
    dashboard_keywords = [
        "dashboard", "overview", "summary",
        "total spend", "total roas", "total revenue",
        "how many accounts", "how many campaigns",
        "connected accounts", "ad accounts", "all accounts",
        "workspace overview", "overall performance",
        "overall spend", "balance", "timeseries",
        "user trends", "tl users", "accounts ads",
        "drilldown", "drill down",
    ]

    # =====================================================
    # ROUTE — most specific first
    # =====================================================

    if any(kw in msg for kw in smart_alert_keywords):
        logger.info("Smart alerts route selected")
        return "smart_alerts"

    if any(kw in msg for kw in task_keywords):
        logger.info("Tasks route selected")
        return "tasks"

    if any(kw in msg for kw in workspace_keywords):
        logger.info("Workspace route selected")
        return "workspace"

    if any(kw in msg for kw in user_mgmt_keywords):
        logger.info("User management route selected")
        return "user_management"

    if any(kw in msg for kw in analytics_keywords):
        logger.info("Analytics route selected")
        return "analytics"

    if any(kw in msg for kw in campaign_keywords):
        logger.info("Campaign route selected")
        return "campaigns"

    if any(kw in msg for kw in automation_keywords):
        logger.info("Automation route selected")
        return "automations"

    if any(kw in msg for kw in rejected_keywords):
        logger.info("Rejected ads route selected")
        return "rejected_ads"

    if any(kw in msg for kw in reporting_keywords):
        logger.info("Reporting route selected")
        return "reporting"

    if any(kw in msg for kw in dashboard_keywords):
        logger.info("Dashboard route selected")
        return "dashboard"

    logger.info("General route selected (fallback)")
    return "general"
