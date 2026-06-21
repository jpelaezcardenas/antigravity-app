-- Migration: knowledge_chunks for pgvector RAG
-- Date: 2026-05-27
-- Purpose: Replace in-memory KB with Supabase pgvector. Schema designed so that
--          kb_seeding_service.py probes the table; if it doesn't exist, the
--          service falls back to in-memory mode automatically.
--
-- Apply manually in Supabase SQL editor (or via supabase CLI) when ready.
-- The application continues to work without this migration applied.

-- 1) Ensure pgvector extension is available
create extension if not exists vector;

-- 2) knowledge_chunks table
create table if not exists public.knowledge_chunks (
    id uuid primary key default gen_random_uuid(),
    client_id text not null,                    -- "ctx-001", "ferez-001", or "__global__" for shared DIAN
    source text not null,                       -- "Resolución DIAN 238/2025" etc.
    content text not null,                      -- The chunk text (≤2000 chars recommended)
    content_hash text not null,                 -- sha256(content)[:16] for dedup
    metadata jsonb default '{}'::jsonb,         -- {topic, year, norma, etc.}
    embedding vector(1536),                     -- OpenAI ada-002 / Gemini embedding-001 dimension
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (client_id, content_hash)
);

-- 3) Index for client filtering
create index if not exists idx_knowledge_chunks_client
    on public.knowledge_chunks(client_id);

-- 4) IVFFlat index for cosine similarity search (built lazily; populate then run REINDEX)
create index if not exists idx_knowledge_chunks_embedding
    on public.knowledge_chunks
    using ivfflat (embedding vector_cosine_ops)
    with (lists = 100);

-- 5) RPC: match chunks by cosine similarity, optionally scoped to a client
create or replace function public.match_knowledge_chunks(
    query_embedding vector(1536),
    p_client_id text default '__global__',
    match_count int default 5
)
returns table (
    id uuid,
    source text,
    content text,
    metadata jsonb,
    content_hash text,
    similarity float
)
language sql stable as $$
    select
        kc.id,
        kc.source,
        kc.content,
        kc.metadata,
        kc.content_hash,
        1 - (kc.embedding <=> query_embedding) as similarity
    from public.knowledge_chunks kc
    where kc.client_id = p_client_id
      and kc.embedding is not null
    order by kc.embedding <=> query_embedding
    limit match_count;
$$;

-- 6) RLS (open for service role; tighten when client tenants are introduced)
alter table public.knowledge_chunks enable row level security;

create policy "service role full access on knowledge_chunks"
    on public.knowledge_chunks
    for all
    using (true)
    with check (true);
