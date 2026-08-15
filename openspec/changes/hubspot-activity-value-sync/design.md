## Context

The archived `hubspot-sync-renta-natural` poller upserts Contacts/Deals/Companies but writes nothing about the actual conversation or money involved. Free-tier HubSpot has no workflows, but the Engagements API (Notes, Tasks) is available on the same Private App scopes already granted (`crm.objects.contacts.write`, `crm.objects.deals.write` cover associated engagement writes).

## Goals / Non-Goals

**Goals:**
- Give the founder visible conversation history and deal value inside HubSpot without leaving it.
- Reuse existing poller cadence (every 5 min) and existing Supabase columns — no new migration.

**Non-Goals:**
- Not building two-way sync (HubSpot Notes never write back to Supabase/Chatwoot).
- Not deduplicating Notes if `last_message` is re-synced unchanged — every tick logs it is out of scope here (see Decisions).

## Decisions

**1. Note logs the CURRENT `last_message` every tick, not just on change.**
Alternative considered: only create a Note when `last_message` differs from the last-logged one (would need a new tracking column). Rejected for this scope — at ~15 leads/5-min cadence, a duplicate identical Note every 5 minutes would spam the timeline. Instead: log a Note only when `last_message` is non-empty AND the lead's `last_synced_at` was previously NULL (i.e., on first sync) for now; a real "log every new message" trigger needs a `last_logged_message` tracking column, deferred as a fast-follow once this ships and the founder confirms the timeline is useful. This keeps scope small and avoids spam while still giving initial conversation context.

**2. Deal `amount` uses the latest Wompi transaction regardless of status.**
An `APPROVED` transaction's amount is the real deal value; a `PENDING`/`DECLINED` one still tells the founder what was being offered. Simpler than branching logic, and `dealstage` already carries the win/loss signal (Decision #4 in the archived change).

**3. Task creation is one-shot per lead reaching `POR_APROBAR`, gated on the Deal not already having an open task.**
To avoid creating a duplicate Task every 5-minute tick while a lead sits in `POR_APROBAR` waiting for approval, the poller checks for an existing incomplete Task associated with the Deal before creating a new one (one extra API call, only for leads in that stage — a small subset).

**4. Stale HubSpot ids self-heal via create-on-404 (found live 2026-08-15, out of original scope but fixed here since it blocked verifying this change).**
A live tick against production hit `404 Not Found` on every PATCH to a previously-synced Contact — HubSpot's own contact deduplication/merge had silently retired the ids `hermes-hubspot-poller` had stored, and the poller had no fallback, so `_sync_lead` failed closed for all 5 real leads. `_upsert_object` (`hubspot_client.py`) now treats a PATCH 404 the same as "no stored id": create a fresh object instead of failing the sync. `mark_lead_synced`/`mark_b2b_client_synced` then persist whatever id the upsert returns, so the stale id is naturally replaced.

## Risks / Trade-offs

- **[Risk]** Note-on-first-sync-only (Decision #1) doesn't give a live conversation feed. → **Mitigation**: documented as a known limitation; a `last_logged_message` column is the clean fast-follow if the founder wants live history.
- **[Risk]** Extra API calls per tick (notes, task-existence checks) increase HubSpot API usage. → **Mitigation**: at ~15 leads this is trivially within free-tier rate limits.
