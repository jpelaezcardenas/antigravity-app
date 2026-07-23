"""
Taty Contadora - REST API endpoints.

Exposes Taty fiscal advisor service to:
- Dashboard (TatyView.tsx)
- Telegram webhook
- Future: WhatsApp, email, etc.
"""

from fastapi import APIRouter, Query, HTTPException, status, Header, Body, Depends
from pydantic import BaseModel, Field
from typing import List, Optional
import logging

from services.taty_service import get_taty_service
from core.deps import get_current_user, _STAGING_USER
from core.supabase_client import get_supabase

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["taty-contadora"],
)  # prefix handled by router.py include_router()


async def _resolve_cliente_cero_tenant_id() -> str:
    """Resolve the Cliente Cero tenant ID from Supabase."""
    supabase = get_supabase()
    result = (
        supabase.table("tenants")
        .select("id")
        .eq("is_cliente_cero", True)
        .single()
        .execute()
    )
    return result.data["id"]


# ============================================================================
# Request/Response Models
# ============================================================================

class TatyAskRequest(BaseModel):
    """Request to Taty for a fiscal question."""
    company_id: Optional[str] = Field(
        None,
        description=(
            "Deprecated and ignored for tenant resolution. The caller's tenant is "
            "resolved from the authenticated session (see get_current_user), never "
            "from this field. Kept optional so existing external callers that still "
            "send it don't get a 422."
        ),
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
    error_code: Optional[str] = Field(
        None,
        description="Set when the request could not be answered normally, e.g. 'tenant_not_resolved'"
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
async def ask_taty(
    request: TatyAskRequest = Body(...),
    x_hermes_profile: Optional[str] = Header(None),
    user: dict = Depends(get_current_user),
) -> TatyAskResponse:
    """
    Ask Taty Contadora a fiscal question.

    **Query Alternative** (for dashboard GET):
    ```
    GET /api/v1/agents/taty/ask?question=¿Cuál es el UVT?
    ```

    **Headers:**
    - X-Hermes-Profile: Profile name (e.g., "taty-v1") for Hermes-based LLM routing

    **Auth / tenant resolution (per-tenant-client-access, taty-per-tenant-profiles):**
    - Authenticated caller with a resolved tenant -> answers scoped to THEIR OWN
      tenant. Any `company_id` in the request body is ignored for resolution —
      it can never be used to read another tenant's profile.
    - Unauthenticated/local-dev caller (AUTH_ENFORCED=False, no token — the
      permissive staging identity) -> Cliente Cero, preserving existing
      dashboard/local-dev behavior.
    - Authenticated caller whose tenant did NOT resolve -> an in-band
      `error_code="tenant_not_resolved"` response. Never falls back to
      Cliente Cero here — that would leak Contexia's own data to an unwired
      client login.

    **Behavior:**
    - Anonymizes PII before sending to LLM (SOSP rule)
    - Retrieves relevant DIAN/Contexia knowledge
    - Calls LLM with failover chain
    - Returns citations and confidence
    - Flags for human review if needed

    **Example:**
    ```json
    {
      "question": "¿Cuál es el UVT para 2026?",
      "channel": "dashboard"
    }
    ```

    Returns: TatyAskResponse with answer, citations, latency, confidence, escalation flag.
    """
    try:
        resolved_tenant_id = user.get("resolved_tenant_id")
        if resolved_tenant_id:
            tenant_id = resolved_tenant_id
        elif user.get("id") == _STAGING_USER["id"]:
            tenant_id = await _resolve_cliente_cero_tenant_id()
        else:
            return TatyAskResponse(
                answer="Tu cuenta aún no está vinculada a una empresa en Contexia. Contacta a soporte.",
                citations=[],
                latency_ms=0,
                confidence=0.0,
                requires_human_review=True,
                error_code="tenant_not_resolved",
            )

        logger.info(f"Taty.ask() from {request.channel}: tenant_id={tenant_id}, profile={x_hermes_profile}")

        # Get Taty service
        taty = get_taty_service()

        # Call service with optional profile from Hermes
        response = taty.ask(
            tenant_id=tenant_id,
            question=request.question,
            channel=request.channel,
            conversation_id=request.conversation_id,
            user_id=request.user_id,
            hermes_profile=x_hermes_profile,
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
    question: str = Query(..., description="Fiscal question"),
    channel: str = Query("dashboard", description="Channel"),
    conversation_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    company_id: Optional[str] = Query(
        None,
        description="Deprecated and ignored for tenant resolution — see TatyAskRequest.company_id",
    ),
    x_hermes_profile: Optional[str] = Header(None),
    user: dict = Depends(get_current_user),
) -> TatyAskResponse:
    """GET alternative for dashboard integration (CORS-friendly).

    Shares the same auth + tenant-resolution logic as the POST handler
    (`ask_taty`) — it just builds the request body from query params.
    """
    request = TatyAskRequest(
        company_id=company_id,
        question=question,
        channel=channel,
        conversation_id=conversation_id,
        user_id=user_id,
    )
    return await ask_taty(request, x_hermes_profile=x_hermes_profile, user=user)


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
