"""
Unit tests for kb_seeding_service.

These tests exercise the in-memory backend path (pgvector is exercised via
integration tests when SUPABASE_URL is set, gated by RUN_KB_PGVECTOR=1).
"""

from __future__ import annotations

import os
import pytest

from services import kb_seeding_service as kb


@pytest.fixture(autouse=True)
def _reset_store():
    """Wipe in-memory state between tests."""
    kb._MEMORY_STORE.clear()
    kb._BACKEND = "memory"  # force memory backend regardless of env
    kb._SUPABASE_CLIENT = None
    yield
    kb._MEMORY_STORE.clear()


class TestSeed:
    def test_seed_inserts_chunks(self) -> None:
        chunks = [
            {"source": "DIAN UVT", "content": "El UVT 2026 es $52.374"},
            {"source": "DIAN IVA", "content": "El IVA es 19%"},
        ]
        result = kb.seed_knowledge_base("test-client", chunks)
        assert result["backend"] == "memory"
        assert result["seeded"] == 2
        assert result["total_for_client"] == 2

    def test_seed_is_idempotent(self) -> None:
        chunks = [{"source": "DIAN UVT", "content": "El UVT 2026 es $52.374"}]
        kb.seed_knowledge_base("c1", chunks)
        result = kb.seed_knowledge_base("c1", chunks)  # same chunks again
        assert result["seeded"] == 0  # deduped
        assert result["total_for_client"] == 1

    def test_empty_chunks_returns_zero(self) -> None:
        result = kb.seed_knowledge_base("c1", [])
        assert result["seeded"] == 0


class TestRetrieve:
    def setup_method(self) -> None:
        kb._MEMORY_STORE.clear()
        kb.seed_knowledge_base("__global__", [
            {"source": "DIAN UVT", "content": "El UVT para 2026 es de 52.374 pesos"},
            {"source": "DIAN IVA", "content": "El IVA general en Colombia es del 19%"},
            {"source": "Estatuto Tributario", "content": "Las tarifas del Régimen Simple van de 1.8% a 11.6%"},
            {"source": "Contexia interna", "content": "La Matriz Financiera evalúa liquidez y solvencia"},
        ])

    def test_retrieve_top_match(self) -> None:
        results = kb.retrieve_similar("UVT 2026", "__global__", top_k=1)
        assert len(results) == 1
        assert "UVT" in results[0]["source"]

    def test_retrieve_handles_accents_and_stopwords(self) -> None:
        # Query without accents should still match accented content
        results = kb.retrieve_similar("regimen simple tarifas", "__global__", top_k=2)
        assert len(results) >= 1
        assert any("Régimen" in r["source"] or "Régimen" in r["content"] for r in results)

    def test_retrieve_falls_back_to_global_pool(self) -> None:
        # Unknown client falls back to __global__
        results = kb.retrieve_similar("IVA general", "nonexistent-client", top_k=1)
        assert len(results) == 1
        assert "IVA" in results[0]["source"] or "IVA" in results[0]["content"]

    def test_retrieve_returns_empty_on_no_match(self) -> None:
        results = kb.retrieve_similar("xyzqwerty nothing matches", "__global__", top_k=3)
        assert results == []


class TestDianSeed:
    def test_dian_seed_loads(self) -> None:
        n = kb.load_dian_seed()
        # The seed file ships with ~48 chunks; allow for additions
        assert n >= 30, f"expected ≥30 DIAN chunks, got {n}"

    def test_dian_seed_is_idempotent(self) -> None:
        kb.load_dian_seed()
        n = kb.load_dian_seed()
        assert n == 0  # second load adds nothing

    def test_can_retrieve_iva_from_seed(self) -> None:
        kb.load_dian_seed()
        results = kb.retrieve_similar("tarifa IVA general Colombia", "__global__", top_k=3)
        assert len(results) >= 1
        assert any("IVA" in r["source"] or "IVA" in r["content"] for r in results)


class TestBackendStatus:
    def test_status_reports_memory(self) -> None:
        kb.seed_knowledge_base("c1", [{"source": "s", "content": "test content here"}])
        status = kb.get_backend_status()
        assert status["backend"] == "memory"
        assert "c1" in status["memory_clients"]
        assert status["memory_total_chunks"] >= 1
