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


@pytest.mark.skipif(
    os.getenv("RUN_KB_PGVECTOR") != "1",
    reason="Exercises the live Supabase pgvector RPC; set RUN_KB_PGVECTOR=1 with SUPABASE_URL "
    "configured to run against a real project.",
)
class TestPgvectorSchemaMatchesRetrieveSimilar:
    """
    Regression coverage for taty-whatsapp-renta-sales-capability root cause #2: the live
    knowledge_chunks table + match_knowledge_chunks RPC diverged from what retrieve_similar()
    actually calls (no client_id column; RPC keyed on match_threshold, not p_client_id).
    Migration 0038_knowledge_chunks_client_id.sql reconciles this. These tests exercise the real
    pgvector path end-to-end against a live Supabase project (never mocked) so a future schema
    drift is caught here instead of live in a customer conversation.
    """

    def setup_method(self) -> None:
        # Override the file's autouse memory-forcing fixture: force real backend re-detection
        # against the actual configured Supabase project for this test class only.
        kb._BACKEND = None
        kb._SUPABASE_CLIENT = None

    def test_backend_detects_pgvector_when_supabase_is_configured(self) -> None:
        assert kb._detect_backend() == "pgvector"

    def test_retrieve_similar_call_signature_succeeds_against_live_rpc(self) -> None:
        """The exact failure mode found live 2026-08-11: calling retrieve_similar() raised
        because match_knowledge_chunks(query_embedding, p_client_id, match_count) did not exist.
        A successful call (even with zero results) proves the RPC signature now resolves."""
        results = kb.retrieve_similar("declaración de renta persona natural", "__global__", top_k=3)
        assert isinstance(results, list)

    def test_seed_then_retrieve_round_trips_through_pgvector(self) -> None:
        test_client = "test-taty-whatsapp-renta-sales-capability"
        chunks = [
            {
                "source": "test-fixture",
                "content": "Chunk de prueba para taty-whatsapp-renta-sales-capability, "
                "borrado al final del test.",
            }
        ]
        try:
            seed_result = kb.seed_knowledge_base(test_client, chunks)
            assert seed_result["backend"] == "pgvector"

            if kb._embed_text("probe") is None:
                pytest.skip("No embedding provider configured (OPENAI_API_KEY/GEMINI_API_KEY)")

            results = kb.retrieve_similar("prueba taty whatsapp", test_client, top_k=3)
            assert any(test_client in str(r) or "prueba" in r.get("content", "") for r in results)
        finally:
            # Restore DB state: this test must not leave rows behind.
            kb._SUPABASE_CLIENT.table("knowledge_chunks").delete().eq(
                "client_id", test_client
            ).execute()
