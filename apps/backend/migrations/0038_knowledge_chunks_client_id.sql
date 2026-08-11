-- Migration: Add client_id/source to knowledge_chunks + p_client_id-keyed match RPC overload.
-- Date: 2026-08-11
-- Purpose: taty-whatsapp-renta-sales-capability root cause #2. The repo's own
-- apps/backend/supabase/migrations/20260527_knowledge_chunks.sql already DECLARES a `client_id`
-- column and a `match_knowledge_chunks(query_embedding, p_client_id, match_count)` RPC — but that
-- file's own header says "Apply manually... the application continues to work without this
-- migration applied", and it was never actually run as written. What IS live in production
-- (kpynymwghfwshvcvevxq), verified 2026-08-11, is a different, simpler table with no
-- `client_id`/`source` columns and a different RPC overload:
--   match_knowledge_chunks(query_embedding vector, match_threshold real, match_count integer)
-- Meanwhile services/kb_seeding_service.py::retrieve_similar calls
-- match_knowledge_chunks(query_embedding, p_client_id, match_count) — a signature that does not
-- exist live. Seeding or retrieving today fails outright rather than returning empty. The table
-- has 0 rows live (verified), so this migration touches no existing data.
--
-- This migration is purely additive: new columns with a default, a NEW function overload
-- (Postgres distinguishes by the 2nd argument's type — `real` vs `text` — so this coexists with
-- the live match_threshold-keyed overload without replacing or dropping it).
-- Idempotent: safe to re-run (IF NOT EXISTS / CREATE OR REPLACE throughout).
-- Prerequisites: the live knowledge_chunks table and pgvector extension (both already present).

-- 1) Add the missing columns the code (and the original, never-applied migration) expect.
ALTER TABLE public.knowledge_chunks
    ADD COLUMN IF NOT EXISTS client_id text NOT NULL DEFAULT '__global__';

ALTER TABLE public.knowledge_chunks
    ADD COLUMN IF NOT EXISTS source text;

-- 2) Index for client filtering (mirrors the original file's intent).
CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_client
    ON public.knowledge_chunks(client_id);

-- 3) Dedup safety net matching the original design intent. Only added if no existing rows would
--    violate it (table is empty in production today, but guarded defensively for any environment
--    where it is not).
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'knowledge_chunks_client_content_hash_key'
    ) THEN
        ALTER TABLE public.knowledge_chunks
            ADD CONSTRAINT knowledge_chunks_client_content_hash_key
            UNIQUE (client_id, content_hash);
    END IF;
END $$;

-- 4) NEW RPC overload: the p_client_id-keyed signature retrieve_similar() actually calls.
--    Distinct overload from the live match_threshold-keyed one (different 2nd-arg type) — that
--    overload is untouched by this migration and keeps working for any other caller.
CREATE OR REPLACE FUNCTION public.match_knowledge_chunks(
    query_embedding vector(1536),
    p_client_id text DEFAULT '__global__',
    match_count int DEFAULT 5
)
RETURNS TABLE (
    id uuid,
    source text,
    content text,
    metadata jsonb,
    content_hash text,
    similarity float
)
LANGUAGE sql STABLE AS $$
    SELECT
        kc.id,
        kc.source,
        kc.content,
        kc.metadata,
        kc.content_hash,
        1 - (kc.embedding <=> query_embedding) AS similarity
    FROM public.knowledge_chunks kc
    WHERE kc.client_id = p_client_id
      AND kc.embedding IS NOT NULL
    ORDER BY kc.embedding <=> query_embedding
    LIMIT match_count;
$$;

COMMENT ON COLUMN public.knowledge_chunks.client_id IS
    'Added 2026-08-11 (migration 0038) — reconciles live schema with the never-applied intent of '
    '20260527_knowledge_chunks.sql. Defaults to __global__ for any pre-existing row.';
