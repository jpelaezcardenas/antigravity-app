## Why

Gaps #3 and #4 from the plan-vs-build audit are the same subsystem: Taty's WhatsApp sales router
(`taty_lead_router.py`) only does deterministic keyword classification (`sales_interest`,
`payment_confirmation`, `unknown`), and the existing KB retrieval module
(`services/kb_seeding_service.py`'s `retrieve_similar`, backing DIAN normograma content) is never
called from it. Today, any lead who asks a real fiscal question ("¿qué pasa si no declaro a
tiempo?", "¿tengo que declarar si soy independiente?") that doesn't match the narrow sales/payment
keyword lists gets a canned, unhelpful reply: *"No estoy segura de tu pregunta..."* — even though
this repo already has a working KB search endpoint doing exactly this for other purposes. Wiring
these together turns Taty from a keyword router into something that can actually answer.

## What Changes

- The `sales_interest`/`payment_confirmation` keyword classification and their downstream
  stage-transition logic (already live, verified in Changes D/H/I, HITL-gated at
  `CrmService.approve_payment`) are **left untouched** — see design.md Decision 1 for why a full
  LLM-driven rewrite of that already-verified, deterministic funnel is explicitly out of scope
  here.
- The `unknown` intent fallback in `route_lead_message` — currently a single static reply — becomes
  a bounded Reason→Act→Reason loop: one anonymized LLM call classifies whether the message is a
  fiscal question and, if so, what to search for; if yes, `retrieve_similar` is called against the
  shared `__global__` DIAN KB pool; a second anonymized LLM call synthesizes a grounded reply from
  the retrieved chunks (or a graceful "no sé, un asesor te ayuda" if nothing relevant is found).
- All LLM calls go through the existing, unmodified `agents.secure_llm.get_anonymized_ai_response`
  — no prompt reaches a provider without SOSP anonymization first (mandatory per existing
  compliance rule).

## Capabilities

### New Capabilities
(none — extends the existing WhatsApp sales-router capability)

### Modified Capabilities
- `taty-whatsapp-sales-router`: adds a new requirement for KB-grounded fiscal-question answering
  on the `unknown`-intent fallback path; the `sales_interest`/`payment_confirmation` requirements
  are unchanged.

## Impact

- `apps/backend/services/taty_lead_router.py` — the only routing logic touched (`unknown` branch
  of `route_lead_message`).
- `apps/backend/services/kb_seeding_service.py` — reused as-is (`retrieve_similar`), not modified.
- `apps/backend/agents/secure_llm.py` — reused as-is (`get_anonymized_ai_response`), not modified.
- No migration, no new endpoint, no frontend change.
