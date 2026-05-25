# app/models/memory.py
#
# Maps to the ai_memory_embedding table defined in ai-schema.sql.
# Uses pgvector's Vector column type for native ANN search.
# The old ai_memory table (JSON embeddings) is no longer used.

from sqlalchemy import BigInteger, Text, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.config.database import Base
from app.config.settings import settings


class Memory(Base):
    """Semantic memory row backed by pgvector HNSW index."""

    __tablename__ = "ai_memory_embedding"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)

    workspace_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    user_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    content: Mapped[str] = mapped_column(Text, nullable=False)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 'conversation' | 'insight' | 'preference'
    category: Mapped[str] = mapped_column(String(30), default="conversation")

    # 384-dim all-MiniLM-L6-v2 vector
    embedding: Mapped[list] = mapped_column(
        Vector(settings.EMBEDDING_DIMS), nullable=False
    )

    conversation_id: Mapped[str | None] = mapped_column(String(64), nullable=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
