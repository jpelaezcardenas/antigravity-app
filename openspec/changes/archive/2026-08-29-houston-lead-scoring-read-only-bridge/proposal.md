# Proposal: houston-lead-scoring-read-only-bridge

## Why

Subdomain 7 of the freemium-onboarding master plan (`houston-outreach-content-critic-bridge`)
assumed Houston's outreach agent might produce content needing validation through the existing
Sell Machine Content Critic loop (`run_creative_loop`/`manus_draft_hooks`), which would require
generalizing that parameter. Investigation (informed by the founder's own decision, documented in
`docs/integrations/houston-plan-integracion.md`) found this premise does not hold: Houston is
being used **read-only, for lead-scoring/pipeline visibility only** ("por ahora autotag only"),
consuming the existing `hermes-hubspot-poller` bridge via its own Composio→HubSpot connector.
Houston never writes back to HubSpot or Contexia, and does not generate outreach content this
change needs to gate.

## What Changes

- No code changes to `antigravity-app`. This is an investigation-and-documentation change,
  closing the master plan's open Subdomain 7 question with a concrete answer.
- Adds two durable reference documents to `docs/integrations/`:
  - `houston-plan-integracion.md` — the integration plan (Houston reads Contexia's real HubSpot
    pipeline via Composio; no new code; a playbook file removes Houston's need to guess facts).
  - `houston-playbook-ventas.md` — the actual playbook content uploaded to Houston via its
    `set-up-my-sales-info` skill (company facts, ICP, unconfirmed pricing, CRM stage mapping).
- Documents an explicit, known gap: Chatwoot's lead classification (intención/prioridad/
  servicio_interes) does not reach HubSpot today, so Houston cannot see it while connected only
  via HubSpot. Flagged as a future, separate change if the founder wants Houston's scoring to use
  those signals — not built here.

## Capabilities

### New Capabilities
None — no spec-level behavior change to any Contexia system. Houston is an external consumer of
the existing `hubspot-sync-renta-natural` capability's output; that capability's contract is
unchanged (still strictly unidirectional Supabase → HubSpot, per ARCHITECTURE.md Decision #20).

### Modified Capabilities
None.

## Impact

- `docs/integrations/houston-plan-integracion.md`, `docs/integrations/houston-playbook-ventas.md`
  — new reference docs (persisted per the founder's explicit request — "deben quedar como fuente
  fija acá, no perdidos en un hilo de Claude Code").
- `ARCHITECTURE.md` — one-line addendum to Decision #20 noting Houston's read-only Composio/
  HubSpot consumption of the existing bridge.
- No backend/frontend code touched. No deploy required (docs-only).
