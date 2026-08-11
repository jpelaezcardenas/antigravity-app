"""Tests for TatyAgentService's WhatsApp sales-lead calling convention
(taty-whatsapp-renta-sales-capability, Stage 4).

`conversation_history` and `lead_context` are additive parameters on `ask()` /
`_build_prompt()` / `_build_system_prompt()`: every existing caller (Telegram, PWA) omits
them, so these tests focus on (a) the omitted case being a true no-op, matching
`test_taty_ask_tenant_scoping.py`'s hermetic-mock convention, and (b) the new WhatsApp-shaped
content actually appearing when they're provided — including the "never invent a price"
instruction, since pricing tiers are undefined as of this change.
"""

from __future__ import annotations

from services.taty_service import TatyAgentService, DEFAULT_PROFILE


def _profile(**overrides) -> dict:
    base = {
        **DEFAULT_PROFILE,
        "tenant_id": "11111111-1111-1111-1111-111111111111",
        "nit": None,
        "nombre_empresa": "Contexia SAS",
        "company_id": None,
        "kb_client_id": "__global__",
    }
    base.update(overrides)
    return base


class TestBuildPromptConversationHistory:
    def test_no_history_omits_conversation_block(self):
        profile = _profile()
        prompt = TatyAgentService()._build_prompt("Hola", [], profile)
        assert "Conversación reciente" not in prompt

    def test_history_renders_user_and_assistant_turns(self):
        profile = _profile()
        history = [
            {"role": "user", "text": "Hola ayudame"},
            {"role": "assistant", "text": "Claro, ¿en qué te ayudo?"},
        ]
        prompt = TatyAgentService()._build_prompt(
            "Quiero saber si me toca declarar renta", [], profile, conversation_history=history
        )
        assert "Conversación reciente" in prompt
        assert "Cliente: Hola ayudame" in prompt
        assert "Taty: Claro, ¿en qué te ayudo?" in prompt

    def test_empty_history_list_omits_conversation_block(self):
        profile = _profile()
        prompt = TatyAgentService()._build_prompt("Hola", [], profile, conversation_history=[])
        assert "Conversación reciente" not in prompt


class TestBuildSystemPromptLeadContext:
    def test_no_lead_context_matches_base_prompt_exactly(self):
        """Regression safety: Telegram/PWA never pass lead_context, so the system prompt they
        get must be byte-identical to before this parameter existed."""
        profile = _profile()
        taty = TatyAgentService()
        with_none = taty._build_system_prompt(profile)
        with_explicit_none = taty._build_system_prompt(profile, lead_context=None)
        assert with_none == with_explicit_none
        assert "Contexto adicional" not in with_none

    def test_lead_stage_included_when_present(self):
        profile = _profile()
        prompt = TatyAgentService()._build_system_prompt(
            profile, lead_context={"lead_stage": "PROSPECTOS"}
        )
        assert "PROSPECTOS" in prompt

    def test_persona_asalariado_described(self):
        profile = _profile()
        prompt = TatyAgentService()._build_system_prompt(
            profile, lead_context={"persona_fields": {"es_asalariado": True}}
        )
        assert "asalariado" in prompt.lower()

    def test_persona_independiente_described(self):
        profile = _profile()
        prompt = TatyAgentService()._build_system_prompt(
            profile, lead_context={"persona_fields": {"es_asalariado": False}}
        )
        assert "independiente" in prompt.lower()

    def test_required_documents_listed(self):
        profile = _profile()
        prompt = TatyAgentService()._build_system_prompt(
            profile,
            lead_context={"offer": {"documentos_requeridos": ["RUT", "extractos bancarios"]}},
        )
        assert "RUT" in prompt
        assert "extractos bancarios" in prompt

    def test_unconfirmed_price_instructs_never_to_invent_a_number(self):
        profile = _profile()
        prompt = TatyAgentService()._build_system_prompt(
            profile, lead_context={"offer": {"precio_confirmado": False}}
        )
        assert "no inventes" in prompt.lower()
        assert "asesor" in prompt.lower()

    def test_offer_without_precio_confirmado_key_defaults_to_no_invent_instruction(self):
        """Missing key must behave the same as explicit False — a lead_context built without
        pricing info yet must never accidentally allow Taty to state a number."""
        profile = _profile()
        prompt = TatyAgentService()._build_system_prompt(
            profile, lead_context={"offer": {"documentos_requeridos": ["RUT"]}}
        )
        assert "no inventes" in prompt.lower()

    def test_confirmed_price_omits_the_never_invent_instruction(self):
        """The price-specific never-invent instruction goes away once a price is confirmed — but
        the separate, unconditional never-invent-contact-details instruction (also phrased with
        'no inventes') is expected to still be present, so this checks the price-specific phrase
        precisely rather than the substring alone."""
        profile = _profile()
        prompt = TatyAgentService()._build_system_prompt(
            profile, lead_context={"offer": {"precio_confirmado": True}}
        )
        assert "no inventes ni menciones un número" not in prompt.lower()

    def test_never_invent_contact_details_instruction_always_present(self):
        """Found live 2026-08-11: without this, the model fabricates a plausible-looking
        Contexia email/phone/website when a WhatsApp lead asks how to make contact. Unlike the
        price flag, there's no 'confirmed' source to gate this on — it must always be present
        whenever lead_context is provided at all."""
        profile = _profile()
        prompt = TatyAgentService()._build_system_prompt(profile, lead_context={"lead_stage": "NUEVOS"})
        assert "correo" in prompt.lower()
        assert "no inventes" in prompt.lower()
