## Context

`b2b_payments` has one row per `(client_id, period)` with `amount_cents`. `crm_service.py`'s
`b2b_payments_grid()` already reads and pivots this data for display. Nothing evaluates it for
risk. `centinela_service.py` shows the exact pattern this repo already uses for "evaluate a set of
rules against data, persist triggered alerts, read them back" — `CentinelaRule` subclasses +
`CentinelaService.evaluate()`/`save_alerts()`/`get_alerts_for_company()` — and
`crm_endpoints.py`/`B2bRetainersTab.tsx`/`crm-api.ts` show the exact pattern for a new CRM
read-mostly endpoint reaching the Búnker.

## Goals / Non-Goals

**Goals:** detect the two clearest, already-computable risk signals (missed payment, payment drop)
from data that already exists; persist alerts so there's a history, not just a live recompute;
surface them where the founder already looks (the B2B/Retainers tab).

**Non-Goals:**
- Not building a notification/email system — alerts are visible in the Búnker on demand, no
  outbound messaging (matches this repo's "no Supabase SMTP / no invite emails" precedent from
  `per-tenant-client-access`).
- Not a scheduled/cron evaluation — the endpoint evaluates on-demand when the tab loads, same as
  `b2b_payments_grid()` computing its pivot on every call. A cron/schedule is a natural follow-up
  once there's a concrete need for alerts to exist without someone opening the tab, not required to
  close today's gap.
- Not HubSpot integration — out of scope for this change (being handled in a separate thread per
  the founder).
- Not predictive/ML churn scoring — two explicit, explainable rules only, matching Centinela's own
  "explicit rule, not a model" philosophy.

## Decisions

**1. Separate `retention_service.py`, not a new `CentinelaRule` subclass.** Centinela's rules
evaluate a single client's own fiscal `data` dict (UVT, retention, margins) — retention risk
instead needs the *roster-wide* payment history across all B2B clients to compute each client's own
trailing average. Reusing `CentinelaRule`'s single-record shape would force an awkward pre-fetch
step; a small dedicated module with the same "rule → evaluate → alert dict" shape keeps the pattern
recognizable without forcing a mismatched abstraction.

**2. `retention_alerts` mirrors `centinela_alerts`' columns exactly** (`id`, `tenant_id`,
`client_id`, `rule_id`, `severity`, `message`, `created_at`) — no schema decisions to relitigate,
and any future admin tooling that already knows how to read `centinela_alerts` generalizes for
free.

**3. Both rules key off `b2b_clients.status == 'activo'` only.** An `inactivo` client isn't a churn
risk, it's already churned (or was never fully onboarded) — evaluating it would just add noise.

**4. "Missed payment" checks the most recently *complete* calendar month, not the current
in-progress one.** A client billed on the 28th shouldn't show as at-risk on the 3rd of the next
month just because that month's row hasn't landed yet.

**5. "Payment drop" needs at least 3 prior months of payment history before it fires.** Fewer than
3 data points makes "trailing average" noisy to the point of being misleading (e.g. a client's
first-ever payment always looks like a 100% drop from "nothing"). New clients are simply not
evaluated by this rule until they have enough history — not a bug, a threshold.

## Risks / Trade-offs

- **[Risk] A client who pays via a different cadence (e.g. quarterly) triggers false "missed
  payment" alerts every non-payment month.** No B2B client in the current seeded roster has a
  non-monthly cadence (confirmed against `crm-b2b-retainers`' seed data), so this isn't a live
  problem today; if a non-monthly client is onboarded later, this rule needs a per-client cadence
  field — flagged as a known limitation, not silently ignored.
- **[Trade-off] On-demand evaluation (Non-Goal: no cron) means alerts only refresh when the tab is
  opened.** Accepted for the same reason `b2b_payments_grid()` already works this way — the founder
  is the only consumer today, and this matches existing operational rhythm rather than adding a new
  scheduled job with its own failure modes to monitor.

## Migration Plan

1. Failing tests first: each rule's `evaluate()` in isolation (missed payment fires/doesn't per the
   complete-month boundary; payment drop fires/doesn't per the 3-month-history threshold and
   drop-percentage math); `RetentionService.evaluate_roster()` aggregates correctly across clients;
   `save_alerts()`/`get_alerts()` persist and read back scoped to `tenant_id`.
2. Implement `retention_service.py`.
3. Migration: create `retention_alerts` table (RLS admin-only, same policy shape as
   `centinela_alerts`/`b2b_clients`).
4. Implement `GET /api/v1/crm/b2b/retention-alerts` in `crm_endpoints.py`.
5. Frontend: `crm-api.ts` fetch function + types; `B2bRetainersTab.tsx` alerts panel with explicit
   loading/error/empty states (no mock fallback in the UI layer, per this tab's existing
   data-bound convention).
6. Sync the `retention-loop` (new) and `crm-b2b-retainers` (delta) specs.
7. Stage 11: deploy, verify via Supabase MCP that the migration applied and via a live Búnker check
   (screenshot) that the panel renders.

## Open Questions

None blocking.
