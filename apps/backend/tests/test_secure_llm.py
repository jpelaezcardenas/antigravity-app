"""Tests for the SOSP-compliant LLM wrapper (agents/secure_llm.py).

Guarantees that raw client identifiers/fiscal data never leave the server in the
outbound prompt, and that the model's response is rehydrated to originals.
"""
from unittest.mock import patch

from agents.secure_llm import get_anonymized_ai_response

RAW = "Cliente NIT 900.123.456-7, email cliente@acme.co, facturó $12.500.000 este mes."
SECRETS = ["900.123.456-7", "cliente@acme.co", "$12.500.000"]


def test_outbound_prompt_is_anonymized_and_response_rehydrated():
    captured = {}

    def fake_get_ai_response(prompt, system_prompt="", **kwargs):
        captured["prompt"] = prompt
        # Simulate the model echoing the (masked) prompt back in its answer.
        return prompt

    with patch("agents.secure_llm.get_ai_response", side_effect=fake_get_ai_response):
        result = get_anonymized_ai_response(prompt=RAW, system_prompt="Eres un analista.")

    sent = captured["prompt"]
    # Raw identifiers must NOT leave the server.
    for secret in SECRETS:
        assert secret not in sent, f"{secret} leaked in outbound prompt"
    # Opaque tokens are sent instead.
    assert "<NIT_1>" in sent
    assert "<EMAIL_1>" in sent
    assert "<MONEY_1>" in sent
    # The response is rehydrated back to the original values.
    for secret in SECRETS:
        assert secret in result, f"{secret} not restored in response"


def test_system_prompt_is_also_anonymized():
    captured = {}

    def fake_get_ai_response(prompt, system_prompt="", **kwargs):
        captured["system_prompt"] = system_prompt
        return "ok"

    with patch("agents.secure_llm.get_ai_response", side_effect=fake_get_ai_response):
        get_anonymized_ai_response(
            prompt="¿Debo declarar renta?",
            system_prompt="Contexto del cliente: cliente@acme.co NIT 900.123.456-7",
        )

    sent_system = captured["system_prompt"]
    assert "cliente@acme.co" not in sent_system
    assert "900.123.456-7" not in sent_system


def test_dict_response_is_rehydrated():
    def fake_get_ai_response(prompt, system_prompt="", **kwargs):
        # JSON path: model returns a dict containing tokens from the masked prompt.
        return {"resumen": prompt, "detalle": {"nota": prompt}}

    with patch("agents.secure_llm.get_ai_response", side_effect=fake_get_ai_response):
        result = get_anonymized_ai_response(prompt=RAW, response_format="json")

    assert isinstance(result, dict)
    for secret in SECRETS:
        assert secret in result["resumen"]
        assert secret in result["detalle"]["nota"]


def test_pulso_analyze_endpoint_anonymizes_outbound_prompt():
    """End-to-end: the /pulso/analyze endpoint must not leak raw fiscal data."""
    from fastapi.testclient import TestClient
    from main import app

    client = TestClient(app)
    captured = {}

    def fake_get_ai_response(prompt, system_prompt="", **kwargs):
        captured["prompt"] = prompt
        return {"resumen": "ok"}

    with patch("agents.secure_llm.get_ai_response", side_effect=fake_get_ai_response):
        resp = client.post(
            "/api/v1/agents/pulso/analyze",
            json={
                "data": {
                    "nit": "900.123.456-7",
                    "email": "cliente@acme.co",
                    "ingresos": "$12.500.000",
                },
                "company_id": "ctx-001",
            },
        )

    assert resp.status_code == 200
    assert "prompt" in captured, "endpoint did not route through the LLM wrapper"
    for secret in SECRETS:
        assert secret not in captured["prompt"], f"{secret} leaked from /pulso/analyze"
