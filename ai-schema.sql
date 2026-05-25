-- ════════════════════════════════════════════════════════════════════════════════
-- Lemonmaxx AI Engine — Database Schema
-- ════════════════════════════════════════════════════════════════════════════════
--
-- All AI-related tables in one file.
-- Run: PGPASSWORD=admin psql -h 127.0.0.1 -U postgres -d lemonmaxx_db -f ai-schema.sql
--
-- Prerequisites:
--   - workspace(id) and "user"(id) tables must exist
--   - pgvector extension: CREATE EXTENSION IF NOT EXISTS vector;
--
-- Tables:
--   1. ai_conversation     — Chat session index
--   2. ai_message           — Chat messages (permanent, deduped)
--   3. ai_memory_embedding  — Semantic memory (pgvector 384-dim)
--   4. ai_prompts           — Custom system prompts per user
-- ════════════════════════════════════════════════════════════════════════════════

-- Ensure pgvector extension exists
CREATE EXTENSION IF NOT EXISTS vector;

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. AI Chat — Conversations
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ai_conversation (
    id              VARCHAR(64) PRIMARY KEY,
    workspace_id    BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    title           TEXT DEFAULT '',
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fast lookup: list conversations for a user, newest first
CREATE INDEX IF NOT EXISTS idx_ai_conversation_user
    ON ai_conversation(workspace_id, user_id, updated_at DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. AI Chat — Messages
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ai_message (
    id              BIGSERIAL PRIMARY KEY,
    conversation_id VARCHAR(64) NOT NULL REFERENCES ai_conversation(id) ON DELETE CASCADE,
    workspace_id    BIGINT NOT NULL,
    user_id         BIGINT NOT NULL,
    role            VARCHAR(10) NOT NULL,     -- 'user' | 'assistant'
    content         TEXT NOT NULL,
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Deduplication: prevents duplicate messages in same conversation
    UNIQUE(conversation_id, role, created_at)
);

-- Fast lookup: get messages for a conversation, ordered by time
CREATE INDEX IF NOT EXISTS idx_ai_message_conv
    ON ai_message(conversation_id, created_at);

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Semantic Memory — pgvector Embeddings
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ai_memory_embedding (
    id              BIGSERIAL PRIMARY KEY,
    workspace_id    BIGINT NOT NULL REFERENCES workspace(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,                   -- Original text (question + answer)
    summary         TEXT,                            -- First 200 chars for display
    category        VARCHAR(30) DEFAULT 'insight',   -- 'conversation', 'insight', 'preference'
    embedding       vector(384) NOT NULL,            -- all-MiniLM-L6-v2 (local model)
    conversation_id VARCHAR(64),                     -- Source conversation
    metadata        JSONB DEFAULT '{}',              -- Extra context (tool names, dates)
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- HNSW index for fast cosine similarity search
CREATE INDEX IF NOT EXISTS idx_ai_memory_embedding_vector
    ON ai_memory_embedding USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Tenant isolation + user filtering
CREATE INDEX IF NOT EXISTS idx_ai_memory_embedding_ws_user
    ON ai_memory_embedding (workspace_id, user_id);

-- Category filtering
CREATE INDEX IF NOT EXISTS idx_ai_memory_embedding_category
    ON ai_memory_embedding (workspace_id, category);

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Custom System Prompts
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS ai_prompts (
    id              SERIAL PRIMARY KEY,
    workspace_id    INTEGER NOT NULL,
    user_id         INTEGER NOT NULL,
    name            TEXT NOT NULL,                    -- Prompt name/label
    content         TEXT NOT NULL,                    -- Full prompt text
    created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Fast lookup: prompts for a user in a workspace
CREATE INDEX IF NOT EXISTS idx_ai_prompts_user
    ON ai_prompts(workspace_id, user_id);
