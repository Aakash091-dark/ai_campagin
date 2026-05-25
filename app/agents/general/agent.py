# app/agents/general/agent.py

import json

from app.core.orchestrator.state import (
    AgentState,
)

from app.core.llm.analyzer import (
    generate_ai_response,
)

from app.config.logging import (
    get_logger,
)


logger = get_logger(
    "general-agent"
)


# =========================================================
# GENERAL CHAT AGENT
# =========================================================
async def run_general_agent(
    state: AgentState
):

    try:

        message = state["message"]

        logger.info(
            "Running general agent"
        )

        # =============================================
        # AI RESPONSE — structured JSON
        # =============================================
        ai_result = (
            await generate_ai_response(
                user_message=message,
                tool_data={
                    "type": "general_chat"
                },
                conversation_context=state.get(
                    "memory_context",
                    [],
                ),
                db_context=state.get("db_context"),
            )
        )

        # =============================================
        # STORE UI JSON
        # =============================================
        state["ui_json"] = (
            ai_result["ui_json"]
        )

        state["tokens_used"] = (
            ai_result["tokens_used"]
        )

        state["success"] = True

        return state

    except Exception as e:

        logger.error(
            "General agent failed",
            error=str(e),
        )

        state["success"] = False

        state["error"] = str(e)

        state["ui_json"] = json.dumps({
            "type": "error",
            "title": "Chat Error",
            "message": str(e),
        })

        return state