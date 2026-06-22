"""
Tests for Social Ops FastAPI endpoints (FASE 4, Slice 4, Task 4.4).

Content Ideas, Lead Reply, Sales Closure, Metrics Analyzer endpoints
against canonical social_*_drafts tables, behind social_ops_canonical feature flag.
"""

from __future__ import annotations

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
