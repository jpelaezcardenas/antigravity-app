# Design: freemium-tenant-minimum-seed

## Context

The master plan (Subdomain 5) left an explicit open design question: seed a minimal synthetic
Shadow GL balance for a new freemium tenant, or depend entirely on Subdomain 6's (much larger,
undesigned) agent-insight bridge. Investigation of migrations `0028` and `0035` resolves this
cheaply.

## Decision D1 — Seed sintético, not depend on Subdomain 6

Reuse migration `0028`'s exact `SYNTH-{nit}-OPEN` / `SYNTH:per-tenant-client-access` naming
convention for a single opening-balance journal entry, written only into the new tenant's own
`erp_journal_entries`/`erp_journal_lines`.

**Why not wait for Subdomain 6**: Subdomain 6 is explicitly the largest, least-designed item in
the plan (new agent pipeline, Hermes poller coordination, new endpoint, new fallback-source logic
in `CashTodayCard`). Blocking a freemium lead's first-screen experience on that is not compatible
with "camino más rápido a la venta #1." The seed is a ~1-day change; Subdomain 6 remains the
durable long-term answer and can layer on top later without conflict (different data source,
same UI consumer).

**Why this reuse is safe**: migration `0028`'s pattern is already proven in production for the 10
seeded B2B clients. `financials_service.py::compute_pulso_daily_snapshot` reads `caja_real` as the
running balance of account `1110` across all journal lines for the tenant — an `-OPEN` entry alone
is sufficient to make `caja_real` non-zero, with no dependency on any `-SALE`/`-EXPENSE` row.

## Decision D2 — Only seed the opening balance, not synthetic yesterday's sale/expense

Migration `0028` also seeds `-SALE` (account `4105`) and `-EXPENSE` (account `5135`) entries, kept
fresh forever by the existing rolling-reseed cron (`0035`). This change deliberately does **not**
reuse that part of the pattern for freemium tenants.

**Why**: `-SALE`/`-EXPENSE` fabricate "yesterday's business activity" for a lead who, by
definition, has done nothing in the product yet. Showing "Ventas de ayer: $2,000,000" for a brand
new signup is dishonest in a way an opening balance is not — an opening balance reads as "here is
the starting capital you told us about," while a fabricated sale reads as invented history. This
also keeps the change genuinely minimal (an `-OPEN` entry is a single `IF NOT EXISTS` guard + one
journal entry + two lines — no interaction with the reseed cron at all, since `0035`'s WHERE clause
only matches `-SALE`/`-EXPENSE` suffixes, never `-OPEN`).

**Consequence**: `ventas_ayer`/`gastos_ayer` on a fresh freemium tenant's `CashTodayCard` correctly
show 0 (not fabricated) while `caja_real` shows the seeded opening balance — an honest partial
"ready" state, not an "empty" one.

## Decision D3 — Where the seed is triggered: inside `create_b2b_client`, gated to freemium

`create_b2b_client` (Subdomain 4) already validates `plan_tier` and writes it to both `tenants`
and `b2b_clients` in one call. Adding `opening_balance_cents` as one more optional parameter to
that same call — rather than a separate endpoint — keeps the alta flow a single atomic step from
the vendor's perspective, matching the master plan's own wording ("agregar un paso opcional
'saldo de apertura' al flujo de alta del subdominio 4").

Gate: the seed fires only when `plan_tier == "freemium"` AND `opening_balance_cents` is provided
and `> 0`. For any other tier, the field is accepted but ignored (paid tiers get real Siigo/DIAN
data, not a synthetic seed) — this is a deliberate no-op, not a validation error, so the frontend
doesn't need tier-conditional request shaping beyond hiding the field.

## Decision D4 — Idempotency and isolation

`seed_freemium_opening_balance(tenant_id, nit, opening_cents)` checks for an existing
`external_reference_id = f"SYNTH-{nit}-OPEN"` row scoped to `tenant_id` before inserting — mirrors
`0028`'s own `IF NOT EXISTS` guard, so a retried alta request (e.g. a double-click) never
double-seeds. `tenant_id` is always the newly created tenant's own id (never Cliente Cero's,
never another tenant's) — sourced directly from the `tenants` insert result already present in
`create_b2b_client`, not looked up separately.

## Out of scope

- Any change to `financials_service.py` — account codes `1110`/`3105` are already correctly
  classified for `caja_real`.
- Any change to the rolling-reseed cron (`0035`) — an `-OPEN` entry is never matched by its WHERE
  clause, by design (opening balances are static, not "yesterday" data).
- Seeding for non-freemium tiers — paid tiers are expected to onboard real Siigo/DIAN data via
  existing ingestion, not a synthetic seed.
- Subdomain 6 (agent-insight bridge) — remains a separate, later change; this seed and that bridge
  are different data sources feeding the same UI consumer (`CashTodayCard`), not competing designs.
