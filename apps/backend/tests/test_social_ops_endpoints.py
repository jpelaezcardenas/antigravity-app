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

        # Mock approval_queue_service.enqueue_draft to capture call
        with patch(
            "services.social_ops_service.ApprovalQueueService.enqueue_draft",
            new=AsyncMock(return_value=(True, None, None)),
        ) as mock_enqueue:
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

        # Verify enqueue_draft was called with correct draft_type
        mock_enqueue.assert_awaited_once()
        call_args = mock_enqueue.await_args
        # Args: draft_id, draft_type, journal_entry (payload), memo=""
        call_kwargs = call_args[1] if call_args[1] else {}
        enqueued_draft_type = call_kwargs.get("draft_type") or (call_args[0][1] if len(call_args[0]) > 1 else None)
        assert enqueued_draft_type == "social_reply"
