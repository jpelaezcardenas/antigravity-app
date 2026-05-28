from channels.meta import normalize_meta_webhook
from channels.telegram import normalize_telegram_update
from services.social_ops_service import get_social_ops_service


def setup_function():
    get_social_ops_service().reset_memory(seed=False)


def test_telegram_normalization_and_idempotent_ingest():
    service = get_social_ops_service()
    update = {
        "update_id": 101,
        "message": {
            "message_id": 55,
            "text": "/ops conectar Stripe",
            "chat": {"id": 999, "type": "private"},
            "from": {"id": 123, "username": "founder", "first_name": "Ana"},
        },
    }

    [event] = normalize_telegram_update(update)
    first = service.ingest_normalized_event(event)
    second = service.ingest_normalized_event(event)

    assert first["created"] is True
    assert second["created"] is False
    assert len(service.events) == 1
    assert second["event"]["duplicate_count"] == 1


def test_meta_normalization_handles_instagram_comments():
    payload = {
        "object": "instagram",
        "entry": [
            {
                "id": "ig-account",
                "changes": [
                    {
                        "field": "comments",
                        "value": {
                            "comment_id": "c1",
                            "message": "Tengo multa DIAN por vender en TikTok",
                            "from": {"username": "creator"},
                        },
                    }
                ],
            }
        ],
    }

    [event] = normalize_meta_webhook(payload)

    assert event["channel"] == "instagram"
    assert event["event_type"] == "comment"
    assert "multa DIAN" in event["text"]


def test_classifies_commercial_maturity_cases():
    service = get_social_ops_service()

    embargo = service.analyze_text("Me llego embargo y requerimiento DIAN")
    rut = service.analyze_text("Necesito sacar RUT para vender cursos")
    stripe = service.analyze_text("Conectar Stripe y separar centro de costos")
    audit = service.analyze_text("Quiero auditoria sombra por una multa")

    assert embargo["urgency"] == "critical"
    assert embargo["next_stage"] == "escalado_entidad_a"
    assert rut["maturity_stage"] == "Semi-formal"
    assert stripe["maturity_stage"] == "Formal Escalable"
    assert stripe["next_stage"] in {"formalizacion", "activacion_fase2"}
    assert audit["next_stage"] == "auditoria_sombra"


def test_sensitive_commands_remain_pending_approval():
    service = get_social_ops_service()

    draft = service.parse_command(
        text="/ops integrar Stripe y crear centro de costos TikTok",
        channel="telegram",
        actor_handle="operator",
    )

    assert draft["status"] == "pending_approval"
    assert draft["requires_approval"] is True
    assert draft["action"] == "connect_integration"


def test_onboarding_intake_extracts_credentials_without_long_forms():
    service = get_social_ops_service()
    workspace = service.start_onboarding(
        company_name="ACME SAS",
        customer_email="owner@acme.co",
        payment_reference="pay_001",
        plan_name="Starter",
        owner_handle="@owner",
        requested_channels=["telegram", "instagram", "linkedin"],
    )

    intake = service.intake_onboarding(
        workspace_id=workspace["id"],
        source="telegram",
        actor_handle="@owner",
        text="Nuestro NIT es 901234567-8. Usamos Siigo. Bancolombia y Nequi. Tenemos Stripe. No tengo RUT aun.",
    )

    assert "erp_access" in intake["present"]
    assert "payment_processor_keys" in intake["present"]
    assert "token_dian" in intake["missing"]
    assert intake["extracted"]["erp"] == "siigo"
    assert "stripe" in intake["extracted"]["payment_processors"]
