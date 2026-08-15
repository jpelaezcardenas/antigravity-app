# metrics-dashboard-phase9 — DEFERRED

**Date deferred:** 2026-08-13 (pre-GTM tech-debt triage)
**Status:** 0/108 tasks started. Not archived — left in `changes/` as a tracked, intentional
deferral, not an accidental stall.

## Why deferred

Restoring the "one change at a time" invariant (HARNESS.md) required triaging 11 accumulated
active changes down to a small number before the GTM integration push (Siigo + DIAN + Wompi +
production multi-tenant). This change is large (108 tasks across 5 stages: schema, backend API,
frontend layout, chart rendering, testing/deploy) and has zero engineering investment yet — it is
the lowest-cost change to park.

## What it depends on

`automated-approval-rules` (archived 2026-08-13) deferred its own Prometheus metrics and
monitoring-dashboard DoD items to this change — see that change's
`reports/2026-06-25-deployment.md` closure note. This change's Stage 2 (Backend API Endpoints) is
the natural home for those approval-rules-specific counters/histograms when this resumes.

## Resume trigger

Pick this back up once:
1. GTM integration work has landed and stabilized, or
2. There's a concrete need for auto-approval-rate visibility (e.g. a client asks "how much of
   this was automated").

No code exists yet — resuming means starting Stage 1 from scratch, not continuing partial work.
