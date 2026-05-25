# app/core/memory/context_builder.py

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.memory.conversation_memory import (
    get_conversation_history,
)

from app.core.memory.semantic_search import (
    semantic_memory_search,
)

from app.config.logging import get_logger


logger = get_logger("context-builder")


# =========================================================
# BUILD AI CONTEXT
# =========================================================
async def build_context(
    db: AsyncSession,
    workspace_id: int,
    conversation_id: str,
    user_message: str,
):

    try:

        history = await get_conversation_history(
            db=db,
            conversation_id=conversation_id,
            limit=10,
        )

        history = [
            msg for msg in history
            if msg["role"] in ["user", "assistant"]
        ]

        semantic_memories = await semantic_memory_search(
            db=db,
            workspace_id=workspace_id,
            query=user_message,
            limit=5,
        )

        memory_context = ""

        for memory in semantic_memories:

            memory_context += (
                f"\nRelevant Memory:\n"
                f"{memory['content']}\n"
            )

        return {
            "system_context": memory_context,
            "history": history
        }

    except Exception as e:

        logger.error(
            "Failed to build context",
            error=str(e),
        )

        return {
            "system_context": "",
            "history": []
        }