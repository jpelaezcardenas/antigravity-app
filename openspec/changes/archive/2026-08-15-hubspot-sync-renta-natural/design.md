## Context

Renta Natural is a B2C funnel (quiz → lead → WhatsApp/Taty conversation → payment) tracked today only as rows in Supabase `crm_leads`. There is no kanban view, no stage-based reporting, no easy way for the founder to see funnel health at a glance. HubSpot was evaluated (free tier) against the existing Supabase CRM; the founder decided the CRM is not replaced — HubSpot sits alongside it as a commercial/reporting layer. Live verification against the connected HubSpot account (accountId 51867201, STANDARD/free) confirmed the hard constraint that shapes this design: **exactly one deal pipeline** (`pipeline: default`, "Sales Pipeline", 7 stock stages). With only one pipeline available, it is dedicated entirely to the Renta Natural B2C funnel; B2B retainers are not modeled as HubSpot deals.

Existing precedent for external-service polling from a local, credential-sovereign process is `apps/hermes-manus-poller/` — this design reuses that pattern rather than inventing a new one.

## Goals / Non-Goals

**Goals:**
- Give Renta Natural leads (`crm_leads`) a visual pipeline + reporting surface in HubSpot, kept in sync from Supabase.
- Give B2B clients (`b2b_clients`) a lightweight read-only presence in HubSpot (Companies) for cross-referencing, without pretending they belong in a sales pipeline.
- Keep Supabase as the single operational source of truth — no logic anywhere reads HubSpot as authoritative.
- Keep the HubSpot Private App Access Token out of Railway/Vercel entirely — same data-sovereignty posture as decision #1 (Hermes local) and #10 (GBrain local) in `ARCHITECTURE.md`.

**Non-Goals:**
- No bidirectional sync. HubSpot never writes back to Supabase in this change.
- No B2B deal pipeline in HubSpot. B2B retainers stay exclusively in `b2b_clients`/`b2b_payments`.
- No HubSpot workflows/automations (not available on free tier; out of scope even if upgraded later).
- No write actions from the Búnker UI to HubSpot — the badge/link is read-only.
- No handling of HubSpot's 1,000-contact free-tier ceiling — flagged as a future decision, not solved here.

## Decisions

**1. Sync direction: Supabase → HubSpot, one-way.**
Alternative considered: bidirectional sync (e.g., a rep updates deal stage in HubSpot UI). Rejected — introduces a "who's authoritative" conflict the founder explicitly wanted to avoid, and doubles the surface area for bugs. One-way keeps Supabase's existing `crm_leads` state machine as the only source of truth; HubSpot only ever reflects it.

**2. Trigger: Hermes polling, not a Supabase webhook/trigger to a cloud endpoint.**
Alternative considered: Supabase DB webhook → Railway endpoint → HubSpot API. Rejected — would require the HubSpot token to live in Railway, breaking the same data-sovereignty principle already established for Hermes/GBrain (`ARCHITECTURE.md` decisions #1, #10). Polling from Hermes (local/WSL) mirrors `apps/hermes-manus-poller/` exactly: credentials stay local, Hermes reads `crm_leads`/`b2b_clients` deltas on an interval and pushes to HubSpot's API.

**3. Auth: HubSpot Private App Access Token, not full OAuth.**
Alternative considered: OAuth app with refresh-token flow. Rejected as unnecessary complexity for a single-tenant internal integration (Contexia syncing its own data to its own HubSpot account) — a Private App token is HubSpot's documented recommended approach for exactly this case and avoids building/maintaining an OAuth refresh cycle for a Hermes-local script.

**4. Pipeline stage mapping (Sales Pipeline stock stages ← real `crm_leads.stage` values):**

**Correction (2026-08-15):** the original mapping in this section assumed Spanish funnel
stage names ("Quiz Completado", etc.) that do not exist anywhere in the schema. The actual
`crm_leads.stage` column (migration `0022_crm_b2c_sell_machine.sql`) is constrained to exactly
four values: `NUEVOS | PROSPECTOS | POR_APROBAR | LISTOS_CONTADORA`. There is no explicit "lost"
stage on `crm_leads` itself; a lead's payment outcome lives on the related
`crm_wompi_transactions.status` (`PENDING | APPROVED | DECLINED`). The mapping below reflects
the real data the sync code actually reads — the aspirational Spanish names are kept only as
the human-facing label the founder can set in HubSpot's UI (Decision unchanged: relabeling is a
cosmetic, decoupled, founder-doable step).

| `crm_leads.stage` (real) | HubSpot stock stage (value) | Human label (HubSpot UI) |
|---|---|---|
| `NUEVOS` | `appointmentscheduled` | Quiz Completado |
| `PROSPECTOS` | `qualifiedtobuy` | Lead Calificado |
| `POR_APROBAR` | `presentationscheduled` | Contactado |
| `LISTOS_CONTADORA` | `decisionmakerboughtin` | Pago Iniciado |

Additionally, when a lead has a related `crm_wompi_transactions` row:
- `status = 'APPROVED'` → HubSpot Deal `dealstage = closedwon` (overrides the stage-based mapping above)
- `status = 'DECLINED'` → HubSpot Deal `dealstage = closedlost`
- `status = 'PENDING'` (or no transaction) → mapping above applies unchanged

`contractsent` stays unused/reserved, as originally decided.

Alternative considered: renaming the actual HubSpot stage labels via the API to match Spanish funnel names. Originally deferred as a manual founder step; **done 2026-08-15** via `PATCH /crm/v3/pipelines/deals/default/stages/{stageId}` using the Private App token (scope `crm.schemas.deals.write`, confirmed granted) — no HubSpot MCP tool exposes pipeline/stage management, so this used the token directly rather than the connected MCP. Stage internal `value`s (`appointmentscheduled`, etc.) are untouched — only the human-facing `label` changed, so the poller's `stage_mapping.py` needed no code change.

**5. `b2b_clients` → Companies only, never Deals.**
Companies is a distinct HubSpot object from Deals/pipeline — syncing there gives cross-reference value (a rep can look up a B2B account in HubSpot) with zero pipeline contention. Keeps the one free pipeline slot 100% dedicated to Renta Natural, per the founder's decision.

**6. Sync state tracking: new columns on existing tables, not a separate mapping table.**
`crm_leads.hubspot_contact_id`, `crm_leads.hubspot_deal_id`, `crm_leads.last_synced_at`; `b2b_clients.hubspot_company_id`, `b2b_clients.last_synced_at`. Alternative considered: a generic `hubspot_sync_log` join table. Rejected for this scope — two known object types with a strict 1:1 relationship to their Supabase row don't need a generic join table; add one later if a third synced object type appears.

**7. Every tick re-syncs every row — not just unsynced/changed ones (revised 2026-08-15, found
during live verification).**
Two things were tried and reverted before landing here. First: filter via PostgREST's `.gt.`
column comparison in the query string — 400s, because PostgREST parses the right-hand side as a
literal string, not a column reference. Second: filter client-side on `updated_at > last_synced_at`
— self-perpetuates, because the very PATCH that stamps `last_synced_at` fires the table's
`updated_at` trigger, so every synced row looks freshly-updated on the very next tick, forever
(confirmed live: tick 2 resynced all 21 already-synced rows under this scheme). Rather than build
real change detection (a content-hash/version column, or a trigger that skips `updated_at` on
sync-only writes — both real options, deferred), the founder's actual requirement — the HubSpot
pipeline should reflect a lead's live conversation stage with Taty, not a one-time snapshot — is
better served by simply upserting every row every tick. At this scale (~20 rows today) that's a
trivial number of API calls well inside the free-tier rate limit, and it's strictly simpler and
more correct than any partial-sync scheme. Confirmed live: a second tick re-PATCHes all 21 rows
by their stored HubSpot ids (no duplicates), and dealstage updates as `crm_leads.stage`/
`crm_wompi_transactions.status` change between ticks.

## Risks / Trade-offs

- **[Risk]** Free-tier 1,000-contact ceiling could be hit if Renta Natural leads scale fast. → **Mitigation**: `last_synced_at` + row counts make it trivial to monitor; flag as an explicit follow-up decision (upgrade vs. cap sync) before it becomes a silent failure.
- **[Risk]** Hermes polling interval means HubSpot state lags Supabase (not real-time). → **Mitigation**: acceptable per Goals — HubSpot is a reporting/commercial layer, not the operational surface; document the expected lag (e.g., every N minutes) in the poller's own docs.
- **[Risk]** Stock stage labels in English (`Appointment Scheduled`, etc.) will look wrong to the founder in the HubSpot UI until manually relabeled. → **Mitigation**: documented as an independent manual step (Decision #4), not a blocker to shipping the sync.
- **[Risk]** If Hermes is offline, sync silently stops with no alert. → **Mitigation**: reuse whatever staleness/health-check pattern `apps/hermes-manus-poller/` already has, if any; otherwise flag as a task for a minimal `last_synced_at` staleness check surfaced in the Búnker badge (e.g., badge shows "Sincronizado ✓" only if `last_synced_at` is recent, otherwise a neutral "sin sincronizar" state — never a false-positive check).
- **[Trade-off]** No relabeling automation for stage names means the pipeline reads in English out of the box. Accepted — cosmetic, one-time, founder-doable in the HubSpot UI directly.

## Migration Plan

1. Add sync-state columns to `crm_leads` and `b2b_clients` (additive migration, no backfill required — `last_synced_at` starts NULL, meaning "never synced").
2. Build the Hermes poller module (new directory alongside `apps/hermes-manus-poller/`), reading the Private App token from local Hermes config/secrets, never from a repo-committed file.
3. Implement Contact+Deal upsert for `crm_leads`, Company upsert for `b2b_clients`, idempotent on the new `hubspot_*_id` columns.
4. Add the read-only Búnker badge/link component, sourced from the new columns. **Correction (2026-08-15):** the Búnker does NOT read Supabase directly — `B2cKanbanTab.tsx`/`B2bRetainersTab.tsx` call `apps/backend/presentation/crm_endpoints.py` (Railway), which projects an explicit column list from `crm_service.py`. No new endpoint was needed, but the existing `list_b2b_clients`/`b2b_payments_grid`/`b2c_pipeline` selects had to be extended to include `hubspot_*_id`/`last_synced_at` so the new columns actually reach the frontend types.
5. Deploy: Stage 11 applies only to the Búnker frontend change (Vercel) and the Supabase migration — the Hermes poller itself is a local process, not a Railway/Vercel deploy, so its "deployment" is starting/enabling the Hermes-local worker and confirming a first successful sync in HubSpot's UI.
6. Rollback: disable/stop the Hermes poller process (no HubSpot writes continue); the Búnker badge simply shows unsynced state; Supabase columns are additive and safe to leave in place even if HubSpot integration is later abandoned.

## Open Questions

- What Hermes polling interval is acceptable (real-time-ish vs. every few minutes)? Defer to whatever `apps/hermes-manus-poller/` already uses as a default, unless the founder wants a different cadence for sales-facing data.
- Should `contractsent` stage be repurposed (e.g., "Oferta Enviada") or left unused? Founder call, doesn't block implementation.
- At what lead volume does the 1,000-contact free-tier ceiling become a real risk, and who owns watching for it?
