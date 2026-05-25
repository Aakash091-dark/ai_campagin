# app/core/memory/semantic_search.py
#
# Semantic memory search using pgvector's native cosine-distance operator (<=>).
# Replaces the old Python-side numpy cosine similarity loop.
#
# FIX: Build the SQL query dynamically so we never pass a NULL typed
# parameter to PostgreSQL — avoids AmbiguousParameterError on :uid.
#
# The HNSW index on ai_memory_embedding.embedding makes this O(log n)
# instead of O(n) full-table scan.

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.memory.embeddings import generate_embedding
from app.config.settings import settings
from app.config.logging import get_logger

logger = get_logger("semantic-search")


async def semantic_memory_search(
    db: AsyncSession,
    workspace_id: int,
    query: str,
    limit: int = 5,
    user_id: int | None = None,
) -> list[dict]:
    """
    Find the most semantically similar memories for a workspace using
    pgvector's cosine-distance operator (<=>) and the HNSW index.

    Returns a list of dicts with keys: id, content, similarity, category.
    Only results with similarity >= SIMILARITY_THRESHOLD are returned.

    FIX: user_id filter is appended dynamically so PostgreSQL never
    receives a NULL parameter with an ambiguous type, which caused
    AmbiguousParameterError and broke the entire transaction.
    """
    try:
        query_embedding = await generate_embedding(query)

        # pgvector cosine distance: 0 = identical, 2 = opposite.
        # similarity = 1 - distance  →  higher is better.
        threshold_distance = 1.0 - settings.SIMILARITY_THRESHOLD

        # ── Build query dynamically to avoid NULL type ambiguity ──
        base_sql = """
            SELECT
                id,
                content,
                category,
                1 - (embedding <=> CAST(:embedding AS vector)) AS similarity
            FROM ai_memory_embedding
            WHERE workspace_id = :wid
              AND (embedding <=> CAST(:embedding AS vector)) <= :threshold
        """

        params: dict = {
            "embedding": str(query_embedding),
            "wid": workspace_id,
            "threshold": threshold_distance,
            "lim": limit,
        }

        # Only add the user_id clause when we actually have a value —
        # passing NULL as :uid causes PostgreSQL to raise
        # AmbiguousParameterError because it cannot infer the column type.
        if user_id is not None:
            base_sql += " AND user_id = :uid"
            params["uid"] = user_id

        base_sql += """
            ORDER BY embedding <=> CAST(:embedding AS vector)
            LIMIT :lim
        """

        result = await db.execute(text(base_sql), params)

        rows = result.fetchall()

        memories = [
            {
                "id": row.id,
                "content": row.content,
                "similarity": float(row.similarity),
                "category": row.category,
            }
            for row in rows
        ]

        logger.info(
            "Semantic search complete",
            workspace_id=workspace_id,
            results=len(memories),
        )

        return memories

    except Exception as exc:
        logger.error("Semantic search failed", error=str(exc))
        # Rollback so the session is not left in a failed-transaction state.
        # Callers share the same AsyncSession; without this rollback every
        # subsequent query in the same request would fail with
        # InFailedSQLTransactionError.
        try:
            await db.rollback()
        except Exception:
            pass
        return []
