"""Tests for Taty's `ask()` tenant-scoping (taty-per-tenant-profiles, task 2).

Covers:
- `_build_prompt` never asserts a régimen the tenant profile doesn't actually
  have (design D1 / GROUND_TRUTH compliance): the régimen clause is omitted
  when `profile["regimen"]` is `None`, and included when it is set.
- `_retrieve_chunks` keys `retrieve_similar(client_id=...)` off
  `profile["kb_client_id"]` (design D7), trusting kb_seeding_service's own
  `"__global__"` fallback rather than reimplementing it in taty_service.
- Cliente Cero's tenant profile (`kb_client_id == "ctx-001"`) results in
  `retrieve_similar` being called with `client_id="ctx-001"`.

Follows the hermetic-mock convention used by test_taty_tenant_profiles.py:
no live Supabase/LLM network calls.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.taty_service import TatyAgentService, DEFAULT_PROFILE


def _profile(**overrides) -> dict:
    """Build a minimal resolved tenant profile dict, as `_get_tenant_profile`
    would return it, with sane defaults overridable per test."""
    base = {
        **DEFAULT_PROFILE,
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "nit": "900.111.222-3",
        "nombre_empresa": "Hermetic Test Tenant SAS",
        "company_id": None,
        "kb_client_id": "11111111-1111-1111-1111-111111111111",
    }
    base.update(overrides)
    return base


class TestBuildPromptRegimenOmission:
    def test_regimen_none_omits_regimen_clause(self):
        profile = _profile(regimen=None)
        chunks = [{"text": "El IVA general es del 19%.", "source": "Estatuto Tributario"}]

        prompt = TatyAgentService()._build_prompt("¿Cuál es el IVA?", chunks, profile)

        assert "régimen" not in prompt.lower()
        assert "regimen" not in prompt.lower()

    def test_regimen_set_includes_regimen_clause(self):
        profile = _profile(regimen="Régimen Común")
        chunks = [{"text": "El IVA general es del 19%.", "source": "Estatuto Tributario"}]

        prompt = TatyAgentService()._build_prompt("¿Cuál es el IVA?", chunks, profile)

        assert "régimen" in prompt.lower()
        assert "Régimen Común" in prompt


class TestRetrieveChunksKbClientIdKeying:
    def test_retrieve_chunks_passes_through_kb_client_id_to_retrieve_similar(self):
        """Tenant with a dedicated (possibly empty-seeded) kb_client_id: taty_service
        passes it through as-is and trusts kb_seeding_service.retrieve_similar's own
        internal '__global__' fallback (design D7) — no special-case logic here."""
        profile = _profile(kb_client_id="22222222-2222-2222-2222-222222222222")

        with patch("services.taty_service.retrieve_similar", return_value=[]) as mock_retrieve:
            TatyAgentService()._retrieve_chunks("¿Cuál es el UVT?", profile)

        mock_retrieve.assert_called_once()
        _, kwargs = mock_retrieve.call_args
        assert kwargs["client_id"] == "22222222-2222-2222-2222-222222222222"

    def test_cliente_cero_profile_retrieves_with_ctx_001_client_id(self):
        profile = _profile(kb_client_id="ctx-001", company_id="ctx-001")

        with patch("services.taty_service.retrieve_similar", return_value=[]) as mock_retrieve:
            TatyAgentService()._retrieve_chunks("¿Cuál es la Matriz Financiera?", profile)

        mock_retrieve.assert_called_once()
        _, kwargs = mock_retrieve.call_args
        assert kwargs["client_id"] == "ctx-001"


class TestAskUsesTenantProfileDirectly:
    def test_unknown_tenant_returns_tenant_not_found_error_code(self):
        service = TatyAgentService()
        with patch.object(service, "_get_tenant_profile", return_value=None) as mock_resolve:
            response = service.ask(tenant_id="unresolvable-tenant", question="¿Cuál es el IVA?")

        mock_resolve.assert_called_once_with("unresolvable-tenant")
        assert response["error_code"] == "tenant_not_found"

    def test_resolved_tenant_calls_get_tenant_profile_not_get_agent_profile(self):
        service = TatyAgentService()
        assert not hasattr(service, "_get_agent_profile"), (
            "_get_agent_profile must be fully removed in task 2 — ask() calls "
            "_get_tenant_profile directly (design D5)."
        )

        profile = _profile(regimen=None)
        llm_response = MagicMock()
        llm_response = "Respuesta de prueba"

        with patch.object(service, "_get_tenant_profile", return_value=profile) as mock_resolve, \
             patch("services.taty_service.retrieve_similar", return_value=[]), \
             patch("services.taty_service.get_llm_engine") as mock_get_engine:
            mock_engine = MagicMock()
            mock_engine.get_ai_response_with_profile.return_value = llm_response
            mock_get_engine.return_value = mock_engine

            response = service.ask(tenant_id=profile["tenant_id"], question="¿Cuál es el IVA?")

        mock_resolve.assert_called_once_with(profile["tenant_id"])
        assert response["answer"] == llm_response
