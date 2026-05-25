# app/api/routes/memory.py
#
# Memory API — search and manage semantic memories stored in
# the ai_memory_embedding table (pgvector).

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter, Depends, HTTPException, Query

from app.config.database import get_db
from app.api.dependencies.user import get_current_user
from app.core.memory.semantic_search import semantic_memory_search
from app.config.logging import get_logger

router = APIRouter()
logger = get_logger("memory-routes")


# =========================================================
# SEARCH MEMORIES
# GET /api/v1/memory/search?q=...&limit=5
# =========================================================
@router.get("/search")
async def search_memories(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Semantic search over the user's memory embeddings."""
    user_id = current_user["user_id"]

    # Resolve workspace_id from user record
    row = await db.execute(
        text('SELECT workspace_id FROM "user" WHERE id = :uid LIMIT 1'),
        {"uid": user_id},
    )
    workspace_id = row.scalar_one_or_none()
    if workspace_id is None:
        raise HTTPException(status_code=404, detail="User has no workspace")

    results = await semantic_memory_search(
        db=db,
        workspace_id=int(workspace_id),
        query=q,
        limit=limit,
        user_id=user_id,
    )

    return {"success": True, "count": len(results), "data": results}


# =========================================================
# LIST RECENT MEMORIES
# GET /api/v1/memory/?limit=20
# =========================================================
@router.get("/")
async def list_memories(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """List the most recent memory entries for the current user."""
    user_id = current_user["user_id"]

    row = await db.execute(
        text('SELECT workspace_id FROM "user" WHERE id = :uid LIMIT 1'),
        {"uid": user_id},
    )
    workspace_id = row.scalar_one_or_none()
    if workspace_id is None:
        raise HTTPException(status_code=404, detail="User has no workspace")

    result = await db.execute(
        text("""
            SELECT id, content, summary, category, conversation_id, created_at
            FROM ai_memory_embedding
            WHERE workspace_id = :wid AND user_id = :uid
            ORDER BY created_at DESC
            LIMIT :lim
        """),
        {"wid": int(workspace_id), "uid": user_id, "lim": limit},
    )

    rows = [dict(r._mapping) for r in result]
    return {"success": True, "count": len(rows), "data": rows}


# =========================================================
# DELETE A MEMORY
# DELETE /api/v1/memory/{memory_id}
# =========================================================
@router.delete("/{memory_id}")
async def delete_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    """Delete a specific memory entry (only the owner can delete)."""
    user_id = current_user["user_id"]

    result = await db.execute(
        text("""
            DELETE FROM ai_memory_embedding
            WHERE id = :mid AND user_id = :uid
            RETURNING id
        """),
        {"mid": memory_id, "uid": user_id},
    )
    deleted = result.fetchone()
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found or not owned by you")

    await db.commit()
    return {"success": True, "deleted_id": memory_id}
