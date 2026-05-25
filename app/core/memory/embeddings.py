# app/core/memory/embeddings.py

from sentence_transformers import (
    SentenceTransformer
)

from app.config.settings import settings

from app.config.logging import get_logger


logger = get_logger("embeddings")


# =========================================================
# LOAD MODEL
# =========================================================
embedding_model = SentenceTransformer(
    settings.AI_EMBEDDING_MODEL
)


# =========================================================
# GENERATE EMBEDDING
# =========================================================
async def generate_embedding(
    text: str
):

    cleaned_text = text[
        : settings.MAX_EMBED_CHARS
    ]

    embedding = embedding_model.encode(
        cleaned_text
    )

    return embedding.tolist()