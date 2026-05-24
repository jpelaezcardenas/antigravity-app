"""
Knowledge Base REST endpoints.

Exposes:
  - POST /kb/seed         Seed chunks for a client (or __global__)
  - GET  /kb/status       Backend status + chunk counts
  - POST /kb/seed-dian    Idempotent load of the curated DIAN seed file
"""

from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
import logging

from services.kb_seeding_service import (
    seed_knowledge_base,
    load_dian_seed,
    get_backend_status,
    retrieve_similar,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["knowledge-base"])


class KBChunk(BaseModel):
    source: str = Field(..., description="Citable source name")
    content: str = Field(..., min_length=10, max_length=8000)
    metadata: Optional[Dict] = Field(default_factory=dict)


class KBSeedRequest(BaseModel):
    client_id: str = Field(..., description="Client ID or '__global__' for shared DIAN pool")
    chunks: List[KBChunk]


class KBSeedResponse(BaseModel):
    backend: str
    seeded: int
    total_for_client: int


class KBSearchRequest(BaseModel):
    client_id: str
    query: str = Field(..., min_length=3)
    top_k: int = Field(5, ge=1, le=20)


@router.post(
    "/seed",
    response_model=KBSeedResponse,
    summary="Seed knowledge chunks for a client",
)
async def seed(request: KBSeedRequest) -> KBSeedResponse:
    try:
        chunks_dicts = [c.dict() for c in request.chunks]
        result = seed_knowledge_base(request.client_id, chunks_dicts)
        return KBSeedResponse(**result)
    except Exception as e:
        logger.error(f"KB seed failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Seed failed: {e}")


@router.post(
    "/seed-dian",
    response_model=KBSeedResponse,
    summary="Load curated DIAN seed file (idempotent)",
)
async def seed_dian() -> KBSeedResponse:
    try:
        seeded = load_dian_seed()
        status_info = get_backend_status()
        return KBSeedResponse(
            backend=status_info["backend"],
            seeded=seeded,
            total_for_client=status_info.get("memory_total_chunks") or seeded,
        )
    except Exception as e:
        logger.error(f"KB seed-dian failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"DIAN seed failed: {e}")


@router.get(
    "/status",
    summary="KB backend status + chunk counts",
)
async def kb_status():
    return get_backend_status()


@router.post(
    "/search",
    summary="Retrieve similar chunks (debug/eval endpoint)",
)
async def kb_search(request: KBSearchRequest):
    results = retrieve_similar(request.query, request.client_id, request.top_k)
    return {"results": results, "count": len(results)}
