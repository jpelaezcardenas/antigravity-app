## Context

`route_lead_message` in `taty_lead_router.py` classifies every inbound WhatsApp message into
`sales_interest`, `payment_confirmation`, or `unknown` via two static keyword tuples
(`classify_lead_intent`). The `sales_interest` and `payment_confirmation` branches drive real
stage transitions (`NUEVOS→PROSPECTOS`, `→POR_APROBAR`) and touch real money (Wompi checkout links,
transaction status), all verified live across Changes D/H/I with a HITL gate at
`CrmService.approve_payment` between `POR_APROBAR` and `LISTOS_CONTADORA`. The `unknown` branch —
everything that doesn't match a sales/payment keyword, which in practice is most fiscal questions a
real lead would ask — returns one static reply and does nothing else.

Separately, `services/kb_seeding_service.py` already implements a working retrieval function
(`retrieve_similar(query, client_id, top_k=5)`), backing a DIAN normograma corpus seeded under the
shared `"__global__"` client_id pool (confirmed via `kb_seeding_service.py`'s own docstrings and
`kb_endpoints.py`'s `/kb/search` debug endpoint) — but nothing in the Taty lead-router pipeline
calls it. `agents/secure_llm.py` already provides the mandatory SOSP-anonymized LLM call wrapper
(`get_anonymized_ai_response`) used elsewhere in this repo for anything that might see PII/fiscal
data before reaching a cloud LLM provider.

## Goals / Non-Goals

**Goals:**
- Give Taty a real, KB-grounded answer for fiscal questions that don't match the sales/payment
  keyword lists, instead of a canned non-answer.
- Wire `retrieve_similar` into the lead-router pipeline for the first time (closes gap #4).
- Introduce a bounded Reason→Act→Reason loop (closes gap #3, scoped narrowly — see Decision 1).

**Non-Goals:**
- **Rewriting `sales_interest`/`payment_confirmation` classification to be LLM-driven.** These
  already work, are deterministic (a legal/product requirement for anything touching
  `CrmService.approve_payment`'s HITL gate and real Wompi transactions), and are covered by a live
  Stage-11-verified test suite across three archived changes. Replacing deterministic keyword
  matching with probabilistic LLM classification for a path that moves money is a regression in
  reliability disguised as an upgrade — explicitly rejected here (Decision 1).
- **An open-ended, multi-step agent loop.** This change implements exactly one bounded Reason→Act→
  Reason sequence per message (classify-and-decide → optional KB search → synthesize), not a
  recursive ReAct agent that can call tools repeatedly. An unbounded loop is unnecessary for "answer
  a fiscal question" and would be far harder to test deterministically and rate-limit/cost-control.
- **Streaming replies or conversational memory across messages.** Each message is still handled
  independently, consistent with the existing router's statelessness (state lives in
  `crm_leads`/`crm_tax_profiles`, not in-memory conversation history).

## Decisions

1. **Scope the "ReAct" rework to the `unknown`-intent fallback only, not the whole router.**
   Alternative considered: replace `classify_lead_intent` entirely with an LLM call that decides
   among all three intents. Rejected — introduces non-determinism into a path that advances a lead
   to `POR_APROBAR`/creates real Wompi checkout links; the existing keyword approach has a 100%
   reproducible test suite Change H/I built confidence on, and there's no product reason to touch
   what already works. The `unknown` branch is exactly where Taty currently provides zero value, so
   that's where the upgrade belongs.
2. **Bounded 2-call Reason→Act→Reason sequence, not an agent loop.**
   Call 1 (`_classify_fiscal_question`, JSON mode via `get_anonymized_ai_response`): given the
   message, returns `{"is_fiscal_question": bool, "search_query": str}`. If `is_fiscal_question`
   is false, fall back to the existing static "No estoy segura..." reply (zero behavior change for
   genuinely off-topic messages, e.g. "hola" or spam).
   Act: if true, call `retrieve_similar(search_query, "__global__", top_k=3)` (the existing,
   unmodified KB function, shared DIAN pool — Taty has no tenant/client_id of her own for this
   corpus, per the confirmed `"__global__"` convention).
   Call 2 (`_synthesize_kb_reply`, text mode via `get_anonymized_ai_response`): given the message
   and the retrieved chunks, produce a grounded reply. If `retrieve_similar` returns zero chunks,
   skip Call 2 entirely and return a graceful "no tengo esa información, un asesor de Contexia te
   puede ayudar" — never let the LLM hallucinate an answer with no retrieved grounding.
3. **All LLM calls go through `agents.secure_llm.get_anonymized_ai_response`, never
   `agents.llm_engine.get_ai_response` directly.** Non-negotiable per this repo's existing SOSP
   compliance rule — a WhatsApp message from a lead is exactly the kind of content (name, phone,
   possibly financial specifics) that must never reach a cloud provider unmasked.
4. **Unit tests mock `get_anonymized_ai_response` and `retrieve_similar` directly — no real LLM
   or Supabase credentials needed**, consistent with every prior Change in this router
   (`get_crm_service`, `_get_lead_stage`, etc. are all patched in existing tests). LLM
   non-determinism is exactly why the call boundary is mocked in tests, not exercised for real
   except in the Stage 11 live smoke test (which will use a real fiscal question and eyeball the
   reply for plausibility, since an LLM reply can't be asserted byte-for-byte).
5. **Graceful degradation on any LLM failure**: if `get_anonymized_ai_response` raises (provider
   failover exhausted, timeout, etc.) at either call site, catch and fall back to the pre-existing
   static "No estoy segura de tu pregunta..." reply — Taty must never crash or leave a lead
   unanswered because an LLM provider had an outage.

## Risks / Trade-offs

- **[Risk] LLM latency added to every unmatched message** (2 sequential calls when a fiscal
  question is detected) → **Mitigation**: WhatsApp is not a synchronous UI waiting on this
  response in real time the way a chat widget would be; a few extra seconds before Taty's reply is
  acceptable. If this proves too slow live, a follow-up change could parallelize or cache common
  questions — not addressed here.
- **[Risk] Retrieved KB content might be stale or incomplete for 2026 DIAN rules** → **Mitigation**:
  out of scope for this change (the KB corpus's freshness is `kb_seeding_service.py`'s concern, not
  the router's); the router only fails gracefully when nothing relevant is found, it doesn't try to
  validate the corpus's currency.
- **[Trade-off] No conversational memory** — if a lead asks a follow-up that only makes sense in
  context of their previous message, this change won't handle it (each message stands alone). This
  matches the existing router's design already, not a new limitation introduced here.

## Migration Plan

No migration — pure logic addition to `taty_lead_router.py`'s existing `unknown` branch. Stage 11
live smoke test: send a fabricated WhatsApp message asking a real fiscal question (e.g. "¿qué pasa
si no declaro la renta a tiempo?"), confirm the reply is no longer the static fallback and instead
reflects retrieved KB content (or the graceful "no sé" message if the seeded corpus doesn't cover
it) — since LLM output can't be asserted exactly, this smoke test is inspected for plausibility,
not string-matched.

## Open Questions

- Should the `_classify_fiscal_question` call also detect and bail early for a message that's
  clearly abusive/spam, to save an LLM call? Not addressed here — out of scope, no evidence yet
  this is a real problem at current lead volume.
