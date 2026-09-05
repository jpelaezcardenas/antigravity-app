# Deployment report — radar-adoption-tracking

**Date:** 2026-09-05
**Change:** Adoption tracking for Radar de Caja — closes the last open acceptance criterion
of the archived `radar-cash-projection-13w`
**Deployed by:** Claude Opus 5 session, authorized by the founder

## What shipped

| Surface | What | Where |
|---|---|---|
| Database | `radar_module_opens` table + tenant-scoped RLS (migration `0047`) | Supabase `kpynymwghfwshvcvevxq` — **applied** |
| Backend | `record_module_open()` + wiring into `GET /api/v1/radar/proyeccion-caja` | Railway `antigravity-app-production-175a` |
| Docs | `ARCHITECTURE.md` Radar bullet now states the telemetry side effect | repo |
| Frontend | none | — |

**Commit:** `353dc7e`

## Verification

- **Dedupe, against the real database:** 1 call → 1 row; 3 calls → still 1 row; cleanup → 0.
- **Migration:** applied to production Supabase; table, both partial unique indexes, the
  rollup index and both policies exist.
- **RLS:** `radar_module_opens_tenant_isolation` scopes reads through `user_tenants`;
  `radar_module_opens_service_role` lets the backend write for any tenant. Deliberately
  **not** the `USING (true)` shape the Shadow GL tables carry.
- **Tests:** 7 new, all green. Full radar suite green apart from the one pre-existing,
  unrelated failure in `test_radar_alert_count_tenant_scoping.py` (verified against a stash
  of this change's diff during the previous change, and unchanged since).
- **Backend health after deploy:** `/api/v1/health` 200; `/api/v1/radar/proyeccion-caja`
  still 401 without a token — the telemetry write did not alter the endpoint's contract.

## Two bugs the mocked tests could not catch

Both would have shipped as a **permanent silent no-op**: the write fails, fail-soft swallows
it, and the table never fills. Neither was visible in the unit tests, which passed throughout.
Both were found by running the real function against the real database.

1. **Wrong Supabase client.** `record_module_open` initially used `get_supabase()` — the
   **anon** key. With that key the insert evaluates the table's tenant-isolation policy, which
   reads `user_tenants`, whose own policy chain raises
   `42P17 infinite recursion detected in policy for relation "user_roles"`. Pre-existing and
   unrelated to this change, but fatal to this write. Fixed to `get_service_supabase()` and
   pinned with a regression test so a refactor cannot quietly undo it.

2. **`upsert(on_conflict=...)` cannot infer a partial index.** The dedupe indexes must be
   partial — Postgres treats NULLs as distinct, so a non-partial unique index would let the
   NULL-user staging identity insert unbounded rows per day. Postgres cannot use a partial
   index for `ON CONFLICT` inference, so the upsert failed with
   `42P10 no unique or exclusion constraint matching the ON CONFLICT specification` and wrote
   nothing. Replaced with a plain `INSERT` that treats `23505` as the normal
   "already recorded today" path, logged at debug rather than warning.

**Rule earned:** *fail-soft telemetry must be verified against the real datastore before it is
called done. A passing mock proves the call shape, not that a single row ever lands.*

## Pre-existing issues surfaced, not fixed here

- `public.user_roles` has a recursive RLS policy (`42P17`). Any anon-key query that
  transitively evaluates it fails. Worth its own change.
- The Shadow GL tables (`erp_journal_entries`, `erp_journal_lines`, `dian_xml_documents`)
  carry `USING (true)` policies for `{anon, authenticated, service_role}` — no database-level
  tenant isolation. See the masterprompt audit for the full finding.

## How to read the KPI

```sql
SELECT tenant_id,
       date_trunc('week', opened_on)::date AS week_start,
       COUNT(DISTINCT user_id) FILTER (WHERE user_id IS NOT NULL) AS users_opened,
       COUNT(*) AS total_opens
FROM public.radar_module_opens
WHERE opened_on >= CURRENT_DATE - INTERVAL '8 weeks'
GROUP BY tenant_id, date_trunc('week', opened_on)
ORDER BY week_start DESC, tenant_id;
```

The table is empty until real users open the screen. Note the honest caveat inherited from
the audit: with the Shadow GL effectively empty, every client currently sees the
"not enough history yet" state, so early adoption numbers measure curiosity about an empty
state, not engagement with a projection.
