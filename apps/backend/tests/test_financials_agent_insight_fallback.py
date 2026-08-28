"""
Pure-mock unit tests for the pulso-diario-agent-insight-bridge fallback in
presentation/financials_endpoints.py::get_financials. No real Supabase calls.
"""

from __future__ import annotations

import asyncio

from presentation.financials_endpoints import get_financials


def run(coro):
    return asyncio.run(coro)


AUTHENTICATED_USER = {
    "id": "76680e1f-2943-4235-8501-18b090d59257",
    "email": "cliente@example.com",
    "resolved_user_id": "76680e1f-2943-4235-8501-18b090d59257",
    "resolved_tenant_id": "tenant-1",
}


def _patch_common(monkeypatch, empty_snapshot: bool, insight_tasks):
    import presentation.financials_endpoints as endpoints_module

    snapshot = (
        {"caja_real": 0, "dinero_disponible": 0, "ventas_ayer": 0, "gastos_ayer": 0, "status": "empty"}
        if empty_snapshot
        else {"caja_real": 500_000, "dinero_disponible": 500_000, "ventas_ayer": 0, "gastos_ayer": 0, "status": "healthy"}
    )
    monkeypatch.setattr(
        endpoints_module, "compute_pulso_daily_snapshot", lambda tenant_id, as_of: snapshot
    )

    async def fake_resolve_plan_tier(tenant_id):
        return "freemium"

    monkeypatch.setattr(endpoints_module, "_resolve_plan_tier", fake_resolve_plan_tier)
    monkeypatch.setattr(
        endpoints_module, "list_completed_tasks", lambda **kwargs: insight_tasks
    )
    return endpoints_module


class TestAgentInsightFallback:
    def test_empty_shadow_gl_with_insight_returns_insight(self, monkeypatch):
        insight_result = {
            "caja_real": 750_000,
            "dinero_disponible": 750_000,
            "ventas_ayer": 0,
            "gastos_ayer": 0,
        }
        _patch_common(
            monkeypatch,
            empty_snapshot=True,
            insight_tasks=[{"created_at": "2026-08-28T00:00:00Z", "result": insight_result}],
        )

        snapshot = run(get_financials(user=AUTHENTICATED_USER))

        assert snapshot["status"] == "healthy"
        assert snapshot["source"] == "agent_insight"
        assert snapshot["caja_real"] == 750_000

    def test_empty_shadow_gl_without_insight_stays_empty(self, monkeypatch):
        _patch_common(monkeypatch, empty_snapshot=True, insight_tasks=[])

        snapshot = run(get_financials(user=AUTHENTICATED_USER))

        assert snapshot["status"] == "empty"
        assert "source" not in snapshot

    def test_healthy_shadow_gl_never_consults_insight_fallback(self, monkeypatch):
        endpoints_module = _patch_common(
            monkeypatch,
            empty_snapshot=False,
            insight_tasks=[{"created_at": "2026-08-28T00:00:00Z", "result": {
                "caja_real": 1, "dinero_disponible": 1, "ventas_ayer": 1, "gastos_ayer": 1,
            }}],
        )
        calls = []
        monkeypatch.setattr(
            endpoints_module,
            "list_completed_tasks",
            lambda **kwargs: calls.append(kwargs) or [],
        )

        snapshot = run(get_financials(user=AUTHENTICATED_USER))

        assert snapshot["status"] == "healthy"
        assert snapshot["caja_real"] == 500_000
        assert calls == []

    def test_latest_insight_wins_when_multiple_exist(self, monkeypatch):
        _patch_common(
            monkeypatch,
            empty_snapshot=True,
            insight_tasks=[
                {"created_at": "2026-08-27T00:00:00Z", "result": {
                    "caja_real": 100, "dinero_disponible": 100, "ventas_ayer": 0, "gastos_ayer": 0,
                }},
                {"created_at": "2026-08-28T00:00:00Z", "result": {
                    "caja_real": 999, "dinero_disponible": 999, "ventas_ayer": 0, "gastos_ayer": 0,
                }},
            ],
        )

        snapshot = run(get_financials(user=AUTHENTICATED_USER))

        assert snapshot["caja_real"] == 999
