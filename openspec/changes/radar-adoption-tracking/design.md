## Context

The archived `radar-cash-projection-13w` left one acceptance criterion open: an adoption
event feeding the KPI *"≥40% de usuarios activos abren Radar de Caja al menos 1x/semana"*.
The audit (`.../archive/2026-09-05-radar-cash-projection-13w/reports/2026-09-05-masterprompt-audit.md`,
item C8) records why it was descoped and that it must be closed separately.

Two constraints shape the design. First, `contexia-app/CLAUDE.md` forbids new dependencies
without strong reason, so a third-party tracker is out. Second, the same audit found that the
Shadow GL tables carry permissive `USING (true)` RLS policies — this change must not add
another table with that shape.

## Goals / Non-Goals

**Goals:**
- Make the adoption KPI computable from real data.
- Bounded table growth: one row per tenant + user + day regardless of how many times the
  screen is loaded.
- Genuine tenant isolation at the database level, not just in application code.
- Zero risk to the projection itself.

**Non-Goals:**
- Visualising adoption anywhere. The KPI query below is the deliverable, not a dashboard.
- A general analytics pipeline. One table, one KPI.
- Tracking anything other than "this user opened Radar de Caja on this day".

## Decisions

1. **Record server-side inside `GET /proyeccion-caja`, not via a separate client call.**
   Alternative considered: a `POST /radar/visto` the card fires on mount. Rejected — it adds
   a client round-trip, can be silently dropped by a future refactor of the card, and would
   be the first piece of analytics wiring in `contexia-app`, which its hard rules discourage.
   Recording on the read is the more reliable signal for "the module was opened" and costs
   the client nothing. The trade-off is accepted deliberately: a **read endpoint now has a
   write side effect**, which is unusual and is why it is called out here rather than buried.

2. **Deduplicate per (tenant_id, user_id, opened_on) with partial unique indexes, and a
   plain `INSERT` that tolerates the duplicate.** The KPI is "opened at least once per week", so sub-daily
   resolution buys nothing and would let a polling client or a re-render loop inflate the
   table without bound. A day-grain unique row makes the table's size proportional to actual
   usage. Weekly rollup is then a trivial `date_trunc('week', opened_on)`.

3. **Fail-soft.** The write is wrapped so that any exception — table missing because the
   migration has not been applied yet, RLS rejection, network blip — is logged and swallowed,
   and the projection response is returned unchanged. Telemetry is never allowed to degrade a
   financial read. This also means the code can deploy safely *before* the migration is
   applied.

4. **Real tenant-scoped RLS, copied from migration `0045`,** not the `*_anon_all`
   `USING (true)` pattern the Shadow GL tables use. Authenticated users see only rows for
   tenants they belong to via `user_tenants`; `service_role` retains full access for the
   backend. Adding another permissive table while the audit is actively flagging that pattern
   would be indefensible.

5. **`user_id` is nullable.** The staging identity (`AUTH_ENFORCED=False`, no token) resolves
   to a tenant but has no `auth.uid()`. Rather than drop those opens or invent an id, the row
   is written with `user_id IS NULL`, and the KPI query counts distinct users ignoring nulls.
   The dedupe constraint uses `COALESCE`-free semantics via a partial unique index so nulls
   do not defeat it.

### Two corrections that only the real database revealed

Both were found by running against production Supabase, not by the mocked tests — which
passed throughout. Recorded here because each would have shipped as a **silent no-op**:
fail-soft would have swallowed the error and the table would simply never have filled.

- **The write must use the service-role client, not the anon one.** With the anon key the
  insert evaluates `radar_module_opens_tenant_isolation`, which reads `user_tenants`, whose
  own policy chain raises `42P17 infinite recursion detected in policy for relation
  "user_roles"` — a pre-existing bug unrelated to this change, but fatal to this write. The
  write is not request-controlled (`tenant_id` from the resolved scope, `user_id` from the
  verified JWT), which is exactly what `radar_module_opens_service_role` exists for, mirroring
  the `metrics_snapshots` nightly job. Pinned by a regression test.
- **`upsert(on_conflict=...)` cannot be used, because the dedupe indexes are partial.**
  Postgres cannot infer a partial index for `ON CONFLICT`; the attempt failed with `42P10 no
  unique or exclusion constraint matching the ON CONFLICT specification` and wrote nothing.
  The indexes have to stay partial — Postgres treats NULLs as distinct, so a non-partial index
  would let the NULL-user staging identity insert unbounded rows per day. So the code issues a
  plain `INSERT` and treats `23505` (unique violation) as the normal already-recorded-today
  path, logged at debug rather than warning.

## KPI query (the actual deliverable)

Weekly adoption per tenant — distinct users who opened the module, per ISO week:

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

The ≥40% target is that ratio against active users per tenant, which lives in
`user_tenants` — deliberately not hard-coded here, since "active user" is a product
definition the founder owns, not an engineering constant.

## Risks / Trade-offs

- **[Risk] A read endpoint that writes is surprising to the next reader.** → Mitigation:
  documented in Decision #1, in the endpoint docstring, and covered by a test asserting the
  projection still succeeds when the write raises.
- **[Risk] The migration is not applied and the table does not exist in production.** →
  Mitigation: fail-soft (Decision #3). The endpoint keeps working; opens are simply not
  recorded until the migration lands. Deploy order does not matter.
- **[Trade-off] Day-grain loses time-of-day detail.** Accepted — the KPI is weekly, and the
  bounded-growth property is worth more than resolution nobody asked for.
- **[Trade-off] Counting a fetch as an "open".** A background refetch would count as an open.
  There is no such refetch today (the card fetches once on mount), and day-grain dedupe caps
  the distortion at one row regardless.

## Migration Plan

`0047_radar_module_opens.sql` is additive: `CREATE TABLE IF NOT EXISTS` + indexes + policies.
No existing table or row is modified, so there is nothing to back-fill and nothing to break.
Rollback is `DROP TABLE public.radar_module_opens`. Per this repo's practice for schema
changes (see `ARCHITECTURE.md` Decisions #14/#15, where migrations were applied only with
explicit founder confirmation), applying it to production is a founder-approved step.
