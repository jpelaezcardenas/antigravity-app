## Context

`crm_leads` (Change B, archived) already has a `whatsapp_phone` column and a `NUEVOS` stage meant
to receive inbound WhatsApp leads (confirmed live via Supabase MCP: `crm_leads(id, tenant_id,
full_name, whatsapp_phone, email, stage, source, last_message, score, assigned_agent, ...)`,
`crm_tax_profiles(id, tenant_id, lead_id, es_asalariado, topes, rut_status, extractos_status,
obligado_declarar, notes, ...)`). `crm_leads.tenant_id` is Cliente Cero's own tenant (the seller),
fixed — not the future tenant a converted lead would get. Nothing feeds `crm_leads` today except
manual seeding/advancing in the Búnker.

Taty exists today (`taty_service.py` + `taty_intent_router.py`) as a fiscal advisor for
already-onboarded tenants: `route_message(tenant_id, message)` classifies intent via deterministic
keyword matching (`classify_intent`) into `status | risk | correction | unknown`, and
`status`/`risk` call read-only agent functions scoped to that `tenant_id`
(`get_daily_summary(tenant_id)`, `calculate_risk_score(tenant_id)`). `correction` escalates to the
Approval Queue via `enqueue_taty_escalation(tenant_id, message)`. There is no lead concept anywhere
in this module — verified by reading it directly.

The existing Meta channel (`presentation/meta_endpoints.py` + `channels/meta.py`) proves the exact
`hub.challenge` handshake WhatsApp Cloud API also uses: `GET /webhook` reads
`hub.mode`/`hub.verify_token`/`hub.challenge` query params, compares against
`os.getenv("META_WEBHOOK_VERIFY_TOKEN", "contexia-meta-webhook")`, and echoes the challenge as
plain text on match. Telegram's channel (`channels/telegram.py` +
`presentation/telegram_endpoints.py`, not read in full here but confirmed structurally similar to
Meta's) is the template for inbound normalization shape and outbound sending via `httpx`.

## Goals / Non-Goals

**Goals:**
- Give WhatsApp-inbound leads a path into `crm_leads` (create-or-update by `whatsapp_phone`,
  advance `NUEVOS → PROSPECTOS` on sales intent).
- Reuse `CrmService.advance_lead`/`update_tax_profile` (Change B) completely unmodified.
- Prove the WhatsApp channel's plumbing (hub.challenge, inbound normalization, outbound sending)
  against simulated/fabricated payloads, with zero real WhatsApp credentials required to pass
  tests or even to deploy dark.
- Keep the Wompi-dependent tools (`generate_wompi_link`, `verify_wompi_transaction`) as honest,
  clearly-labeled stubs — never a fake payment confirmation.

**Non-Goals:**
- Going live with a real WhatsApp Business number/token — that's a manual founder step (Meta
  Business verification, phone number provisioning) outside this repo's code.
- Building the real Wompi integration (Change C).
- Touching `taty_intent_router.py`'s existing tenant-scoped behavior in any way.
- Any Hermes/Manus-side work.

## Decisions

**1. A new, separate lead-scoped router — NOT an extension of `taty_intent_router.py`.**
The proposal's original framing ("extend `taty_intent_router.py` with sales intents") doesn't fit
the actual code: `route_message`/`classify_intent`/the escalation helper are all built around
`tenant_id` and call tenant-scoped agent functions (`get_daily_summary`, `calculate_risk_score`).
A WhatsApp lead has no `tenant_id` — it's a prospect who hasn't signed up. Bolting lead-shaped
logic onto a tenant-shaped function would require an awkward union parameter or silently wrong
calls. Instead: a new module, `services/taty_lead_router.py`, with its own
`classify_lead_intent(message) -> (intent, confidence)` and `route_lead_message(lead_id, message)
-> dict`, reusing the *pattern* (deterministic keywords, an escalation-style approval-queue path
for the payment-confirmation intent) but operating on `lead_id` throughout. This mirrors how
Change F introduced a new service rather than extending `executor_outbox` for a shape it didn't
fit (same lesson, applied again).

**2. Reuse `crm_leads.whatsapp_phone` as the identity key; no new `whatsapp_chat_mappings` table.**
Confirmed live via Supabase MCP that the column already exists from Change B. A lead is
found-or-created by `whatsapp_phone` directly in `crm_leads` — no separate mapping table needed,
simpler than the plan's original sketch (which proposed one as an "or" alternative).

**3. New `WHATSAPP_CANONICAL` flag — not reusing an existing one.**
Unlike Change F (which reused `SELL_MACHINE_CANONICAL` because it extended an already-live
surface), this is a brand-new channel surface with its own webhook and no existing flag covers it.
Matches Change E's precedent (new capability area → new flag, dark-deployed, flipped after a
Stage 11 smoke test).

**4. WhatsApp env vars read via `os.getenv`, not added to `config.py`'s pydantic `Settings`.**
Matches the existing `META_WEBHOOK_VERIFY_TOKEN` precedent in `meta_endpoints.py` exactly (`import
os; os.getenv("...", "default")`) rather than introducing a new pattern. `WHATSAPP_TOKEN`,
`WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_WEBHOOK_VERIFY_TOKEN` — none of these have real values yet;
`send_whatsapp_message()` checks for their presence and raises/returns a clear "not configured"
result rather than making a network call with empty credentials.

**5. `generate_wompi_link`/`verify_wompi_transaction` are explicit `NotImplementedError`-raising
stubs, not fakes.**
Each stub's docstring and error message names Change C as the closure. `route_lead_message`
catches this specific case for the "ya pagué"/payment-intent branch and returns a
graceful "not yet available, an admin will follow up" reply — never a fabricated "payment
confirmed."

**6. Sales-intent detection triggers `advance_lead(lead_id, "PROSPECTOS")` only from `NUEVOS`.**
If the lead is already past `NUEVOS` (e.g. an existing `PROSPECTOS`/`POR_APROBAR` lead texts
again), `route_lead_message` does NOT re-advance or regress the stage — it only ever moves forward
once, from `NUEVOS`. This avoids fighting with a human admin who's already manually advanced/
approved the lead in the Búnker. `CrmService.advance_lead` itself has no such guard (any stage to
any valid stage), so this guard lives in the new router, not in the reused service.

**7. Persona-state persistence uses `update_tax_profile` incrementally, tolerant of a missing row.**
`crm_tax_profiles` is 1:1 with a lead (Change B seeds one per lead) but a brand-new WhatsApp-created
lead won't have one yet. `route_lead_message` creates an empty `crm_tax_profiles` row (via a direct
insert, matching Change B's seed pattern) if `get_tax_profile(lead_id)` returns `{}`, then applies
detected persona fields (`es_asalariado`, `topes`) via the existing `update_tax_profile`.

## Risks / Trade-offs

- **[Risk] No real WhatsApp number exists — this entire channel is unverifiable end-to-end until
  one is provisioned.** → Mitigation: all logic (normalizer, router, stage transitions, persona
  persistence) is tested against fabricated WhatsApp Cloud API payload shapes (public API docs
  shape, no real credentials). Stage 11's live smoke test exercises the deployed webhook with a
  simulated payload via curl — explicitly documented as a stand-in for real verification, not a
  substitute for it.
- **[Risk] Deterministic keyword classification is coarse (same trade-off Taty's existing router
  already accepted).** → Mitigation: consistent with the existing precedent; not a regression.
  Low-confidence messages get a clarifying reply, same idiom as `taty_intent_router.py`'s
  `unknown` branch.
- **[Risk] A malicious/malformed webhook payload.** → Mitigation: the normalizer defensively reads
  optional fields (`.get()` throughout, matching `channels/telegram.py`'s style) and returns an
  empty event list rather than raising, so a bad payload can't crash the webhook handler.

## Migration Plan

1. Channel + normalizer + lead router, TDD, no new tables/migrations (reuses `crm_leads`/
   `crm_tax_profiles` as-is).
2. New `WHATSAPP_CANONICAL` flag added to `config.py`, defaulting `false`; routes registered in
   `router.py` behind it.
3. Stage 11: commit, merge, verify Railway green with the flag still `false` (dark deploy — this
   DOES need the dark-deploy step, new flag), verify the webhook's `GET` hub.challenge responds
   correctly even while dark (no data risk in a handshake echo), flip the flag, `POST` a fabricated
   inbound WhatsApp payload via curl, confirm a `crm_leads` row is created/advanced and
   `crm_tax_profiles` persona fields land correctly via direct Supabase SQL, deployment report
   (explicitly noting the no-real-number limitation), archive.
- **Rollback**: flip `WHATSAPP_CANONICAL` back to `false`; the webhook route disappears, nothing
  else in the codebase depends on it.

## Open Questions

- Real WhatsApp Business number + token + Meta Business verification — tracked as an existing open
  decision in the Sell Machine plan, not resolved by this change.
- Should `taty_lead_router.py` eventually call an LLM for richer intent classification instead of
  keywords? Deferred — keyword matching is consistent with the existing Taty precedent and
  sufficient for this stage.
