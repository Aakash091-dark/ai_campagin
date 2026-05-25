# app/core/orchestrator/graph.py

import time

from sqlalchemy.ext.asyncio import AsyncSession

from langgraph.graph import StateGraph, END

from app.core.orchestrator.state import AgentState
from app.core.orchestrator.router import route_agent

from app.agents.analytics.agent import run_analytics_agent
from app.agents.campaigns.agent import run_campaign_agent
from app.agents.automations.agent import run_automation_agent
from app.agents.reporting.agent import run_reporting_agent
from app.agents.rejected_ads.agent import run_rejected_ads_agent
from app.agents.general.agent import run_general_agent
from app.agents.dashboard.agent import run_dashboard_agent
from app.agents.smart_alerts.agent import run_smart_alerts_agent
from app.agents.tasks.agent import run_tasks_agent
from app.agents.workspace.agent import run_workspace_agent
from app.agents.user_management.agent import run_user_management_agent

from app.core.orchestrator.post_processor import process_final_response
from app.services.db_context import resolve_workspace_context
from app.config.logging import get_logger

logger = get_logger("graph")


# =========================================================
# ROUTER NODE
# =========================================================
async def router_node(state: AgentState):
    selected_agent = await route_agent(state["message"])
    state["selected_agent"] = selected_agent
    logger.info("Agent selected", agent=selected_agent)
    return state


# =========================================================
# AGENT NODES
# =========================================================
async def analytics_node(state: AgentState):
    return await run_analytics_agent(state)

async def campaigns_node(state: AgentState):
    return await run_campaign_agent(state)

async def automations_node(state: AgentState):
    return await run_automation_agent(state)

async def reporting_node(state: AgentState):
    return await run_reporting_agent(state)

async def rejected_ads_node(state: AgentState):
    return await run_rejected_ads_agent(state)

async def general_node(state: AgentState):
    return await run_general_agent(state)

async def dashboard_node(state: AgentState):
    return await run_dashboard_agent(state)

async def smart_alerts_node(state: AgentState):
    return await run_smart_alerts_agent(state)

async def tasks_node(state: AgentState):
    return await run_tasks_agent(state)

async def workspace_node(state: AgentState):
    return await run_workspace_agent(state)

async def user_management_node(state: AgentState):
    return await run_user_management_agent(state)


# =========================================================
# POST PROCESSOR NODE
# =========================================================
async def post_processor_node(state: AgentState):
    return process_final_response(state)


# =========================================================
# CONDITIONAL ROUTER
# =========================================================
def route_by_agent(state: AgentState) -> str:
    routing_map = {
        "analytics": "analytics",
        "campaigns": "campaigns",
        "automations": "automations",
        "reporting": "reporting",
        "rejected_ads": "rejected_ads",
        "general": "general",
        "dashboard": "dashboard",
        "smart_alerts": "smart_alerts",
        "tasks": "tasks",
        "workspace": "workspace",
        "user_management": "user_management",
    }
    return routing_map.get(state["selected_agent"], "general")


# =========================================================
# BUILD GRAPH
# =========================================================
workflow = StateGraph(AgentState)

_nodes = {
    "router": router_node,
    "analytics": analytics_node,
    "campaigns": campaigns_node,
    "automations": automations_node,
    "reporting": reporting_node,
    "rejected_ads": rejected_ads_node,
    "general": general_node,
    "dashboard": dashboard_node,
    "smart_alerts": smart_alerts_node,
    "tasks": tasks_node,
    "workspace": workspace_node,
    "user_management": user_management_node,
    "post_processor": post_processor_node,
}

for name, fn in _nodes.items():
    workflow.add_node(name, fn)

workflow.set_entry_point("router")

_agent_names = [
    "analytics", "campaigns", "automations", "reporting",
    "rejected_ads", "general", "dashboard",
    "smart_alerts", "tasks", "workspace", "user_management",
]

workflow.add_conditional_edges(
    "router",
    route_by_agent,
    {name: name for name in _agent_names},
)

for name in _agent_names:
    workflow.add_edge(name, "post_processor")

workflow.add_edge("post_processor", END)

graph = workflow.compile()


# =========================================================
# RUN GRAPH
# Accepts an optional AsyncSession so the DB context can be
# resolved once before any agent runs.
# =========================================================
async def run_ai_graph(
    workspace_id: int,
    message: str,
    conversation_id: str,
    user_id: int | None = None,
    memory_context: list | None = None,
    extra_data: dict | None = None,
    db: AsyncSession | None = None,
) -> dict:

    start_time = time.time()

    # ─────────────────────────────────────────────────────
    # RESOLVE DB CONTEXT
    # Query the database once to get all IDs the agents need:
    # accounts, users, tasks, rules, alerts, etc.
    # Agents read state["db_context"] instead of asking the user.
    # ─────────────────────────────────────────────────────
    db_context: dict = {}
    if db is not None:
        try:
            db_context = await resolve_workspace_context(
                db=db,
                workspace_id=workspace_id,
                user_id=user_id,
            )
        except Exception as e:
            logger.error("DB context resolution failed", error=str(e))
            db_context = {"workspace_id": workspace_id, "user_id": user_id}
    else:
        db_context = {"workspace_id": workspace_id, "user_id": user_id}

    initial_state: AgentState = {
        "workspace_id": workspace_id,
        "user_id": user_id,
        "message": message,
        "conversation_id": conversation_id,
        "intent": None,
        "selected_agent": None,
        "memory_context": memory_context or [],
        "db_context": db_context,
        "extra_data": extra_data or {},
        "tools_used": [],
        "tool_results": [],
        "ui_json": None,
        "openui_response": "",
        "tokens_used": 0,
        "execution_time": 0,
        "success": True,
        "error": None,
    }

    result = await graph.ainvoke(initial_state)
    result["execution_time"] = round(time.time() - start_time, 2)

    return result
