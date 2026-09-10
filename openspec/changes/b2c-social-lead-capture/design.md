## Context

Verified live against Supabase (project `kpynymwghfwshvcvevxq`, canonical per Decisión #9) and
against `contexia-wizard/`'s own config before designing anything:

- **`crm-b2c-sell-machine`** (already live) defines the real funnel: `crm_leads` (Cliente Cero
  tenant, `stage` in `NUEVOS|PROSPECTOS|POR_APROBAR|LISTOS_CONTADORA`), reachable via the existing
  `POST /api/v1/crm/leads/whatsapp-intake` (find-or-create by phone).
- **`contexia-wizard/`** (a separate Next.js app, `contexia-wizard.vercel.app` per
  `ARCHITECTURE.md`'s stack table) already has a lead-capture flow with a diagnostic wizard
  (`DiagnosticoPDF.tsx`, a `Stepper`) — but **its own `.env.example` points at
  `SUPABASE_URL=https://wzqymuzpjbagnbgsiqig.supabase.co`**, a project confirmed via
  `list_projects` to be **status `INACTIVE`**, not the canonical `kpynymwghfwshvcvevxq`. A `leads`
  table does not exist at all in the canonical project (verified: zero rows returned from
  `information_schema.tables`). **This means the existing wizard's leads never reach `crm_leads`,
  never reach Taty, and may not be capturing anything at all right now if that project is paused.**
  This is treated as a separate, pre-existing piece of orphaned technical debt — flagged here, not
  silently repaired as part of this change's scope (repairing a disconnected legacy app is a
  different decision than building the new social-capture surface this change is actually for).
- **No active request-rate-limiting middleware was found wired in `apps/backend/main.py`**,
  despite `ARCHITECTURE.md`'s stack description naming `slowapi` — this is either stale
  documentation or middleware that exists but isn't mounted; either way, this change cannot rely
  on an existing global rate limiter and must implement its own throttle for the new public,
  unauthenticated endpoint it introduces.

## Goals / Non-Goals

**Goals:**
- Give social ad/organic traffic (Facebook/Instagram/TikTok) a real landing surface that feeds
  the *existing, live* `crm_leads` funnel — not a new, parallel lead store, and not the orphaned
  wizard's disconnected one.
- Capture a lead the moment a valid phone number is entered, even if the visitor abandons the rest
  of the form (Dapta Forms' partial-capture pattern).
- Trigger Taty's first WhatsApp contact within minutes of capture, reusing existing text-delivery
  infrastructure — no new send mechanism, no dependency on the still-gated voice/Twilio capability.

**Non-Goals:**
- Not fixing or reconnecting `contexia-wizard/`'s orphaned Supabase project — flagged as a finding,
  not fixed here.
- Not building campaign analytics/attribution dashboards — the `source` field this change adds is
  enough to query later by hand; a dashboard is a separate, future decision.
- Not designing ad creatives, copy, or targeting — marketing execution outside this repo's scope.
- Not adding a global rate-limiting middleware for the whole backend — scoped narrowly to this
  one new public endpoint.

## Decisions

**1. New page lives in `contexia-app/` (the canonical PWA source), not `contexia-wizard/`.**
`contexia-wizard/` is orphaned (wrong/inactive Supabase project) and its own `.gitignore`/build
setup is a separate Vercel deployment with its own drift risk. `contexia-app/` already deploys to
`contexia.online` and already talks to the canonical backend via `authenticatedFetch`-style
helpers (see `lib/ingestion-api.ts`'s pattern) — this new page reuses that deployment pipeline,
just as an unauthenticated public route.
Alternative considered: fix `contexia-wizard/`'s Supabase config and extend it — rejected for this
change; that is real work (reconnect + verify + probably reconcile a `leads` schema that doesn't
exist anywhere live) that deserves its own decision, not a silent side-quest inside this one.

**2. The capture write path is a NEW, narrowly-scoped public endpoint — not a direct reuse of
`whatsapp-intake` for the partial-capture step.**
`POST /api/v1/crm/leads/whatsapp-intake` requires a tenant-scoped bearer token (per its own spec,
`crm-b2c-sell-machine`'s last requirement) — a public landing page visitor has no such token. This
change adds `POST /api/v1/crm/social-capture/partial` (name to confirm at implementation, unauth,
rate-limited by IP + phone), which internally resolves to Cliente Cero and calls the *same*
underlying `CrmService` find-or-create logic `whatsapp-intake` already uses — not a duplicate
implementation, just a different, public-safe entry point into it.
Alternative considered: make `whatsapp-intake` itself accept unauthenticated calls — rejected,
that would weaken an existing authenticated contract for every other caller for the sake of one
new use case.

**3. Rate limiting: IP + phone-number throttle, implemented locally in this endpoint.**
Given no global limiter is actually wired, this endpoint implements its own simple throttle
(e.g., N requests per IP per minute, and reject a phone number already captured in the last M
minutes to prevent spam-refresh duplicate WhatsApp sends) rather than depending on infrastructure
that turned out not to exist. A full evaluation of whether to actually wire `slowapi` globally is
out of scope — flagged as a separate finding, not fixed here.

**4. First-contact trigger reuses the existing Chatwoot text-delivery path — no voice, no Twilio.**
Once a lead is captured, the same delivery mechanism `taty_lead_router.py` already uses for
outbound WhatsApp text sends the first message. This has zero dependency on
`taty-voice-outbound-calls` (still gated on Twilio approval scope/consent questions) — captures
and first-contacts can ship and go live independently and immediately.

**5. Source/UTM tagging: additive field on `crm_leads`, not a new attribution system.**
A single `source` text field (e.g. `"facebook_ad_renta2026"`, `"instagram_organic"`,
`"tiktok_ad_x"`) captured from the landing page's query string at submission time. No campaign
dashboard, no join to ad-platform APIs — just enough for the founder to run a manual query later
("how many `crm_leads` with `source LIKE 'tiktok%'` converted").

## Risks / Trade-offs

- **[Risk]** A public, unauthenticated capture endpoint is inherently abusable (bot spam, fake
  numbers triggering WhatsApp sends to random people). → **Mitigation**: IP + phone throttle
  (Decision 3); additionally, the outbound WhatsApp first-contact should only fire once per unique
  phone number ever (checked against existing `crm_leads`), not once per form submission — a
  repeat submission from the same number never re-triggers an unwanted message.
- **[Risk]** `contexia-wizard/`'s orphaned state was discovered as a side effect of this design,
  not the point of it — there is a real chance leads have been silently lost there for a while.
  → **Mitigation**: documented explicitly here and in the master plan as its own follow-up item,
  not buried or forgotten; not fixed inside this change's scope.
- **[Trade-off]** No dashboard/analytics for the `source` field at launch. → Accepted: the
  founder can query Supabase directly for now; building a dashboard before there's real campaign
  volume to analyze would be premature.

## Migration Plan

1. New `crm_leads.source` column (nullable, additive — same pattern as `lead_type` from
   `whatsapp-b2b-lead-bridge`, no backfill, no default change to existing rows).
2. Public landing page in `contexia-app/`, with partial-capture-on-phone-entry behavior.
3. `POST /api/v1/crm/social-capture/partial` endpoint: rate-limited, resolves to Cliente Cero,
   reuses `CrmService` find-or-create, stamps `source`.
4. Wire the immediate first-WhatsApp-contact trigger (text only) on successful capture, gated on
   "never sent before to this phone number".
5. Stage 11: deploy, verify with a real test submission end-to-end (form → `crm_leads` row with
   `source` set → real WhatsApp message received), report.

Rollback: the new column is additive; disabling the page/endpoint reverts to the current state
with zero data migration.

## Open Questions

- Exact landing page URL/path (`contexia.online/renta` vs. something else) — founder/marketing
  decision, not decided here.
- Whether `contexia-wizard/`'s orphaned Supabase project should be reconnected, retired, or left
  as-is — a separate decision, flagged but not made here.
- Whether `ARCHITECTURE.md`'s claim that `slowapi` is wired is stale documentation that should be
  corrected, or middleware that exists but isn't actually mounted and should be fixed — flagged,
  not resolved here.
