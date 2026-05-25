# app/agents/analytics/agent.py
#
# Analytics agent — routes to the correct analytics endpoint
# based on user intent.  Date-range queries ask the user for
# missing dates before calling the backend.

import json

from app.core.orchestrator.state import AgentState
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
)
from app.tools.analytics import get_connected_ad_accounts
from app.core.llm.analyzer import generate_ai_response
from app.config.logging import get_logger

logger = get_logger("analytics-agent")


# =========================================================
# INTENT KEYWORDS
# =========================================================
ACCOUNT_KEYWORDS = [
    "account", "accounts", "ad account", "ad accounts",
    "connected", "connected account", "connected accounts",
]
LIVE_KEYWORDS = ["live", "real-time", "current performance", "right now"]
HISTORICAL_KEYWORDS = ["historical", "history", "past", "date range", "between"]
BREAKDOWN_KEYWORDS = ["breakdown", "hourly", "by hour", "granularity"]
TEAM_KEYWORDS = ["team", "team members", "member performance", "user performance"]
EXPORT_KEYWORDS = ["export", "download report", "generate report"]
CREATIVE_KEYWORDS = ["creative", "creatives", "ad creative", "creative performance"]
DYNAMIC_KEYWORDS = ["dynamic matrix", "matrix", "cross dimension", "dim1", "dim2"]
OFFER_KEYWORDS = ["offer", "offers", "vertical", "vertical offers"]


def _missing_fields_response(fields: list[str]) -> str:
    return json.dumps({
        "type": "missing_fields",
        "title": "More information needed",
        "message": "Please provide the following to run this analytics query:",
        "required_fields": fields,
    })


# =========================================================
# ANALYTICS AGENT
# =========================================================
async def run_analytics_agent(state: AgentState) -> AgentState:

    try:
        workspace_id = state["workspace_id"]
        message = state["message"]
        message_lower = message.lower()
        extra = state.get("extra_data", {}) or {}

        logger.info("Running analytics agent", workspace_id=workspace_id)

        tool_data = {}
        action_taken = "none"

        # =====================================================
        # CONNECTED AD ACCOUNTS
        # =====================================================
        if any(kw in message_lower for kw in ACCOUNT_KEYWORDS):

            tool_data = await get_connected_ad_accounts(workspace_id)
            action_taken = "get_connected_ad_accounts"

        # =====================================================
        # CREATIVE ANALYTICS
        # =====================================================
        elif any(kw in message_lower for kw in CREATIVE_KEYWORDS):

            platform = extra.get("platform")
            start_date = extra.get("start_date")
            end_date = extra.get("end_date")

            missing = []
            if not platform:
                missing.append("platform — facebook | google | tiktok")
            if not start_date:
                missing.append("start_date — YYYY-MM-DD")
            if not end_date:
                missing.append("end_date — YYYY-MM-DD")

            if missing:
                state["ui_json"] = _missing_fields_response(missing)
                state["success"] = True
                return state

            if "graph" in message_lower:
                tool_data = await get_creatives_graph(
                    workspace_id=workspace_id,
                    platform=platform,
                    start_date=start_date,
                    end_date=end_date,
                    view_mode=extra.get("view_mode", "workspace"),
                )
                action_taken = "get_creatives_graph"
            else:
                tool_data = await get_creatives_cards(
                    workspace_id=workspace_id,
                    platform=platform,
                    start_date=start_date,
                    end_date=end_date,
                    view_mode=extra.get("view_mode", "workspace"),
                )
                action_taken = "get_creatives_cards"

        # =====================================================
        # DYNAMIC MATRIX
        # =====================================================
        elif any(kw in message_lower for kw in DYNAMIC_KEYWORDS):

            platform = extra.get("platform")
            start_date = extra.get("start_date")
            end_date = extra.get("end_date")

            missing = []
            if not platform:
                missing.append("platform — facebook | google | tiktok")
            if not start_date:
                missing.append("start_date — YYYY-MM-DD")
            if not end_date:
                missing.append("end_date — YYYY-MM-DD")

            if missing:
                state["ui_json"] = _missing_fields_response(missing)
                state["success"] = True
                return state

            tool_data = await get_dynamic_matrix(
                workspace_id=workspace_id,
                platform=platform,
                start_date=start_date,
                end_date=end_date,
                dim1=extra.get("dim1"),
                dim2=extra.get("dim2"),
                dim3=extra.get("dim3"),
            )
            action_taken = "get_dynamic_matrix"

        # =====================================================
        # EXPORT ANALYTICS REPORT
        # =====================================================
        elif any(kw in message_lower for kw in EXPORT_KEYWORDS):

            if "status" in message_lower:
                export_id = extra.get("export_id")
                if not export_id:
                    state["ui_json"] = _missing_fields_response(["export_id — Export job ID"])
                    state["success"] = True
                    return state
                tool_data = await get_export_status(workspace_id, int(export_id))
                action_taken = "get_export_status"

            elif "list" in message_lower or "show" in message_lower:
                date_from = extra.get("date_from") or extra.get("start_date")
                date_to = extra.get("date_to") or extra.get("end_date")
                if not date_from or not date_to:
                    state["ui_json"] = _missing_fields_response(
                        ["date_from — YYYY-MM-DD", "date_to — YYYY-MM-DD"]
                    )
                    state["success"] = True
                    return state
                tool_data = await list_analytics_exports(workspace_id, date_from, date_to)
                action_taken = "list_analytics_exports"

            else:
                platform = extra.get("platform")
                date_from = extra.get("date_from") or extra.get("start_date")
                date_to = extra.get("date_to") or extra.get("end_date")
                missing = []
                if not platform:
                    missing.append("platform — facebook | google | tiktok")
                if not date_from:
                    missing.append("date_from — YYYY-MM-DD")
                if not date_to:
                    missing.append("date_to — YYYY-MM-DD")
                if missing:
                    state["ui_json"] = _missing_fields_response(missing)
                    state["success"] = True
                    return state
                tool_data = await create_analytics_export(
                    workspace_id=workspace_id,
                    platform=platform,
                    date_from=date_from,
                    date_to=date_to,
                    full=extra.get("full", False),
                )
                action_taken = "create_analytics_export"

        # =====================================================
        # TEAM MEMBERS ANALYTICS
        # =====================================================
        elif any(kw in message_lower for kw in TEAM_KEYWORDS):

            platform = extra.get("platform")
            from_date = extra.get("from_date") or extra.get("start_date")
            to_date = extra.get("to_date") or extra.get("end_date")

            missing = []
            if not platform:
                missing.append("platform — facebook | google | tiktok")
            if not from_date:
                missing.append("from_date — YYYY-MM-DD")
            if not to_date:
                missing.append("to_date — YYYY-MM-DD")

            if missing:
                state["ui_json"] = _missing_fields_response(missing)
                state["success"] = True
                return state

            tool_data = await get_team_members_analytics(
                workspace_id=workspace_id,
                platform=platform,
                from_date=from_date,
                to_date=to_date,
            )
            action_taken = "get_team_members_analytics"

        # =====================================================
        # HISTORICAL BREAKDOWN
        # =====================================================
        elif any(kw in message_lower for kw in BREAKDOWN_KEYWORDS):

            platform = extra.get("platform")
            start_date = extra.get("start_date")
            end_date = extra.get("end_date")

            missing = []
            if not platform:
                missing.append("platform — facebook | google | tiktok")
            if not start_date:
                missing.append("start_date — YYYY-MM-DD")
            if not end_date:
                missing.append("end_date — YYYY-MM-DD")

            if missing:
                state["ui_json"] = _missing_fields_response(missing)
                state["success"] = True
                return state

            tool_data = await get_historical_breakdown(
                workspace_id=workspace_id,
                platform=platform,
                start_date=start_date,
                end_date=end_date,
                granularity=extra.get("granularity", "hour"),
                campaign_id=extra.get("campaign_id"),
            )
            action_taken = "get_historical_breakdown"

        # =====================================================
        # HISTORICAL INSIGHTS
        # =====================================================
        elif any(kw in message_lower for kw in HISTORICAL_KEYWORDS):

            platform = extra.get("platform")
            start_date = extra.get("start_date")
            end_date = extra.get("end_date")

            if not platform and not start_date and not end_date:
                # Cross-platform if no platform specified
                state["ui_json"] = _missing_fields_response(
                    ["start_date — YYYY-MM-DD", "end_date — YYYY-MM-DD"]
                )
                state["success"] = True
                return state

            if not start_date or not end_date:
                state["ui_json"] = _missing_fields_response(
                    ["start_date — YYYY-MM-DD", "end_date — YYYY-MM-DD"]
                )
                state["success"] = True
                return state

            if platform:
                tool_data = await get_historical_campaign_insights(
                    workspace_id=workspace_id,
                    platform=platform,
                    start_date=start_date,
                    end_date=end_date,
                )
                action_taken = "get_historical_campaign_insights"
            else:
                tool_data = await get_cross_platform_historical_insights(
                    workspace_id=workspace_id,
                    start_date=start_date,
                    end_date=end_date,
                )
                action_taken = "get_cross_platform_historical_insights"

        # =====================================================
        # LIVE INSIGHTS (default)
        # =====================================================
        else:

            tool_data = await get_live_campaign_insights(
                workspace_id=workspace_id,
                platform=extra.get("platform"),
            )
            action_taken = "get_live_campaign_insights"

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

        logger.error("Analytics agent failed", error=str(e))

        state["success"] = False
        state["error"] = str(e)
        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Analytics Error",
            "message": str(e),
        })

        return state
