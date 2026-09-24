## Why

Contexia just turned on Meta Pixel (commit `8d47a366`, 2026-09-23) but it only fires `PageView` — no
`Lead` event, no server-side CAPI — so ad spend cannot be attributed to real leads in HubSpot yet.
Separately, the founder has no proactive visibility into GTM health (ad spend, leads, Approval Queue
backlog, Manus task status): Telegram today is purely reactive (Taty replies to inbound messages).
And Approval Queue gates every draft uniformly regardless of risk, which does not scale as agent
task volume grows. A 2026-09-23 audit confirmed "Manus" today only generates ad copy via
`apps/hermes-manus-poller/` + `operator_task_service.py` — none of the founder's broader vision
(RUES/gov-portal automation, cross-source telemetry, risk-tiered HITL) exists yet. This change
closes the near-term, low-risk gaps (attribution wiring, a trustworthy founder digest, risk-tiered
escalation) while deliberately deferring the two items that carry real tradeoffs (Manus-cloud RUES
automation's data-sovereignty tension; a local OCR upgrade with no current production need) to an
explicit founder decision and a future change, respectively — following this company's own
principle that operational/data order must precede further agentic automation.

## What Changes

- Wire Meta CAPI (server-side Conversions API) and add a `Lead` conversion event, so HubSpot's
  native Meta Ads integration can attribute leads to ad spend using real events instead of
  `PageView` alone.
- Add a founder-facing proactive Telegram digest job (reuses the existing Taty Telegram channel,
  `apps/backend/channels/telegram.py`) reporting ad spend, lead counts, Approval Queue backlog, and
  Manus task status — every field that lacks a real data source reports an explicit
  "no disponible" / "sin datos suficientes" state, never a fabricated number (same discipline as
  `radar-cash-projection`'s `sin_historico_suficiente`).
- Add risk-conditional escalation to the Approval Queue: low-risk, high-confidence items (e.g. ad
  copy variants) can be marked for expedited review; anything touching DIAN filings, client-facing
  tax figures, or Wompi payment links always escalates at the highest tier regardless of confidence.
  This modifies `approval-queue`'s existing uniform pre-approval requirement, it does not replace
  Agent Critic's balanced-entry validation.
- **Explicit non-build, documented as a decision gate**: whether to extend Manus's cloud Browser
  Operator for RUES/Cámara de Comercio automation. Not implemented in this change — `design.md`
  documents the data-sovereignty tension (client NIT/legal-rep data leaving local control) and the
  founder decision required before any future change builds it.
- **Explicit non-build, deferred to backlog**: local OCR upgrade (Mistral OCR 4 / Docling
  self-hosted on Hermes) for messy bank-statement PDFs. Current `pypdf`/`openpyxl` pipeline
  (`real-data-ingestion-mvp`) stays as-is; this is only pulled forward if it fails in production.

## Capabilities

### New Capabilities
- `meta-capi-attribution`: server-side Meta Conversions API wiring plus a `Lead` pixel/CAPI event,
  feeding HubSpot's native Meta Ads conversion mapping.
- `founder-telegram-digest`: a scheduled job assembling and sending a founder-facing GTM/ops digest
  over the existing Telegram channel, with explicit missing-data states.

### Modified Capabilities
- `approval-queue`: adds risk-tiered escalation (confidence × irreversibility) on top of the
  existing uniform pre-approval gate; DIAN/tax-figure/Wompi-payment actions always escalate to the
  highest tier.

## Impact

- **Frontend**: `landing.html`, `contexia-app/app/renta-natural/layout.tsx` (add `Lead` event
  trigger at the real conversion point, e.g. form submit).
- **Backend**: new CAPI-send integration point (`apps/backend`, wherever the lead-creation path
  lives) sending server-side events to Meta; `approval_queue` table gains a risk-tier field and
  classification logic; a new scheduled digest assembler reusing `send_telegram_message`.
- **HubSpot**: native Meta Ads conversion-event mapping configured (config-only, no new code) once
  CAPI events exist.
- **No changes** to `apps/hermes-manus-poller/`, `operator_task_service.py`, or any RUES/OCR-related
  code — those stay exactly as audited, pending the founder's sovereignty decision and future need.
- **Deploy**: Stage 11 applies to the CAPI wiring, digest job, and Approval Queue tiering (all ship
  code to Railway/Vercel). The Manus/RUES decision gate and OCR backlog produce no deployable code
  in this change.
