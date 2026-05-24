"""
Taty Contadora - REST API endpoints.

Exposes Taty fiscal advisor service to:
- Dashboard (TatyView.tsx)
- Telegram webhook
- Future: WhatsApp, email, etc.
"""

from fastapi import APIRouter, Query, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from services.taty_service import get_taty_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["taty-contadora"],
)  # prefix handled by router.py include_router()


# ============================================================================
# Request/Response Models
# ============================================================================

class TatyAskRequest(BaseModel):
    """Request to Taty for a fiscal question."""
    company_id: str = Field(
        ...,
        description="Client identifier (e.g., 'ctx-001', 'ferez-001')"
    )
    question: str = Field(
        ...,
        description="Fiscal question (e.g., '¿Cuál es el UVT 2026?')",
        min_length=5,
        max_length=1000
    )
    channel: str = Field(
        "dashboard",
        description="Channel: 'telegram', 'dashboard', 'whatsapp'"
    )
    conversation_id: Optional[str] = Field(
        None,
        description="For multi-turn conversations"
    )
    user_id: Optional[str] = Field(
        None,
        description="User identifier for audit logging"
    )


class Citation(BaseModel):
    """A citation source for the answer."""
    source: str = Field(
        ...,
        description="Source name (e.g., 'Normograma DIAN')"
    )
    fragment: str = Field(
        ...,
        description="Relevant fragment from the source"
    )


class TatyAskResponse(BaseModel):
    """Response from Taty with fiscal advice."""
    answer: str = Field(
        ...,
        description="Fiscal advice in Spanish"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="Sources cited in the answer"
    )
    latency_ms: int = Field(
        ...,
        description="Response time in milliseconds"
    )
    confidence: float = Field(
        ...,
        description="Confidence score 0-1"
    )
    requires_human_review: bool = Field(
        False,
        description="Flag if human CFO should review"
    )
    result: Optional[str] = Field(
        None,
        description="Backward compat alias for 'answer'"
    )


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/ask",
    response_model=TatyAskResponse,
    summary="Ask Taty a fiscal question",
    description="Get fiscal advice from Taty contadora with RAG, failover LLM, and client-specific config."
)
async def ask_taty(request: TatyAskRequest) -> TatyAskResponse:
    """
    Ask Taty Contadora a fiscal question.

    **Query Alternative** (for dashboard GET):
    ```
    GET /api/v1/agents/taty/ask?company_id=ctx-001&question=¿Cuál es el UVT?
    ```

    **Behavior:**
    - Anonymizes PII before sending to LLM (SOSP rule)
    - Retrieves relevant DIAN/Contexia knowledge
    - Calls LLM with failover chain
    - Returns citations and confidence
    - Flags for human review if needed

    **Example:**
    ```json
    {
      "company_id": "ctx-001",
      "question": "¿Cuál es el UVT para 2026?",
      "channel": "dashboard"
    }
    ```

    Returns: TatyAskResponse with answer, citations, latency, confidence, escalation flag.
    """
    try:
        logger.info(f"Taty.ask() from {request.channel}: company_id={request.company_id}")

        # Get Taty service
        taty = get_taty_service()

        # Call service
        response = taty.ask(
            company_id=request.company_id,
            question=request.question,
            channel=request.channel,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
        )

        # Log successful call
        logger.info(f"Taty response OK: latency={response['latency_ms']}ms, "
                   f"requires_review={response['requires_human_review']}")

        return TatyAskResponse(**response)

    except Exception as e:
        logger.error(f"Error in ask_taty: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calling Taty service"
        )


@router.get(
    "/ask",
    response_model=TatyAskResponse,
    summary="Ask Taty a fiscal question (GET)",
)
async def ask_taty_get(
    company_id: str = Query(..., description="Client ID"),
    question: str = Query(..., description="Fiscal question"),
    channel: str = Query("dashboard", description="Channel"),
    conversation_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
) -> TatyAskResponse:
    """GET alternative for dashboard integration (CORS-friendly)."""
    request = TatyAskRequest(
        company_id=company_id,
        question=question,
        channel=channel,
        conversation_id=conversation_id,
        user_id=user_id,
    )
    return await ask_taty(request)


@router.get(
    "/health",
    summary="Health check",
)
async def taty_health():
    """Check if Taty service is ready."""
    try:
        taty = get_taty_service()
        return {
            "status": "ok",
            "service": "taty",
            "ready": True
        }
    except Exception as e:
        logger.error(f"Taty health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Taty service not ready"
        )
