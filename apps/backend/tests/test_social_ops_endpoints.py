"""
Tests for Social Ops FastAPI endpoints (FASE 4, Slice 4, Tasks 4.4–4.5).

Content Ideas, Lead Reply, Sales Closure, Metrics Analyzer endpoints
against canonical social_*_drafts tables, behind social_ops_canonical feature flag.

Task 4.5: Lead Reply draft enqueued to approval_queue with draft_type='social_reply'
alongside social_reply_drafts insert.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest


class TestSocialOpsFeatureFlag:
    """Feature flag SOCIAL_OPS_CANONICAL gates Social Ops endpoint availability."""

    def test_social_ops_canonical_flag_exists_and_defaults_to_false(self) -> None:
        """Feature flag SOCIAL_OPS_CANONICAL exists in config and defaults to False."""
        from config import settings

        # Flag should exist
        assert hasattr(settings, "SOCIAL_OPS_CANONICAL")
        # Default should be False (n8n is active, FastAPI canonical is off)
        assert settings.SOCIAL_OPS_CANONICAL is False

    def test_social_ops_router_conditional_includes_on_flag(self) -> None:
        """presentation/router.py conditionally includes social_ops_router when flag is ON."""
        # Read the router file and verify it checks SOCIAL_OPS_CANONICAL
        with open("presentation/router.py", "r") as f:
            router_code = f.read()

        # Verify the file imports settings
        assert "from config import settings" in router_code
        # Verify the conditional check exists
        assert "if settings.SOCIAL_OPS_CANONICAL:" in router_code
        # Verify the router is included conditionally
        assert "api_router.include_router(social_ops_router" in router_code

    def test_social_ops_service_has_required_methods(self) -> None:
        """SocialOpsService implements all required methods for Task 4.4."""
        from services.social_ops_service import SocialOpsService

        service = SocialOpsService()

        # Required methods for Task 4.4:
        # - list_ideas: GET /api/v1/agents/social-ops/ideas
        assert hasattr(service, "list_ideas")
        assert callable(service.list_ideas)

        # - get_metrics_dashboard: GET /api/v1/agents/social-ops/metrics
        assert hasattr(service, "get_metrics_dashboard")
        assert callable(service.get_metrics_dashboard)

        # - draft_lead_reply: Lead Reply endpoint
        assert hasattr(service, "draft_lead_reply")
        assert callable(service.draft_lead_reply)

        # - draft_sales_closure: Sales Closure endpoint
        assert hasattr(service, "draft_sales_closure")
        assert callable(service.draft_sales_closure)


class TestLeadReplyApprovalQueueIntegration:
    """Lead Reply draft enqueued to approval_queue with draft_type='social_reply'."""

    @pytest.mark.asyncio
    async def test_draft_lead_reply_enqueues_to_approval_queue_with_social_reply_draft_type(
        self,
    ) -> None:
        """
        When Lead Reply agent proposes a reply, draft is inserted into social_reply_drafts
        AND enqueued to approval_queue with draft_type='social_reply'.
        """
        from services.social_ops_service import SocialOpsService
        from services.approval_queue_service import ApprovalQueueService

        service = SocialOpsService()

        # Create a test lead first
        lead_response = service.ingest_normalized_event(
            {
                "channel": "telegram",
                "actor_handle": "test_user",
                "actor_name": "Test User",
                "text": "Hola, tengo una pregunta sobre DIAN",
                "source_event_id": "test-event-1",
            }
        )
        lead_id = lead_response["lead"]["id"]

        # Mock approval_queue_service.enqueue_draft to capture call, and mock the
        # explicit Cliente Cero tenant resolution done at the call site (no
        # silent default — see approval-queue-tenant-scoping design.md)
        fake_cliente_cero_tenant_id = "e2d30d09-6b96-4ebe-a79a-c6aff7a5df34"
        with patch(
            "services.social_ops_service.ApprovalQueueService.enqueue_draft",
            new=AsyncMock(return_value=(True, None, None)),
        ) as mock_enqueue, patch(
            "services.social_ops_service.resolve_cliente_cero_tenant_id",
            return_value=fake_cliente_cero_tenant_id,
        ):
            # Draft lead reply (now async)
            draft = await service.draft_lead_reply(
                lead_id=lead_id,
                channel="telegram",
                intent="inbound_question",
                actor_handle="taty",
            )

        # Verify draft was created
        assert draft["id"]
        assert draft["status"] == "pending_approval"
        assert draft["type"] == "lead_reply"
        assert draft["lead_id"] == lead_id
        assert draft["channel"] == "telegram"

        # Verify enqueue_draft was called with correct draft_type and the
        # explicitly resolved Cliente Cero tenant_id
        mock_enqueue.assert_awaited_once()
        call_args = mock_enqueue.await_args
        # Args: draft_id, draft_type, journal_entry (payload), memo=""
        call_kwargs = call_args[1] if call_args[1] else {}
        enqueued_draft_type = call_kwargs.get("draft_type") or (call_args[0][1] if len(call_args[0]) > 1 else None)
        assert enqueued_draft_type == "social_reply"
        assert call_kwargs.get("tenant_id") == fake_cliente_cero_tenant_id

    @pytest.mark.asyncio
    async def test_draft_lead_reply_skips_enqueue_when_cliente_cero_unresolved(
        self,
    ) -> None:
        """
        When Cliente Cero's tenant cannot be resolved, the enqueue is skipped
        (logged, not silently defaulted) but the lead reply draft is still
        created and returned.
        """
        from services.social_ops_service import SocialOpsService
        from services.approval_queue_service import ApprovalQueueService

        service = SocialOpsService()
        lead_response = service.ingest_normalized_event(
            {
                "channel": "telegram",
                "actor_handle": "test_user2",
                "actor_name": "Test User 2",
                "text": "Hola, tengo una pregunta sobre DIAN",
                "source_event_id": "test-event-2",
            }
        )
        lead_id = lead_response["lead"]["id"]

        with patch(
            "services.social_ops_service.ApprovalQueueService.enqueue_draft",
            new=AsyncMock(return_value=(True, None, None)),
        ) as mock_enqueue, patch(
            "services.social_ops_service.resolve_cliente_cero_tenant_id",
            return_value=None,
        ):
            draft = await service.draft_lead_reply(
                lead_id=lead_id,
                channel="telegram",
                intent="inbound_question",
                actor_handle="taty",
            )

        assert draft["id"]
        mock_enqueue.assert_not_awaited()


class TestCalendarioBorradoresEndpoints:
    """Router-level tests for the new /calendario and /borradores endpoints."""

    def test_list_calendario_endpoint_returns_items(self) -> None:
        from presentation.social_ops_endpoints import list_calendario
        from services.social_ops_service import get_social_ops_service

        service = get_social_ops_service()
        service.calendario = [
            {"id": 1, "semana": 1, "fecha_publicacion": "2026-07-06", "dia_semana": "Lunes",
             "idea_id": None, "pilar": "CLARIDAD", "formato": "CARRUSEL", "titulo_trabajo": "Post A",
             "status": "PLANIFICADO", "responsable": "Ops", "notas_editoriales": None, "created_at": "2026-07-01"},
        ]

        result = list_calendario(semana=None)

        assert result["items"][0]["id"] == 1

    def test_list_calendario_endpoint_filters_by_semana(self) -> None:
        from presentation.social_ops_endpoints import list_calendario
        from services.social_ops_service import get_social_ops_service

        service = get_social_ops_service()
        service.calendario = [
            {"id": 1, "semana": 1, "fecha_publicacion": "2026-07-06", "dia_semana": "Lunes",
             "idea_id": None, "pilar": "CLARIDAD", "formato": "CARRUSEL", "titulo_trabajo": "Post A",
             "status": "PLANIFICADO", "responsable": "Ops", "notas_editoriales": None, "created_at": "2026-07-01"},
            {"id": 2, "semana": 2, "fecha_publicacion": "2026-07-13", "dia_semana": "Lunes",
             "idea_id": None, "pilar": "ACCION", "formato": "VIDEO_CORTO", "titulo_trabajo": "Post B",
             "status": "DRAFT", "responsable": "Ops", "notas_editoriales": None, "created_at": "2026-07-01"},
        ]

        result = list_calendario(semana=2)

        assert len(result["items"]) == 1
        assert result["items"][0]["semana"] == 2

    def test_list_borradores_endpoint_returns_items(self) -> None:
        from presentation.social_ops_endpoints import list_borradores
        from services.social_ops_service import get_social_ops_service

        service = get_social_ops_service()
        service.contenido = {
            1: {"id": 1, "cal_id": 1, "hook": "Hook 1", "hook_alt_1": None, "hook_alt_2": None,
                "copy_body": "Copy 1", "cta": "CTA 1", "hashtags": "#a", "version": 1,
                "status": "BORRADOR_IA", "qa_humanizacion": False, "fecha_aprobacion": None,
                "aprobado_por": None, "created_at": "2026-07-01"},
        }

        result = list_borradores()

        assert result["items"][0]["id"] == 1

    def test_approve_borrador_endpoint(self) -> None:
        from presentation.social_ops_endpoints import approve_borrador, BorradorApprovalRequest
        from services.social_ops_service import get_social_ops_service

        service = get_social_ops_service()
        service.contenido = {
            1: {"id": 1, "cal_id": 1, "hook": "Hook 1", "hook_alt_1": None, "hook_alt_2": None,
                "copy_body": "Copy 1", "cta": "CTA 1", "hashtags": "#a", "version": 1,
                "status": "BORRADOR_IA", "qa_humanizacion": False, "fecha_aprobacion": None,
                "aprobado_por": None, "created_at": "2026-07-01"},
        }

        result = approve_borrador(1, BorradorApprovalRequest(actor_handle="ops_admin"))

        assert result["ok"] is True
        assert service.contenido[1]["status"] == "APROBADO"

    def test_approve_borrador_endpoint_404_for_unknown_id(self) -> None:
        from fastapi import HTTPException
        from presentation.social_ops_endpoints import approve_borrador, BorradorApprovalRequest
        from services.social_ops_service import get_social_ops_service

        service = get_social_ops_service()
        service.contenido = {}

        try:
            approve_borrador(999, BorradorApprovalRequest(actor_handle="ops_admin"))
            assert False, "expected HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 404

    def test_update_borrador_endpoint(self) -> None:
        from presentation.social_ops_endpoints import update_borrador, BorradorUpdateRequest
        from services.social_ops_service import get_social_ops_service

        service = get_social_ops_service()
        service.contenido = {
            1: {"id": 1, "cal_id": 1, "hook": "Hook 1", "hook_alt_1": None, "hook_alt_2": None,
                "copy_body": "Copy 1", "cta": "CTA 1", "hashtags": "#a", "version": 1,
                "status": "BORRADOR_IA", "qa_humanizacion": False, "fecha_aprobacion": None,
                "aprobado_por": None, "created_at": "2026-07-01"},
        }

        result = update_borrador(1, BorradorUpdateRequest(hook="Nuevo hook"))

        assert result["ok"] is True
        assert service.contenido[1]["hook"] == "Nuevo hook"
        assert service.contenido[1]["status"] == "EDITADO_HUMANO"
