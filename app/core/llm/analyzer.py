# app/core/llm/analyzer.py

import json
from typing import Any

from app.core.llm.client import (
    generate_completion,
)

from app.services.db_context import summarise_context

from app.config.logging import (
    get_logger,
)


logger = get_logger("analyzer")


# =========================================================
# GENERATE AI RESPONSE
# =========================================================
async def generate_ai_response(
    user_message: str,
    tool_data: dict | list,
    conversation_context: dict | None = None,
    db_context: dict[str, Any] | None = None,
):
    """
    Generate a structured JSON response from the LLM.

    db_context — the resolved workspace context from the database
    (accounts, users, tasks, automation rules, etc.).
    Injected into the system prompt so the AI knows all IDs
    without the user having to provide them.
    """

    try:

        messages = []

        # =============================================
        # MEMORY CONTEXT (conversation history + semantic)
        # =============================================
        system_context = ""

        if conversation_context:

            history = conversation_context.get(
                "history",
                []
            )

            system_context = conversation_context.get(
                "system_context",
                ""
            )

            for item in history:

                if item["role"] in [
                    "user",
                    "assistant",
                ]:

                    messages.append({
                        "role": item["role"],
                        "content": item["content"],
                    })

        # =============================================
        # DB CONTEXT — inject workspace data into system prompt
        # The AI learns all account IDs, user IDs, task IDs etc.
        # from the database so it never asks the user for them.
        # =============================================
        if db_context:
            db_summary = summarise_context(db_context)
            if db_summary and db_summary != "No context data available.":
                system_context = (
                    f"{system_context}\n\n"
                    f"## WORKSPACE DATABASE CONTEXT\n"
                    f"The following data is already resolved from the database. "
                    f"Use these IDs directly — never ask the user for IDs.\n\n"
                    f"{db_summary}"
                )

        # =============================================
        # TOOL DATA
        # =============================================
        formatted_tool_data = json.dumps(
            tool_data,
            indent=2,
            default=str,
        )

        # =============================================
        # USER MESSAGE
        # =============================================
        messages.append({
            "role": "user",
            "content": f"""
USER REQUEST:
{user_message}

TOOL RESULTS:
{formatted_tool_data}

IMPORTANT RULES:
- Use ONLY provided data
- Never hallucinate metrics
- Return ONLY valid JSON matching the output schemas
- Never return markdown
- Never explain outside JSON
- Use IDs from the WORKSPACE DATABASE CONTEXT above — never ask the user for workspace_id, account_id, user_id, task_id, category_id, etc.
"""
        })

        logger.info(
            "Generating AI response",
            history_messages=len(messages),
            has_db_context=bool(db_context),
        )

        # =============================================
        # GENERATE
        # =============================================
        result = await generate_completion(
            messages=messages,
            system=system_context,
        )

        # =============================================
        # RESULT IS JSON STRING — store as ui_json
        # =============================================
        return {
            "ui_json": result[
                "response"
            ],
            "tokens_used": result[
                "tokens_used"
            ],
        }

    except Exception as e:

        logger.error(
            "Analyzer failed",
            error=str(e),
        )

        raise e