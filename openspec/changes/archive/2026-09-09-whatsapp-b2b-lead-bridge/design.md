## Context

`chatwoot-b2b-lead-capture-investigation` (archived 2026-08-28) found the gap at the *system*
level: nothing routes a WhatsApp/Taty conversation into a B2B lead. Re-investigating the actual
code (2026-09-09) narrows the fix considerably — the auto-tagging pipeline the original findings
called "never built" partially exists:

- `apps/backend/services/taty_lead_router.py:91-106` — `classify_lead_intent(message) -> Tuple[str, float]`
  returns `"sales_interest"`, `"payment_confirmation"`, or `"unknown"` via keyword lists
  (`SALES_INTEREST_KEYWORDS`, `PAYMENT_CONFIRMATION_KEYWORDS`), all scoped to Renta Natural.
- `apps/chatwoot-bridge/main.py:86-119` — `_auto_tag_chatwoot()` **already** writes Chatwoot
  custom attributes programmatically (fire-and-forget, `chatwoot_client.py:96-127`): conversation
  tags (`intencion`, `prioridad`, `siguiente_accion`) and contact attributes (`servicio_interes`
  via `_INTENT_TO_SERVICIO_INTERES[intent]`, `tipo_contribuyente` as a binary
  `persona_natural`/`regimen_simple` derived from `persona_fields["es_asalariado"]`). This is *not*
  a human-only path as the original findings assumed — it just has no B2B branch.
- `crm_leads` (written via `CrmService.whatsapp_intake()`, `crm_service.py:496-536`, and
  `advance_lead()`, line 538-547) has no column distinguishing a B2B signal from the default Renta
  Natural funnel — only `id`, `tenant_id`, `whatsapp_phone`, `full_name`, `stage`, `score`,
  `last_message` are used in code today.
- `TatyAgentService.ask()` (`taty_service.py:159,219-260`) already takes `conversation_history` and
  `lead_context` as additive, defaulted `Optional` params (Decisión #19) — no signature change
  needed here.
- `resolve_request_tenant_scope()` (`core/tenant_context.py:69-94`) is for *authenticated,
  multi-tenant* callers. WhatsApp prospect leads are pre-signup — `CrmService` resolves them under
  Cliente Cero (`_resolve_cliente_cero_tenant_id`, `crm_service.py:120`), a different and correct
  pattern for this stage of the funnel. This change does not touch that.

## Goals / Non-Goals

**Goals:**
- Detect, from the message text Taty already classifies, a B2B-shaped signal (persona jurídica /
  "empresa" / "SAS" / continuous-operations language) distinct from the existing Renta Natural
  categories.
- Persist that signal somewhere an operator can act on it: (a) Chatwoot attributes, extending the
  existing `_auto_tag_chatwoot()` pipeline with a B2B branch instead of building a new mechanism,
  and (b) a new nullable `crm_leads` column so the Búnker / a future dashboard can filter/list B2B
  leads without reading Chatwoot.
- Leave Renta Natural (Campaña 1) classification, replies, and HubSpot Deal-stage mapping
  byte-for-byte unchanged for every message that doesn't hit the new B2B branch.

**Non-Goals:**
- No automatic tenant/`b2b_clients` provisioning. Alta stays the founder/operator's decision via
  the existing `crm-alta-tiered-provisioning` flow (archived 2026-08-28) — this change only makes
  the lead visible.
- No changes to `hermes-hubspot-poller`'s sync rules — B2B leads still never sync as HubSpot
  Deals, only as Companies once/if provisioned (Decisión #20). Out of scope for this change to even
  touch that poller.
- No changes to `resolve_request_tenant_scope()` or the authenticated multi-tenant path — WhatsApp
  leads stay on the Cliente Cero pattern `CrmService` already uses.
- No new Chatwoot custom-attribute schema — reuses `tipo_contribuyente`/`servicio_interes`, whose
  dropdown options (`SAS`, `creacion_empresa`/`CFO`) already exist per the original investigation.

## Decisions

**1. Where the signal lives: extend `classify_lead_intent()`, not a parallel classifier.**
Add a 4th category `"business_interest"` to `taty_lead_router.py:91-106`, via a new
`BUSINESS_INTEREST_KEYWORDS` list (e.g. "empresa", "sas", "negocio", "sociedad", "compañía",
"contabilidad de mi empresa" — Spanish, business-registration/continuous-operations language).
Rationale: the function is already the single point every inbound WhatsApp message passes through
(`route_lead_message()`, line 317+); a parallel classifier would create two sources of truth for
the same message. Alternative considered and rejected: a second LLM-based classifier — rejected
because the existing three categories are keyword-based and cheap; adding a 4th keyword category
keeps the same cost/latency profile and the same testing pattern.

**2. Precedence when a message matches both business and payment/sales keywords.**
Check `business_interest` *before* `sales_interest` in `classify_lead_intent()` (payment
confirmation keeps first priority — money-related intent is time-sensitive and must never be
masked). A message like "somos una SAS interesados en el servicio" should classify as
`business_interest`, not `sales_interest`, so it gets tagged for a human to route correctly instead
of silently entering the Renta Natural sales flow.

**3. Chatwoot tagging: extend `_auto_tag_chatwoot()`, add one new mapping entry + one new
`tipo_contribuyente` branch.**
In `apps/chatwoot-bridge/main.py`: add `"business_interest": "creacion_empresa"` (or `"CFO"` — to
confirm against the exact dropdown option string during implementation, per the original finding's
mention of both) to `_INTENT_TO_SERVICIO_INTERES`, and add a branch so `tipo_contribuyente` becomes
`"SAS"` (or the confirmed exact option) when `intent == "business_interest"`, taking precedence
over the existing `persona_natural`/`regimen_simple` derivation. No changes to the fire-and-forget
error handling or to `set_conversation_attributes`/`set_contact_attributes` call shape.

**4. `crm_leads` gains one nullable column, not a new table.**
New migration adds `crm_leads.lead_type text NULL` (or reuses an existing enum-like pattern if one
is found during implementation — check for precedent before inventing a new column style), written
by `CrmService.whatsapp_intake()`/`advance_lead()` when `intent == "business_interest"`. Default
stays `NULL` (existing Renta Natural leads are not retroactively touched). Alternative considered:
piggyback on `stage` — rejected, `stage` already encodes funnel position (`NUEVOS`/`PROSPECTOS`/
etc.) per Decisión in the CRM funnel design; conflating it with lead *type* would break existing
stage-based logic (`VALID_LEAD_STAGES`, HubSpot stage mapping).

**5. No tenant resolution changes.** The new write path uses the same
`_resolve_cliente_cero_tenant_id` pattern `CrmService` already uses for WhatsApp intake — this is
explicitly not a `resolve_request_tenant_scope()` case, since there is no authenticated tenant yet.

## Risks / Trade-offs

- **[Risk]** Keyword-based B2B detection will have false positives/negatives (e.g. a Renta Natural
  client who happens to mention "mi empresa" casually). → **Mitigation**: this change only *tags
  for human review* (Chatwoot attributes + `crm_leads.lead_type`), never auto-provisions or
  auto-replies differently — a wrong tag costs an operator a few seconds, not a wrong sale.
- **[Risk]** Exact Chatwoot dropdown option strings (`SAS` vs full label, `creacion_empresa` vs
  `CFO`) weren`t confirmed against the live Chatwoot instance in this design pass. → **Mitigation**:
  implementer must read the actual dropdown option values from Chatwoot (via its admin UI or API)
  before hardcoding the string, not guess from the investigation doc's paraphrase.
- **[Risk]** Adding a keyword category could shift existing message classification if keyword
  lists overlap. → **Mitigation**: TDD — write tests asserting every existing
  `sales_interest`/`payment_confirmation`/`unknown` fixture message still classifies unchanged,
  before adding the new category's tests.

## Migration Plan

1. Add `BUSINESS_INTEREST_KEYWORDS` + 4th branch in `classify_lead_intent()` (TDD, existing
   fixtures must stay green).
2. Migration: `crm_leads.lead_type` nullable column (no default change to existing rows).
3. Wire `lead_type` write into `CrmService.whatsapp_intake()`/`advance_lead()`.
4. Extend `_auto_tag_chatwoot()` mapping + `tipo_contribuyente` branch (confirm exact dropdown
   strings against live Chatwoot first).
5. Stage 11: deploy, verify with a real or simulated WhatsApp conversation that would qualify for
   Campaña 2, confirm it lands in `crm_leads` with `lead_type` set and in Chatwoot with the right
   attributes — without changing any existing Renta Natural conversation's behavior.

Rollback: the new column is nullable and additive; reverting the keyword/tagging code is a normal
revert, no data migration needed to undo.

## Open Questions

- Exact Chatwoot dropdown option string for the B2B `servicio_interes`/`tipo_contribuyente` values
  — confirm against the live instance during implementation, not guessed here.
- Whether the Búnker's CRM view (`B2bRetainersTab.tsx` or a Renta Natural lead list) should
  surface `lead_type` visually in this change, or that's a fast-follow — founder to confirm scope
  before Track/task breakdown locks it in.
