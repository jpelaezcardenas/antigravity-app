## Why

Ola 4 of the founder-approved integration plan (2026-08-14) identified a real gap: "hoy no existe:
nadie detecta que un cliente se está yendo." Confirmed via code search this session — no
retention/churn detection exists anywhere in `apps/backend`. The signal already exists, though:
`b2b_payments` (seeded via `crm-b2b-retainers`, archived 2026-07-19) has one row per client per
calendar month; a client with no payment recorded in the most recent months, or one whose latest
payment dropped sharply against their own trailing average, is a real churn/risk signal nobody is
watching.

## What Changes

- New `apps/backend/services/retention_service.py`: a small rule-based evaluator modeled on
  `centinela_service.py`'s `CentinelaRule` pattern (separate module, since this is about the B2B
  roster's health, not a client's own fiscal data) — two initial rules: **missed payment** (no
  `b2b_payments` row for an `activo` client in the most recent complete month) and **payment drop**
  (latest payment `amount_cents` is materially below the client's own trailing 3-month average).
- New `retention_alerts` table (mirrors `centinela_alerts`' shape: `id`, `tenant_id`, `client_id`,
  `rule_id`, `severity`, `message`, `created_at`) — alerts are persisted and queryable, not
  recomputed-and-discarded on every read, same reasoning as Centinela's own alert history.
- `GET /api/v1/crm/b2b/retention-alerts` (new endpoint, same auth/tenant convention as the existing
  `crm_endpoints.py` routes) triggers evaluation and returns current + recent alerts.
- Búnker: surface alerts inside the existing "CRM / Ventas" → "B2B / Retainers" tab
  (`B2bRetainersTab.tsx`) — no new top-level Búnker section, reusing existing UI real estate and
  the existing `crm-api.ts` fetch pattern.

## Capabilities

### New Capabilities
- `retention-loop`: B2B client churn/risk detection, persisted alert history, and Búnker
  visibility.

### Modified Capabilities
- `crm-b2b-retainers`: the "CRM/Ventas Búnker section renders the live B2B grid" requirement gains
  a retention-alerts panel alongside the existing grid — same tab, same data-bound conventions
  (loading/error/empty states, no mock fallback in the UI layer).

## Impact

- `apps/backend/services/retention_service.py` (new)
- `apps/backend/migrations/` (new: `retention_alerts` table)
- `apps/backend/presentation/crm_endpoints.py` (modified: new `GET .../retention-alerts` route)
- `contexia-app/lib/crm-api.ts` (modified: new fetch function + types)
- `contexia-app/components/bunker/crm/B2bRetainersTab.tsx` (modified: alerts panel)
- `openspec/specs/crm-b2b-retainers/spec.md` (delta: retention alerts panel requirement)
- New capability spec `openspec/specs/retention-loop/spec.md`
- No change to `b2b_payments`/`b2b_clients` schemas — read-only consumer of existing data.
