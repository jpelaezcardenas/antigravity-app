"""
Knowledge Base Seeding Service - LÍNEA 3

Provides a single retrieval interface that the rest of the app uses, with two
pluggable backends:

  1. pgvector backend  (preferred) — Supabase `knowledge_chunks` table with
     `embedding vector(1536)`. Cosine similarity search via RPC.
  2. in-memory backend (fallback)  — keyword matching against
     KNOWLEDGE_SOURCES dict. Used when Supabase is not configured or the
     migration has not been run.

The service auto-detects which backend to use at first call and caches the
decision. Callers only see `retrieve_similar(query, client_id, top_k)` — they
never care about the backend.

Seeding:
  - `seed_knowledge_base(client_id, chunks, embed_provider="auto")` accepts a
    list of `{source, content, metadata}` dicts.
  - Embedding provider order: OpenAI ada-002 → Gemini → none (store text-only,
    keyword retrieval).
  - Idempotent: upserts by (client_id, source, content_hash).

DIAN seed file:
  - `apps/backend/kb/dian_chunks.json` contains 30-50 curated chunks.
  - Run `python services/kb_seeding_service.py seed-dian` to load (CLI hook).
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Backend detection
# ---------------------------------------------------------------------------

_BACKEND: Optional[str] = None  # "pgvector" | "memory"
_SUPABASE_CLIENT = None


def _detect_backend() -> str:
    """Return active backend. Cached after first call."""
    global _BACKEND, _SUPABASE_CLIENT
    if _BACKEND is not None:
        return _BACKEND

    try:
        from config import settings
        if not (settings.SUPABASE_URL and settings.SUPABASE_KEY):
            logger.info("KB: Supabase credentials not set, using in-memory backend")
            _BACKEND = "memory"
            return _BACKEND
    except Exception as e:
        logger.warning(f"KB: config load failed ({e}), using in-memory backend")
        _BACKEND = "memory"
        return _BACKEND

    try:
        # Use the shared service-role client (core.supabase_client.get_service_supabase),
        # not a raw anon-keyed client built here. `knowledge_chunks`'s RLS policies grant
        # SELECT only to role `authenticated` and INSERT only to `service_role`
        # (match_knowledge_chunks is SECURITY INVOKER, so RLS applies through the RPC too) —
        # an anon-keyed client would silently return zero rows on every read (RLS filters
        # rows rather than erroring on SELECT) and hard-fail on every seed. Found live
        # 2026-08-11 while fixing taty-whatsapp-renta-sales-capability's root cause #2: this
        # is exactly the "seeded successfully, Taty still says she doesn't know" failure mode
        # a raw anon client would have reproduced even after the schema was fixed.
        from core.supabase_client import get_service_supabase
        _SUPABASE_CLIENT = get_service_supabase()
        # Probe table existence (cheap select with limit 0)
        _SUPABASE_CLIENT.table("knowledge_chunks").select("id").limit(1).execute()
        logger.info("KB: pgvector backend active")
        _BACKEND = "pgvector"
    except ImportError:
        logger.info("KB: supabase-py not installed, using in-memory backend")
        _BACKEND = "memory"
    except Exception as e:
        logger.info(f"KB: knowledge_chunks table not ready ({e}), using in-memory backend")
        _BACKEND = "memory"

    return _BACKEND


# ---------------------------------------------------------------------------
# In-memory store (fallback)
# ---------------------------------------------------------------------------

_MEMORY_STORE: Dict[str, List[Dict]] = {}  # client_id → list of chunks


def _seed_memory(client_id: str, chunks: List[Dict]) -> int:
    """Append chunks to the in-memory store. Deduplicates by content_hash."""
    bucket = _MEMORY_STORE.setdefault(client_id, [])
    existing_hashes = {c.get("content_hash") for c in bucket}
    added = 0
    for chunk in chunks:
        h = _content_hash(chunk["content"])
        if h in existing_hashes:
            continue
        bucket.append({**chunk, "content_hash": h})
        added += 1
    logger.info(f"KB[memory]: seeded {added} chunks for {client_id} (total: {len(bucket)})")
    return added


_STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas",
    "de", "del", "en", "para", "por", "con", "sin", "sobre",
    "que", "qué", "cual", "cuál", "como", "cómo", "donde", "dónde",
    "es", "son", "está", "están", "ser", "estar",
    "se", "su", "sus", "y", "o", "a", "al", "no", "si",
    "mi", "mis", "tu", "tus", "yo", "tú",
    "the", "is", "are", "of", "to", "in", "for", "and", "or",
}


def _tokenize(text: str) -> List[str]:
    """Lowercase, strip punctuation, drop stopwords, keep meaningful tokens."""
    import re
    raw = re.findall(r"[a-záéíóúñü0-9]+", text.lower())
    return [t for t in raw if len(t) >= 3 and t not in _STOPWORDS]


def _retrieve_memory(query: str, client_id: str, top_k: int) -> List[Dict]:
    """Keyword retrieval over in-memory store. Falls back to global pool if client_id has no chunks."""
    bucket = _MEMORY_STORE.get(client_id) or _MEMORY_STORE.get("__global__") or []
    query_tokens = set(_tokenize(query))
    if not query_tokens:
        return []

    scored: List[Tuple[int, Dict]] = []
    for chunk in bucket:
        content_tokens = set(_tokenize(chunk.get("content", "")))
        source_tokens = set(_tokenize(chunk.get("source", "")))
        # Score: 2x weight for query tokens appearing in source/topic, 1x in content
        content_hits = len(query_tokens & content_tokens)
        source_hits = len(query_tokens & source_tokens)
        score = content_hits + 2 * source_hits
        if score > 0:
            scored.append((score, chunk))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:top_k]]


# ---------------------------------------------------------------------------
# pgvector backend (preferred)
# ---------------------------------------------------------------------------

def _seed_pgvector(client_id: str, chunks: List[Dict]) -> int:
    """Upsert chunks by (client_id, content_hash). Chunks whose embedding fails are SKIPPED
    entirely rather than upserted with embedding=None.

    Found live 2026-08-11 (taty-whatsapp-renta-sales-capability): ensure_dian_loaded() runs at
    every backend process start (taty_service.py import time) and re-seeds dian_chunks.json into
    pgvector, not just memory. When it ran during a Railway redeploy while both embedding
    providers were unavailable (OpenAI out of credits, Gemini's free quota exhausted by this
    session's own testing), the old code unconditionally included `"embedding": None` in every
    row, and Postgrest's upsert applied that literally — silently overwriting 48 previously
    good, non-null embeddings with NULL, permanently invisible to match_knowledge_chunks'
    `WHERE embedding IS NOT NULL` filter until manually re-seeded. Skipping the row instead means
    an embedding outage degrades to "this seed call adds nothing new" rather than "this seed call
    actively destroys existing good data."
    """
    rows = []
    skipped = 0
    for chunk in chunks:
        embedding = _embed_text(chunk["content"])
        if embedding is None:
            skipped += 1
            continue
        rows.append({
            "client_id": client_id,
            "source": chunk.get("source", "unknown"),
            "content": chunk["content"],
            "content_hash": _content_hash(chunk["content"]),
            "metadata": chunk.get("metadata", {}),
            "embedding": embedding,
        })

    if skipped:
        logger.warning(
            f"KB[pgvector]: skipped {skipped}/{len(chunks)} chunks for {client_id} — embedding "
            "failed (all providers unavailable). Never upserting embedding=None over a possibly "
            "existing good value; re-run seeding once an embedding provider is available."
        )
    if not rows:
        return 0

    # Upsert by (client_id, content_hash)
    result = _SUPABASE_CLIENT.table("knowledge_chunks").upsert(
        rows, on_conflict="client_id,content_hash"
    ).execute()
    n = len(result.data) if result.data else len(rows)
    logger.info(f"KB[pgvector]: upserted {n} chunks for {client_id}")
    return n


def _retrieve_pgvector(query: str, client_id: str, top_k: int) -> List[Dict]:
    query_embedding = _embed_text(query)
    if query_embedding is None:
        # Embedding failed — fall back to memory retrieval at the query layer
        logger.warning("KB[pgvector]: query embedding failed, falling back to memory")
        return _retrieve_memory(query, client_id, top_k)

    # Call Supabase RPC `match_knowledge_chunks(query_embedding, client_id, top_k)`
    try:
        result = _SUPABASE_CLIENT.rpc(
            "match_knowledge_chunks",
            {"query_embedding": query_embedding, "p_client_id": client_id, "match_count": top_k},
        ).execute()
        return result.data or []
    except Exception as e:
        logger.error(f"KB[pgvector]: retrieval RPC failed ({e}), falling back to memory")
        return _retrieve_memory(query, client_id, top_k)


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _embed_text(text: str) -> Optional[List[float]]:
    """Embed text to a 1536-dim vector using text-embedding-3-small, reachable through two providers
    that share the SAME vector space so seeding and querying stay comparable.

    Provider order (taty-whatsapp-renta-sales-capability, 2026-08-12, reworked live):
      1. OpenRouter (openai/text-embedding-3-small) — PRIMARY. Funded by OpenRouter credits, which
         is the point: direct OpenAI credit was exhausted (429 "no credits remaining") and Gemini's
         free daily quota was exceeded (429) at the same time, leaving the KB unfillable. OpenRouter
         proxies OpenAI's own text-embedding-3-small, so its output is the identical space as (2).
      2. Direct OpenAI (text-embedding-3-small) — same model, same space, used when OpenRouter is
         unreachable and the OpenAI account has credit.

    Deliberately NO ada-002 and NO Gemini: those are DIFFERENT embedding spaces, and mixing embedding
    models within one table makes cosine similarity meaningless (a query embedded with model A cannot
    be compared to chunks embedded with model B). Standardizing on 3-small (1536) also keeps the
    column `embedding vector(1536)` unchanged — no migration. Returns None on total failure; the
    caller skips the chunk on seed, and Taty's token-free keyword fallback covers reads.
    """
    import openai
    from config import settings

    # 1. OpenRouter — credit-funded, primary
    try:
        if getattr(settings, "OPENROUTER_API_KEY", None):
            client = openai.OpenAI(
                api_key=settings.OPENROUTER_API_KEY,
                base_url="https://openrouter.ai/api/v1",
            )
            resp = client.embeddings.create(
                model="openai/text-embedding-3-small", input=text
            )
            return resp.data[0].embedding
    except Exception as e:
        logger.debug(f"KB embedding: OpenRouter failed ({e})")

    # 2. Direct OpenAI — identical model/space, used when it has credit
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            client = openai.OpenAI(api_key=api_key)
            resp = client.embeddings.create(model="text-embedding-3-small", input=text)
            return resp.data[0].embedding
    except Exception as e:
        logger.debug(f"KB embedding: OpenAI failed ({e})")

    return None


def _content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def seed_knowledge_base(client_id: str, chunks: List[Dict]) -> Dict:
    """
    Seed chunks for a client. Auto-routes to active backend.

    Args:
        client_id: Client identifier (e.g., "ctx-001", "__global__" for shared DIAN)
        chunks: List of {source: str, content: str, metadata?: dict}

    Returns:
        {backend: str, seeded: int, total_for_client: int}
    """
    if not chunks:
        return {"backend": _detect_backend(), "seeded": 0, "total_for_client": 0}

    backend = _detect_backend()
    if backend == "pgvector":
        seeded = _seed_pgvector(client_id, chunks)
    else:
        seeded = _seed_memory(client_id, chunks)

    total = (
        len(_MEMORY_STORE.get(client_id, []))
        if backend == "memory"
        else seeded  # pgvector returns inserted count
    )
    return {"backend": backend, "seeded": seeded, "total_for_client": total}


def retrieve_similar(query: str, client_id: str, top_k: int = 5) -> List[Dict]:
    """
    Retrieve chunks most relevant to query. Auto-routes to active backend.

    Returns chunks of shape: {source, content, metadata?, content_hash}
    Falls back to "__global__" client_id pool if specific client has no chunks.
    """
    backend = _detect_backend()
    if backend == "pgvector":
        results = _retrieve_pgvector(query, client_id, top_k)
        if not results:
            results = _retrieve_pgvector(query, "__global__", top_k)
        return results
    else:
        results = _retrieve_memory(query, client_id, top_k)
        if not results:
            results = _retrieve_memory(query, "__global__", top_k)
        return results


def get_backend_status() -> Dict:
    """For health checks / debug endpoints."""
    backend = _detect_backend()
    return {
        "backend": backend,
        "memory_clients": list(_MEMORY_STORE.keys()) if backend == "memory" else [],
        "memory_total_chunks": sum(len(v) for v in _MEMORY_STORE.values()) if backend == "memory" else None,
    }


def load_dian_seed() -> int:
    """
    Load the curated DIAN seed file into the global pool.
    Idempotent (deduplicates by content_hash).
    """
    seed_path = Path(__file__).resolve().parent.parent / "kb" / "dian_chunks.json"
    if not seed_path.exists():
        logger.warning(f"KB: DIAN seed file not found at {seed_path}")
        return 0
    with seed_path.open(encoding="utf-8") as f:
        chunks = json.load(f)
    result = seed_knowledge_base("__global__", chunks)
    logger.info(f"KB: DIAN seed loaded — backend={result['backend']}, seeded={result['seeded']}")
    return result["seeded"]


# Auto-load DIAN seed at import time if not yet loaded
_DIAN_LOADED = False


def ensure_dian_loaded() -> None:
    global _DIAN_LOADED
    if _DIAN_LOADED:
        return
    try:
        load_dian_seed()
        _DIAN_LOADED = True
    except Exception as e:
        logger.warning(f"KB: DIAN auto-load failed ({e})")


if __name__ == "__main__":
    # CLI: `python services/kb_seeding_service.py seed-dian`
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "seed-dian":
        n = load_dian_seed()
        print(f"Seeded {n} DIAN chunks (backend={_detect_backend()})")
    else:
        status = get_backend_status()
        print(json.dumps(status, indent=2))
