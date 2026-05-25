# app/core/orchestrator/state.py

from typing import TypedDict, Optional, List, Dict, Any


# =========================================================
# GRAPH STATE
# =========================================================
class AgentState(TypedDict):

    # =====================================================
    # USER / WORKSPACE
    # =====================================================
    workspace_id: int

    user_id: Optional[int]

    message: str

    conversation_id: str

    # =====================================================
    # ROUTING
    # =====================================================
    intent: Optional[str]

    selected_agent: Optional[str]

    # =====================================================
    # MEMORY
    # =====================================================
    memory_context: List[Dict[str, Any]]

    # =====================================================
    # DB CONTEXT
    # Resolved from the database before agents run.
    # Contains: accounts, users, tasks, automation_rules,
    # smart_alert_rules, task_categories, task_tags,
    # goals, reporting_config, trackers, my_accounts.
    # Agents read this instead of asking the user for IDs.
    # =====================================================
    db_context: Dict[str, Any]

    # =====================================================
    # EXTRA DATA (structured params from user / frontend)
    # Agents read this dict to get validated field values
    # for write operations instead of parsing free text.
    # =====================================================
    extra_data: Optional[Dict[str, Any]]

    # =====================================================
    # TOOLS
    # =====================================================
    tools_used: List[str]

    tool_results: List[Dict[str, Any]]

    # =====================================================
    # UI JSON (STRUCTURED JSON FROM LLM)
    # =====================================================
    ui_json: Optional[str]

    # =====================================================
    # OPENUI RESPONSE (RENDERED FROM ui_json)
    # =====================================================
    openui_response: str

    # =====================================================
    # EXECUTION META
    # =====================================================
    tokens_used: int

    execution_time: float

    # =====================================================
    # STATUS
    # =====================================================
    success: bool

    error: Optional[str]
