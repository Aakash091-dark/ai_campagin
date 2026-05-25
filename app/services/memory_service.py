import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.memory import Memory
from pgvector.sqlalchemy import Vector
from sentence_transformers import SentenceTransformer

# Load a local sentence transformer model for embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

class MemoryService:
    @staticmethod
    async def get_embedding(text: str) -> list[float]:
        # Encode text to get embedding
        return model.encode(text).tolist()

    @staticmethod
    async def store_memory(
        db: AsyncSession,
        workspace_id: int,
        user_id: int,
        content: str,
        category: str = "conversation",
        conversation_id: str = None,
        summary: str = None
    ) -> Memory:
        embedding = await MemoryService.get_embedding(content)
        
        memory = Memory(
            workspace_id=workspace_id,
            user_id=user_id,
            content=content,
            category=category,
            embedding=embedding,
            conversation_id=conversation_id,
            summary=summary or content[:200]
        )
        db.add(memory)
        await db.commit()
        await db.refresh(memory)
        return memory

    @staticmethod
    async def store_conversation_memory(db: AsyncSession, workspace_id: int, user_id: int, content: str, conversation_id: str):
        return await MemoryService.store_memory(db, workspace_id, user_id, content, category="conversation", conversation_id=conversation_id)

    @staticmethod
    async def store_campaign_context(db: AsyncSession, workspace_id: int, user_id: int, context_data: str):
        return await MemoryService.store_memory(db, workspace_id, user_id, context_data, category="insight")

    @staticmethod
    async def semantic_search(
        db: AsyncSession,
        workspace_id: int,
        user_id: int,
        query: str,
        category: str = None,
        limit: int = 5
    ):
        query_embedding = await MemoryService.get_embedding(query)
        
        stmt = select(Memory).where(
            Memory.workspace_id == workspace_id,
            Memory.user_id == user_id
        )
        
        if category:
            stmt = stmt.where(Memory.category == category)
            
        # Order by cosine similarity
        stmt = stmt.order_by(Memory.embedding.cosine_distance(query_embedding)).limit(limit)
        
        result = await db.execute(stmt)
        return result.scalars().all()
