"""
Tests for auth-gating agents_endpoints.py (agent-endpoints-real-tenant-filtering, Stage 1).

Before this change, every route in this file had ZERO auth — any anonymous caller could
invoke pure-LLM analysis/decision endpoints or the orchestrator demo. None of these routes
touch the database, so this change adds only an identity requirement
(`Depends(get_current_user)`), no tenant parameter.

Verifies, for each route function:
  1. Its signature requires a `user` parameter bound to `Depends(get_current_user)` — the
     structural guarantee that FastAPI cannot dispatch the route without resolving identity
     first.
  2. The orchestrator demo's response still contains `"mode": "demo"` and its illustrative
     note, unchanged, once called with a resolved user.
"""

import inspect

import fastapi

from presentation import agents_endpoints
from core.deps import get_current_user, _STAGING_USER


ROUTE_FUNCTIONS = [
    agents_endpoints.social_generate_content,
    agents_endpoints.pulso_analyze,
    agents_endpoints.centinela_monitor,
    agents_endpoints.centinela_decide,
    agents_endpoints.compliance_audit,
    agents_endpoints.full_pipeline,
    agents_endpoints.get_task_info,
]


def _user_dependency_default(fn):
    """Return the Depends() default for the `user` parameter, or None if absent."""
    params = inspect.signature(fn).parameters
    user_param = params.get("user")
    if user_param is None:
        return None
    return user_param.default


class TestAgentsEndpointsRequireAuth:
    def test_every_route_requires_get_current_user(self):
        for fn in ROUTE_FUNCTIONS:
            default = _user_dependency_default(fn)
            assert isinstance(default, fastapi.params.Depends), (
                f"{fn.__name__} has no `user: dict = Depends(get_current_user)` parameter"
            )
            assert default.dependency is get_current_user, (
                f"{fn.__name__}'s `user` dependency is not get_current_user"
            )


class TestOrchestratorDemoUnchanged:
    def test_full_pipeline_still_returns_demo_mode(self):
        import asyncio

        request = agents_endpoints.FullPipelineRequest(
            company_url="https://example.com",
            campaign_objective="lead-gen",
            budget=1000.0,
            company_id="company-1",
        )
        response = asyncio.run(
            agents_endpoints.full_pipeline(request=request, user=dict(_STAGING_USER))
        )
        assert response["mode"] == "demo"
        assert "not actually executed" in response["note"]
