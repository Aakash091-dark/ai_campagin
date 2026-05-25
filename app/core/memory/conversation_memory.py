# app/core/memory/conversation_memory.py
#
# FIX SUMMARY
# -----------
# 1. save_message_memory() now uses TWO separate transactions:
#    - Transaction A: persist the chat message (ai_messages) — must succeed
#      before the response is returned to the user.
#    - Transaction B: write the pgvector embedding (ai_memory_embedding) —
#      runs in a background asyncio task so it never blocks the response
#      and a failure here does NOT break the chat message transaction.
#
# 2. Every except block calls await db.rollback() so the session is never
#    left in InFailedSQLTransactionError state for subsequent queries.
#
# 3. The embedding INSERT uses a fresh savepoint (nested transaction) so
#    even if it fails the outer session stays clean.

import asyncio

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.models.conversation import Conversation
from app.core.memory.embeddings import generate_embedding
from app.config.logging import get_logger

logger = get_logger("conversation-memory")


# =========================================================
# ENSURE CONVERSATION EXISTS
# =========================================================
async def ensure_conversation(
    db: AsyncSession,
    workspace_id: int,
    conversation_id: str,
    user_id: int | None = None,
) -> Conversation:
    try:
        result = await db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        conversation = Conversation(
            id=conversation_id,
            workspace_id=workspace_id,
            user_id=user_id,
            is_active=True,
        )
        db.add(conversation)
        await db.flush()

        logger.info(
            "Conversation created",
            conversation_id=conversation_id,
            workspace_id=workspace_id,
        )
        return conversation

    except Exception as exc:
        logger.error("ensure_conversation failed", error=str(exc))
        try:
            await db.rollback()
        except Exception:
            pass
        raise


# =========================================================
# BACKGROUND EMBEDDING WRITER
# Runs in a fire-and-forget asyncio task.
# Uses its own isolated DB session so a failure here never
# contaminates the caller's session.
# =========================================================
async def _write_embedding_background(
    workspace_id: int,
    content: str,
    conversation_id: str,
) -> None:
    """
    Generate and persist a pgvector embedding for a message.
    Runs as a background task — the chat response is already sent
    before this executes, so any failure is logged but not surfaced.

    user_id is intentionally NOT stored — ai_memory_embedding has a FK
    to the local "user" table, but users live in the remote backend only.
    Scoping by workspace_id + conversation_id is sufficient for retrieval.
    """
    from app.config.database import AsyncSessionLocal  # local import avoids circular

    async with AsyncSessionLocal() as bg_db:
        try:
            embedding = await generate_embedding(content)
            summary = content[:200]

            # Do NOT insert user_id — the ai_memory_embedding table has a
            # foreign key to the local "user" table, but users are managed
            # by the remote backend (api.lemonmaxx.com) and do not exist
            # locally. Scoping by workspace_id + conversation_id is enough.
            await bg_db.execute(
                text("""
                    INSERT INTO ai_memory_embedding
                        (workspace_id, content, summary, category,
                         embedding, conversation_id)
                    VALUES
                        (:wid, :content, :summary, :category,
                         CAST(:embedding AS vector), :conv_id)
                """),
                {
                    "wid": workspace_id,
                    "content": content,
                    "summary": summary,
                    "category": "conversation",
                    "embedding": str(embedding),
                    "conv_id": conversation_id,
                },
            )

            await bg_db.commit()
            logger.info(
                "Background embedding saved",
                workspace_id=workspace_id,
                conversation_id=conversation_id,
            )

        except Exception as exc:
            logger.error("Background embedding write failed", error=str(exc))
            try:
                await bg_db.rollback()
            except Exception:
                pass


# =========================================================
# SAVE MESSAGE  (Transaction A — blocking)
# SAVE EMBEDDING (Transaction B — background, non-blocking)
# =========================================================
async def save_message_memory(
    db: AsyncSession,
    workspace_id: int,
    conversation_id: str,
    role: str,
    content: str,
    user_id: int | None = None,
    tools_used: list | None = None,
) -> bool:
    """
    Persist a chat message to ai_messages in its own transaction.

    The pgvector embedding is written asynchronously in a background
    task using a separate DB session, so:
      - The response is never delayed by embedding generation.
      - An embedding failure never breaks the chat message save.
      - The session passed in is never left in a failed-tx state.
    """
    # ── Transaction A: save the chat message ──────────────────────
    try:
        message = Message(
            conversation_id=conversation_id,
            workspace_id=workspace_id,
            user_id=user_id,
            role=role,
            content=content,
            tools_used=tools_used,
        )
        db.add(message)
        await db.commit()

    except Exception as exc:
        logger.error("Failed to save chat message", error=str(exc))
        try:
            await db.rollback()
        except Exception:
            pass
        return False

    # ── Transaction B: write embedding in background ───────────────
    # Only bother for messages long enough to be semantically useful.
    if len(content) > 20:
        asyncio.create_task(
            _write_embedding_background(
                workspace_id=workspace_id,
                content=content,
                conversation_id=conversation_id,
            )
        )

    return True


# =========================================================
# GET CONVERSATION HISTORY
# =========================================================
async def get_conversation_history(
    db: AsyncSession,
    conversation_id: str,
    limit: int = 20,
) -> list[dict]:
    try:
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
            .limit(limit)
        )
        return [
            {"role": m.role, "content": m.content}
            for m in result.scalars().all()
        ]
    except Exception as exc:
        logger.error("get_conversation_history failed", error=str(exc))
        try:
            await db.rollback()
        except Exception:
            pass
        return []
