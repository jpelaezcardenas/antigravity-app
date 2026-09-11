## Why

Renta Natural (Entidad A) is the only revenue-generating offer Contexia can close before the DIAN
cohort window shuts on 2026-10-26, and no lead has ever completed the full path — WhatsApp intake
→ Taty triage → Tatiana review → real payment → document delivery — end to end. Three prerequisite
OpenSpec changes (`taty-channel-consolidation`, `whatsapp-durable-inbox`,
`taty-wompi-entidad-a-remittance`) already carry the exact blocking work, at 55%, 60%, and 0%
completion respectively, but none of them individually defines "done" as a verified sale. This
change absorbs their remaining scope under one closing criterion — money moving once, correctly
attributed to Entidad A — instead of three independently-archivable code changes with no shared
finish line.

## What Changes

- Consolidate the single live WhatsApp channel (resolve the `phone_number_id` conflict, sign both
  webhooks) so Meta has exactly one callback URL to point at — absorbs `taty-channel-consolidation`
  tasks 4-9.
- Make inbound WhatsApp durable: a Chatwoot poller drains the backend's event inbox so no message
  is lost to a bridge restart, backed by a dedicated "Taty Bot" Chatwoot user — absorbs
  `whatsapp-durable-inbox` tasks 4-8.
- ~~Build the Wompi remittance rail from zero~~ **DEFERRED 2026-09-10 (founder decision)**: the
  first sale's payment path is cash or a direct transfer (key/QR) received by Tatiana in person,
  not a Wompi flow. Only the generic tracking migration was written (unapplied); the payout
  service, CRM trigger, and retry endpoint are not built for this change. See design.md Decision 3b.
- Reference (do not reopen) `taty-document-collection-wiring`, already deployed to production —
  its remaining task 6 (synthetic-document verification) is tracked here as a pre-flight check,
  not new scope.
- Define and execute the end-to-end verification: one real Renta Natural transaction, human-
  approved, correctly routed to Entidad A, with delivery of the resulting service.

**BREAKING**: none — this closes gaps in already-open, unreleased changes; no shipped behavior
changes shape.

## Capabilities

### New Capabilities
- `renta-natural-sale-verification`: the end-to-end acceptance criterion — one verified real sale,
  human-approved at every required gate — that none of the three absorbed changes independently
  defines. Owns the go/no-go checklist and the Stage 11 report format for the whole path.

### Modified Capabilities
None. `taty-channel-consolidation` and `whatsapp-durable-inbox` already have complete spec files in
`openspec/specs/` whose requirement text does not change here — this change only finishes their
unimplemented tasks (their specs already describe the target behavior; the code has not caught up
yet). Likewise `wompi-payment-integration` (collection) is unaffected; the new Entidad A payout leg
is a distinct capability (`taty-wompi-entidad-a-remittance`, already spec'd, unimplemented), not a
modification to it.

## Impact

- Backend: `apps/backend/presentation/whatsapp_endpoints.py`, `channels/whatsapp.py`,
  `apps/backend/services/wompi_payout_service.py` (new), `apps/backend/services/crm_service.py`,
  a new `apps/backend/migrations/0036_whatsapp_inbound_events.sql` (already drafted, not applied)
  and a new remittance-tracking migration (number TBD at implementation time — see design.md).
- `apps/chatwoot-bridge/`: new `inbox_poller.py`, dedicated Chatwoot bot user.
- Founder-dependent, non-code preconditions: Meta App Secret retrieval, `phone_number_id` decision,
  Wompi Pagos a Terceros confirmation with Wompi support, Entidad A payout beneficiary details —
  all tracked as blocking tasks with the founder as explicit owner, never assumed or defaulted.
- Does not touch `apps/backend/core/plan_features.py`, Pulso, GPS, Agentic OS, or any B2B-tier
  surface.
- Adjacent but explicitly out of scope: the `hermes-manus-poller` paid-acquisition circuit (Meta/
  Instagram ad publishing via Manus) documented in `apps/hermes-manus-poller/` and the two Manus
  GTM playbooks provided by the founder — that circuit drives traffic *into* this sale path but is
  a separate, already ~70%-built system with its own OpenSpec capability
  (`hermes-manus-poller`/`hermes-manus-execution-bridge`) and is not modified here.
