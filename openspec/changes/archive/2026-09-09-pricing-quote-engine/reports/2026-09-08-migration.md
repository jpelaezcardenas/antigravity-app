# Migration 0048 — applied to production (2026-09-08)

**Authorisation:** explicit founder approval, given for the migration **only**. The push and the
deploy were offered alongside it and were **not** authorised — they remain pending.

**Target:** Supabase project `kpynymwghfwshvcvevxq` (production).
**Applied via:** Supabase MCP `apply_migration`, name `uvt_values_and_service_band`.
**Result:** `{"success": true}`.

## Pre-state (verified immediately before applying)

| Object | State |
|---|---|
| `public.uvt_values` | did not exist (`to_regclass` → `null`) |
| `b2b_clients.service_band` | absent |
| `b2b_clients` row count | 11 |

## Post-state (verified live, not assumed)

**`uvt_values` seed — both rows present, values matching their cited resolutions:**

| year | value_cop | resolution |
|---|---|---|
| 2025 | 49799 | Resolución DIAN 000193 de 2024 |
| 2026 | 52374 | Resolución DIAN 000238 del 15 de diciembre de 2025 |

Stored in **whole pesos**, as designed — `49799`, not `4979900`. The two live UVTs are distinct
rows, preserving the 2026 duality (UVT 2025 governs año-gravable-2025 obligation thresholds;
UVT 2026 governs 2026 sanctions and withholding).

**`b2b_clients.service_band`:**

- column exists, `is_nullable = YES`, `column_default = NULL`
- rows with a non-null band: **0 of 11** — no client was silently assigned a band, which was the
  point of shipping it with no default
- CHECK constraint present, definition read back from `pg_constraint`:
  `CHECK (((service_band IS NULL) OR (service_band = ANY (ARRAY['micro'::text, 'estandar'::text, 'complejo'::text]))))`

**RLS on `uvt_values`** — enabled (`relrowsecurity = true`), 2 policies, read/write correctly
split rather than one permissive `FOR ALL USING (true)`:

| policy | cmd | roles | qual | with_check |
|---|---|---|---|---|
| `uvt_values_read_all` | SELECT | public | `true` | — |
| `uvt_values_service_role_write` | ALL | service_role | `true` | `true` |

## Why this is safe to leave applied while the code is unpushed

The migration is purely additive and the currently-deployed backend references neither object:
production code does not select `service_band` and does not read `uvt_values`. A new table and a
new nullable column that no running code touches are inert.

This is also the correct order. The hazard runs the other way: `CrmService.list_b2b_clients` (in
the unpushed commit) projects `service_band`, and its `except` branch falls back to **demo
data** — so shipping the code first would have made the Búnker's B2B roster silently display
demo clients. That risk is now closed ahead of any deploy.

## Rollback, if ever needed

```sql
DROP TABLE public.uvt_values;
ALTER TABLE public.b2b_clients DROP COLUMN service_band;
```

No existing data is destroyed by either statement — `service_band` holds no values, and
`uvt_values` contains only the two public legal reference rows.

## Still pending (not authorised)

1. `git push -u origin feat/pricing-quote-engine` — no production effect; `main` is the deploy
   branch.
2. Merge to `main` — **this** is the Vercel + Railway production deploy. Now unblocked from the
   database side.
