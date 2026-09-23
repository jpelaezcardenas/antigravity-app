## Context

A 2026-09-23 repo audit + SOTA research brief established the real gap between the founder's
"empresa 4.0" aspiration and what exists today:

- **Meta Pixel** (`landing.html`, `contexia-app/app/renta-natural/layout.tsx`, since commit
  `8d47a366`) fires `PageView` only. No `Lead` event, no server-side Conversions API (CAPI).
- **HubSpot poller** (`apps/hermes-hubspot-poller/`, spec `hubspot-lead-sync`) syncs `crm_leads` →
  Contacts/Deals and `b2b_clients` → Companies, but nothing links ad-spend or pixel data to it.
- **Telegram** (`apps/backend/presentation/telegram_endpoints.py::send_telegram_message`,
  `chat_id: int, text: str`) is wired and live, used today only reactively by Taty.
- **Approval Queue** (spec `approval-queue`) gates every draft uniformly via Agent Critic balance
  validation — no risk tiering exists.
- **Manus** (`apps/hermes-manus-poller/` + `apps/backend/services/operator_task_service.py`) calls
  Manus API v2 (`task.create`/`task.detail`/`task.listMessages`) for ad-copy generation only. Its
  Browser Operator (RUES/gov-portal automation capability) is unused.
- Lead capture entry point is `apps/backend/presentation/social_capture_endpoints.py::
  social_capture_partial`, which is where a `Lead` conversion event would need to fire from.

This company's own settled architecture (`ARCHITECTURE.md` Decisions #1/#10/#26) requires
financial/client data to stay on local Hermes compute — cloud agent platforms are never a default
for data with that sensitivity. RUES lookups touch client NIT/legal-representative data, which sits
in a gray zone relative to that rule and has NOT been decided by the founder. This design
deliberately does not resolve that decision; it documents it as a gate for a future change.

## Goals / Non-Goals

**Goals:**
- Close the CAPI/Lead-event gap so HubSpot's native Meta Ads mapping can attribute real
  conversions, not just page views.
- Give the founder a trustworthy, low-noise proactive digest — never a number without a real
  source.
- Add risk-tiered escalation to Approval Queue without weakening its existing Agent Critic
  validation for journal-entry drafts.
- Explicitly surface, not silently resolve, the Manus/RUES sovereignty question.

**Non-Goals:**
- Building or wiring Manus's Browser Operator for RUES/Cámara de Comercio automation. Requires an
  explicit founder decision (see Open Questions) and, if approved, a separate future change.
- Any local OCR upgrade (Mistral OCR 4 / Docling) for bank-statement PDFs. Current
  `pypdf`/`openpyxl` pipeline (`real-data-ingestion-mvp`) is not failing in production; revisit only
  if it does.
- Changing Agent Critic's balanced-entry validation logic for journal drafts.
- Building a general-purpose BI/aggregation layer. The digest reads existing tables directly; it is
  not a new analytics platform.

## Decisions

**1. CAPI send point: server-side, at `social_capture_partial`, not client-side duplication.**
Firing `Lead` from the client (`fbq('track','Lead')`) alone is unreliable (ad blockers, ITP/ATT).
The authoritative event fires server-side from `social_capture_partial` (the real lead-creation
path) using Meta's Conversions API, with the client-side pixel event kept as a redundant/lower-
confidence secondary signal per Meta's own event-matching guidance. Alternative considered: client-
only pixel event — rejected because it's exactly the fragility the SOTA research flagged (42%+ of
desktop traffic runs ad blockers).

**2. No new telemetry aggregation service — HubSpot's native Meta Ads mapping does the joining.**
Once CAPI events exist, HubSpot's built-in Ads→CRM conversion mapping (already used by the existing
`hubspot-lead-sync` poller pattern) closes the attribution loop without Contexia building or
maintaining a custom BI layer. Alternative considered: a custom Supabase table joining pixel events
to `crm_leads` — rejected as unnecessary engineering surface when HubSpot already does this natively
and the marketing agency can operate it from the UI.

**3. Digest job reuses `send_telegram_message`, not a new bot/channel.**
A new scheduled job (mirroring the pattern of Contexia's existing 8 Hermes Scheduled Jobs) calls the
already-live `send_telegram_message(chat_id, text)` to the founder's chat ID. Alternative
considered: a dedicated founder-only bot — rejected as unnecessary infra duplication; the existing
Taty bot already reaches the founder's Telegram.

**4. Digest fields with no real data source render an explicit "no disponible" state.**
Follows the precedent already established in `radar-cash-projection` (`sin_historico_suficiente`)
and `pricing-quote-engine` (`uvt_no_disponible`). A digest field is either backed by a real query or
it says so plainly — it is never estimated or omitted silently. Cadence is daily, not per-event, per
the SOTA research finding that per-event alerts cause fatigue and get muted by day 10.

**5. Approval Queue risk tiering is additive: a new field, not a new table or a replacement gate.**
`approval_queue` gains a risk-tier classification (confidence × irreversibility) computed at
enqueue time. Items touching DIAN filings, client-facing tax figures, or Wompi payment links are
hard-coded to the highest tier regardless of computed confidence — this is a safety floor, not a
suggestion the classifier can override. Agent Critic's existing balance validation
(`is_valid`/`reason`) runs unchanged and independently; risk tier only affects review routing/SLA,
never whether a draft is accepted into the queue.

**6. Manus/RUES: decision gate, not a default.** Manus's Browser Operator is capability-adequate for
RUES/Cámara de Comercio lookups (confirmed via SOTA research), but it executes in Manus's cloud VM,
meaning client NIT/legal-rep data would leave local control — a materially different sensitivity
profile than the ad-copy generation Manus already does. This change does not extend
`operator_task_service.py`'s task types to include browser-operator RUES tasks. The founder must
explicitly choose between (a) accepting that data-sovereignty tradeoff for this specific use case,
or (b) running a locally-hosted Browser Use/Skyvern instance on the Hermes machine instead, before
any future change builds this.

## Risks / Trade-offs

- **[Risk]** CAPI event-matching quality (email/phone hashing) may be poor if `social_capture_partial`
  doesn't already capture matchable PII cleanly. → **Mitigation**: verify actual payload fields
  during implementation (task-level, not a design blocker); Meta's mapping degrades gracefully with
  partial match keys, it doesn't hard-fail.
- **[Risk]** A daily digest can still become noise if every field is populated even when nothing
  changed. → **Mitigation**: task-level requirement that the digest highlights deltas/anomalies, not
  just raw snapshots, per the SOTA "why it matters" framing — but the core promise (no fabricated
  numbers) is the hard requirement.
- **[Risk]** Hard-coded highest-tier escalation for DIAN/tax/Wompi actions could be bypassed by a
  future task type that touches these without matching the keyword/pattern classifier. →
  **Mitigation**: classifier list is a fail-closed allowlist gap, not fail-open — flagged as an open
  question below rather than silently accepted.
- **[Trade-off]** Deferring Manus/RUES means the founder's original "empresa 4.0" vision stays
  partially unrealized after this change ships. This is intentional: shipping it without the
  sovereignty decision would violate this repo's own settled architecture rules.

## Migration Plan

- CAPI wiring and digest job are additive — no schema migration beyond the `approval_queue`
  risk-tier column (nullable, defaulted, non-breaking).
- Deploy order: (1) CAPI send point + HubSpot Ads mapping config, verified with live Meta Events
  Manager test events before removing test mode; (2) digest job, first run manually verified before
  scheduling; (3) Approval Queue risk-tier field + classifier, deployed behind existing HITL gate
  (classifier only affects routing, never bypasses approval).
- Rollback: CAPI can be disabled by removing the server-side send call (pixel `PageView` keeps
  working). Digest job is a cron/Scheduled Task — stopping it is a config change, not a code
  rollback. Risk-tier column can be ignored (routing falls back to uniform review) without a
  migration rollback.
- Stage 11 (deploy to production) applies to all three shipped items per `CLAUDE.md` §8.

## Open Questions

- **Founder decision required**: Manus cloud Browser Operator vs. locally-hosted Browser
  Use/Skyvern for future RUES/Cámara de Comercio automation. Not resolved in this change.
- What is the founder's actual Telegram `chat_id` for the digest target, and should it also reach
  Tatiana (Entidad A) for approval-queue-related fields, or founder-only? Founder-only is proposed,
  since Approval Queue already notifies via Chatwoot/Bunker per Decision #14.
- Does `social_capture_partial`'s current payload already carry email/phone in a form usable for
  Meta's CAPI hashed-match keys, or does the capture form need a field added first? To be confirmed
  during implementation.
- Exact keyword/pattern list for the "always highest-tier" classifier (DIAN/tax/Wompi) — to be
  drafted as part of task implementation, reviewed against real `operator_tasks`/`approval_queue`
  history for completeness.
