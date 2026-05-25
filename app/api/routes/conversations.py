# app/api/routes/conversations.py

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from app.models.conversation import Conversation
from app.models.message import Message

from app.config.database import get_db

from app.config.logging import get_logger


router = APIRouter()

logger = get_logger("conversation-routes")


# =========================================================
# LIST CONVERSATIONS
# =========================================================
@router.get("/")
async def list_conversations(
    workspace_id: int,
    db: AsyncSession = Depends(get_db),
):

    query = (
        select(Conversation)
        .where(
            Conversation.workspace_id
            == workspace_id
        )
        .order_by(
            Conversation.updated_at.desc()
        )
    )

    result = await db.execute(query)

    conversations = result.scalars().all()

    return {
        "success": True,
        "count": len(conversations),
        "data": conversations,
    }


# =========================================================
# GET CONVERSATION
# =========================================================
@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):

    conversation_query = (
        select(Conversation)
        .where(
            Conversation.id == conversation_id
        )
    )

    conversation_result = await db.execute(
        conversation_query
    )

    conversation = (
        conversation_result.scalar_one_or_none()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    messages_query = (
        select(Message)
        .where(
            Message.conversation_id
            == conversation_id
        )
        .order_by(
            Message.created_at.asc()
        )
    )

    messages_result = await db.execute(
        messages_query
    )

    messages = messages_result.scalars().all()

    return {
        "success": True,
        "conversation": conversation,
        "messages": messages,
    }


# =========================================================
# DELETE CONVERSATION
# =========================================================
@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
):

    query = (
        select(Conversation)
        .where(
            Conversation.id == conversation_id
        )
    )

    result = await db.execute(query)

    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found"
        )

    await db.delete(conversation)

    await db.commit()

    return {
        "success": True,
        "message": "Conversation deleted"
    }