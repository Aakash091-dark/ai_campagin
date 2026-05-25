# app/agents/dashboard/agent.py
#
# Dashboard agent — routes to the correct dashboard endpoint
# based on user intent.  Date-range queries ask the user for
# missing parameters before calling the backend.

import json

from app.core.orchestrator.state import AgentState
from app.tools.dashboard_tools import (
    get_dashboard_summary,
    get_dashboard_timeseries,
    get_dashboard_user_trends,
    get_dashboard_accounts_ads,
    get_dashboard_tl_users,
    get_dashboard_account_drilldown,
)
from app.tools.balance_tools import (
    get_facebook_balances,
    get_google_balances,
)
from app.services.db_context import (
    resolve_user_id_from_name,
    resolve_account_db_id_from_name,
)
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("dashboard-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
TIMESERIES_KEYWORDS = [
    "timeseries", "time series", "trend", "over time",
    "daily", "weekly", "hourly", "by day", "by week", "by hour",
]
USER_TRENDS_KEYWORDS = [
    "user trend", "user performance", "my trend", "my performance",
]
ACCOUNTS_ADS_KEYWORDS = [
    "accounts ads", "account ads", "ads per account",
]
TL_USERS_KEYWORDS = [
    "tl users", "team lead users", "tl performance",
]
DRILLDOWN_KEYWORDS = [
    "drilldown", "drill down", "account detail", "account data",
    "account performance",
]
BALANCE_KEYWORDS = [
    "balance", "balances", "account balance", "ad spend balance",
    "facebook balance", "google balance",
]
METRICS_KEYWORDS = [
    "metrics", "roas", "ctr", "cpc", "cpm", "impressions",
    "clicks", "conversions", "cost per", "performance",
]
ACCOUNTS_KEYWORDS = [
    "account", "accounts", "ad account", "ad accounts",
    "connected account", "connected accounts",
    "how many accounts", "which accounts", "list accounts",
]


def _missing_fields_response(fields: list[str]) -> str:
    return json.dumps({
        "type": "missing_fields",
        "title": "More information needed",
        "message": "Please provide the following to run this dashboard query:",
        "required_fields": fields,
    })


# =========================================================
# DASHBOARD AGENT
# =========================================================
async def run_dashboard_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}
        db_ctx = state.get("db_context") or {}

        logger.info("Running dashboard agent", workspace_id=workspace_id)

        # ─────────────────────────────────────────────────────
        # AUTO-RESOLVE IDs FROM DB CONTEXT
        # ─────────────────────────────────────────────────────

        # Resolve user_id from user name for user trends
        if extra.get("user_name") and not extra.get("user_id"):
            resolved = resolve_user_id_from_name(db_ctx, str(extra["user_name"]))
            if resolved:
                extra = {**extra, "user_id": resolved}

        # Resolve account_id from account name for drilldown
        if extra.get("account_name") and not extra.get("account_id"):
            acc = resolve_account_db_id_from_name(db_ctx, str(extra["account_name"]))
            if acc:
                extra = {**extra, "account_id": acc}

        tool_data = {}
        action_taken = "none"

        # =====================================================
        # BALANCE
        # =====================================================
        if any(kw in message_lower for kw in BALANCE_KEYWORDS):

            if "google" in message_lower:
                tool_data = await get_google_balances(workspace_id=workspace_id)
                action_taken = "get_google_balances"
            else:
                tool_data = await get_facebook_balances(workspace_id=workspace_id)
                action_taken = "get_facebook_balances"

        # =====================================================
        # ACCOUNT DRILLDOWN
        # =====================================================
        elif any(kw in message_lower for kw in DRILLDOWN_KEYWORDS):

            platform = extra.get("platform")
            account_id = extra.get("account_id")
            start_date = extra.get("start_date")
            end_date = extra.get("end_date")

            missing = []
            if not platform:
                missing.append("platform — facebook | google | tiktok")
            if not account_id:
                missing.append("account_id — Ad account ID")
            if not start_date:
                missing.append("start_date — YYYY-MM-DD")
            if not end_date:
                missing.append("end_date — YYYY-MM-DD")

            if missing:
                state["ui_json"] = _missing_fields_response(missing)
                state["success"] = True
                return state

            tool_data = await get_dashboard_account_drilldown(
                workspace_id=workspace_id,
                platform=platform,
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
            )
            action_taken = "get_dashboard_account_drilldown"

        # =====================================================
        # TL USERS
        # =====================================================
        elif any(kw in message_lower for kw in TL_USERS_KEYWORDS):

            from_date = extra.get("from_date") or extra.get("start_date")
            to_date = extra.get("to_date") or extra.get("end_date")

            if not from_date or not to_date:
                state["ui_json"] = _missing_fields_response(
                    ["from_date — YYYY-MM-DD", "to_date — YYYY-MM-DD"]
                )
                state["success"] = True
                return state

            tool_data = await get_dashboard_tl_users(
                workspace_id=workspace_id,
                from_date=from_date,
                to_date=to_date,
            )
            action_taken = "get_dashboard_tl_users"

        # =====================================================
        # ACCOUNTS ADS
        # =====================================================
        elif any(kw in message_lower for kw in ACCOUNTS_ADS_KEYWORDS):

            from_date = extra.get("from_date") or extra.get("start_date")
            to_date = extra.get("to_date") or extra.get("end_date")

            if not from_date or not to_date:
                state["ui_json"] = _missing_fields_response(
                    ["from_date — YYYY-MM-DD", "to_date — YYYY-MM-DD"]
                )
                state["success"] = True
                return state

            tool_data = await get_dashboard_accounts_ads(
                workspace_id=workspace_id,
                from_date=from_date,
                to_date=to_date,
            )
            action_taken = "get_dashboard_accounts_ads"

        # =====================================================
        # USER TRENDS
        # =====================================================
        elif any(kw in message_lower for kw in USER_TRENDS_KEYWORDS):

            user_id = extra.get("user_id")
            granularity = extra.get("granularity", "day")
            from_date = extra.get("from_date") or extra.get("start_date")
            to_date = extra.get("to_date") or extra.get("end_date")

            missing = []
            if not user_id:
                missing.append("user_id — User ID")
            if not from_date:
                missing.append("from_date — YYYY-MM-DD")
            if not to_date:
                missing.append("to_date — YYYY-MM-DD")

            if missing:
                state["ui_json"] = _missing_fields_response(missing)
                state["success"] = True
                return state

            tool_data = await get_dashboard_user_trends(
                workspace_id=workspace_id,
                user_id=int(user_id),
                granularity=granularity,
                from_date=from_date,
                to_date=to_date,
            )
            action_taken = "get_dashboard_user_trends"

        # =====================================================
        # TIMESERIES
        # =====================================================
        elif any(kw in message_lower for kw in TIMESERIES_KEYWORDS):

            granularity = extra.get("granularity", "day")
            if "hour" in message_lower:
                granularity = "hour"
            elif "week" in message_lower:
                granularity = "week"

            from_date = extra.get("from_date") or extra.get("start_date")
            to_date = extra.get("to_date") or extra.get("end_date")

            if not from_date or not to_date:
                state["ui_json"] = _missing_fields_response(
                    [
                        "from_date — YYYY-MM-DD",
                        "to_date — YYYY-MM-DD",
                        f"granularity — day | hour | week (detected: {granularity})",
                    ]
                )
                state["success"] = True
                return state

            tool_data = await get_dashboard_timeseries(
                workspace_id=workspace_id,
                granularity=granularity,
                from_date=from_date,
                to_date=to_date,
            )
            action_taken = "get_dashboard_timeseries"

        # =====================================================
        # DEFAULT: DASHBOARD SUMMARY
        # =====================================================
        else:

            from_date = extra.get("from_date") or extra.get("start_date")
            to_date = extra.get("to_date") or extra.get("end_date")

            tool_data = await get_dashboard_summary(
                workspace_id=workspace_id,
                from_date=from_date,
                to_date=to_date,
            )
            action_taken = "get_dashboard_summary"

        state["tools_used"].append(action_taken)
        state["tool_results"].append(tool_data)

        ai_result = await generate_ai_response(
            user_message=message,
            tool_data=tool_data,
            conversation_context=state.get("memory_context", []),
            db_context=state.get("db_context"),
        )

        state["ui_json"] = ai_result["ui_json"]
        state["tokens_used"] = ai_result["tokens_used"]
        state["success"] = True

        return state

    except Exception as e:

        logger.error("Dashboard agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Dashboard Error",
            "message": str(e),
        })

        return state
