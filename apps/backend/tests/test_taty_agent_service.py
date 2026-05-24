from application.taty_agent_service import TatyAgentRequest, TatyAgentService


def test_taty_agent_returns_compatible_shape(monkeypatch):
    def fake_llm(**kwargs):
        assert "Fuentes recuperadas" in kwargs["prompt"]
        assert kwargs["preferred_provider"].value == "groq"
        return "La UVT 2026 es $52.374 COP segun la DIAN [S1]."

    monkeypatch.setattr("application.taty_agent_service.get_ai_response", fake_llm)

    service = TatyAgentService()
    response = service.ask(
        TatyAgentRequest(
            company_id="demo-company",
            question="Cuanto vale la UVT 2026?",
            channel="dashboard",
        )
    )

    assert response.success is True
    assert response.answer == response.result == response.response
    assert "$52.374" in response.answer
    assert response.citations
    assert response.latency_ms >= 0
    assert response.task_type == "taty_fiscal_rag"


def test_taty_agent_flags_human_review_for_dian_notice(monkeypatch):
    monkeypatch.setattr(
        "application.taty_agent_service.get_ai_response",
        lambda **kwargs: "Esto requiere revisar el caso con el equipo humano de Contexia.",
    )

    service = TatyAgentService()
    response = service.ask(
        TatyAgentRequest(
            company_id="demo-company",
            question="Me llego un requerimiento de la DIAN, que debo hacer?",
            channel="telegram",
        )
    )

    assert response.requires_human_review is True
    assert response.citations
