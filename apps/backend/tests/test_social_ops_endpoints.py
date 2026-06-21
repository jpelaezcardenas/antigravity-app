from fastapi.testclient import TestClient
from unittest.mock import patch

from agents.llm_engine import AllProvidersFailedError
from main import app
from services.social_ops_service import get_social_ops_service


client = TestClient(app)


def setup_function():
    get_social_ops_service().reset_memory(seed=False)


def test_social_ops_event_simulation_and_pipeline_contract():
    response = client.post(
        "/api/v1/social-ops/events/simulate",
        json={
            "channel": "instagram",
            "event_type": "comment",
            "text": "Tengo una multa DIAN y necesito auditoria sombra",
            "actor_handle": "@lead",
            "source_event_id": "endpoint-1",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created"] is True
    assert body["diagnosis"]["next_stage"] == "auditoria_sombra"

    pipeline = client.get("/api/v1/social-ops/pipeline")
    assert pipeline.status_code == 200
    assert "columns" in pipeline.json()
    assert pipeline.json()["summary"]["total_leads"] == 1


def test_command_parse_contract_keeps_pending_approval():
    response = client.post(
        "/api/v1/social-ops/commands/parse",
        json={
            "text": "/ops publicar carrusel en LinkedIn",
            "channel": "telegram",
            "actor_handle": "ops",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "pending_approval"
    assert body["action"] == "publish_content"


def test_meta_tiktok_and_linkedin_channel_contracts():
    meta = client.post(
        "/api/v1/channels/meta/webhook",
        json={
            "object": "facebook",
            "entry": [
                {
                    "id": "page",
                    "messaging": [
                        {
                            "message": {"mid": "m1", "text": "Necesito RUT"},
                            "sender": {"id": "u1"},
                        }
                    ],
                }
            ],
        },
    )
    tiktok = client.post(
        "/api/v1/channels/tiktok/webhook",
        json={"events": [{"id": "tt1", "comment_text": "Me preocupa la DIAN"}]},
    )
    linkedin = client.post(
        "/api/v1/channels/linkedin/sync",
        json={"comments": [{"id": "li1", "text": "Conectar Stripe"}]},
    )

    assert meta.status_code == 200
    assert tiktok.status_code == 200
    assert linkedin.status_code == 200
    assert meta.json()["events_ingested"] == 1
    assert tiktok.json()["events_ingested"] == 1
    assert linkedin.json()["events_ingested"] == 1


def test_lead_reply_draft_contract_is_pending_approval():
    created = client.post(
        "/api/v1/social-ops/events/simulate",
        json={
            "channel": "instagram",
            "event_type": "comment",
            "text": "Tengo multa DIAN y no se si necesito RUT",
            "actor_handle": "@lead",
            "source_event_id": "reply-1",
        },
    ).json()
    lead_id = created["lead"]["id"]

    reply = client.post(
        "/api/v1/social-ops/leads/reply-draft",
        json={"lead_id": lead_id, "channel": "instagram", "actor_handle": "taty"},
    )
    assert reply.status_code == 200
    body = reply.json()
    assert body["status"] == "pending_approval"
    assert "Taty" in body["message_text"]


def test_sales_draft_contract_is_pending_approval():
    created = client.post(
        "/api/v1/social-ops/events/simulate",
        json={
            "channel": "facebook",
            "event_type": "message",
            "text": "Quiero vender en TikTok pero me preocupa la DIAN y no tengo RUT",
            "actor_handle": "prospecto",
            "source_event_id": "sales-1",
        },
    ).json()
    lead_id = created["lead"]["id"]

    sales = client.post(
        "/api/v1/social-ops/leads/sales-draft",
        json={"lead_id": lead_id, "channel": "facebook", "actor_handle": "taty"},
    )
    assert sales.status_code == 200
    body = sales.json()
    assert body["status"] == "pending_approval"
    assert "Auditoria Sombra" in body["message_text"]


def test_ideas_endpoints_contract():
    ideas = client.get("/api/v1/social-ops/ideas")
    assert ideas.status_code == 200
    body = ideas.json()
    assert "items" in body

    if body["items"]:
        idea_id = body["items"][0]["id"]
        upd = client.post(f"/api/v1/social-ops/ideas/{idea_id}/status", json={"status": "SELECCIONADA"})
        assert upd.status_code == 200
        gen = client.post(f"/api/v1/social-ops/ideas/{idea_id}/generate-draft")
        assert gen.status_code == 200
        assert "draft_text" in gen.json()


def test_generate_draft_falls_back_when_all_llm_providers_fail():
    get_social_ops_service().reset_memory(seed=True)
    ideas = client.get("/api/v1/social-ops/ideas").json()["items"]
    assert ideas
    idea_id = ideas[0]["id"]

    with patch("agents.llm_engine.get_ai_response", side_effect=AllProvidersFailedError("llm down")):
        response = client.post(f"/api/v1/social-ops/ideas/{idea_id}/generate-draft")

    assert response.status_code == 200
    body = response.json()
    assert body["idea_id"] == idea_id
    assert "draft_text" in body
    assert "Contexia" in body["draft_text"]
