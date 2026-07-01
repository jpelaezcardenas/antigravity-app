# Deployment Report — hermes-user-sync-and-onboarding

**Date:** 2026-06-24
**Commit:** `a2d3e09` (pushed to `main`)
**Status:** ✅ Closed for this change's scope — one item (T9.5) explicitly deferred to Hermes-side configuration

## Summary

Formalized loose `PHASE3_*.md` docs into a proper OpenSpec change (`proposal.md`/`tasks.md`),
verified the real state against Supabase (not the docs' claims), closed the two genuine gaps
(RLS policies, dead admin-dashboard code), and redesigned the remaining onboarding-execution
work to be Hermes-native instead of a new FastAPI service layer.

## What shipped

| Item | Status | Evidence |
|---|---|---|
| T1-T6 (identity schema + seed data) | Already done, verified | 3 users, 3 roles, 31 permissions in `kpynymwghfwshvcvevxq` |
| T7 (RBAC middleware) | Already done, verified | `core/rbac.py` wired into `mission_endpoints.py`, `admin_onboarding_endpoints.py` (now deleted) |
| T8 (RLS policies) | ✅ Done this session | Migration `0015_role_based_rls_policies.sql`, 9 policies across 5 tables, applied via Supabase MCP |
| T9 (admin dashboard) | Redesigned + partially done | Dead code deleted; cloud-side RLS gating done; Hermes-side execution spec'd in `HERMES_HANDOFF.md`, not yet configured (T9.5, follow-up) |
| T10 (onboard remaining members) | ✅ Resolved | `growth@contexia.online` never registered (not actionable); `admin@contexia.co` was a stray account, deleted by Juan David's direction |
| T11 (final verification) | Partially done | No regressions; cross-tenant RLS block not manually tested (no second tenant exists yet); identity-model blocker tracked separately in `agent-operations-multitenant-security` §11.7 |

## Database changes (Supabase `kpynymwghfwshvcvevxq`)

- 9 new RLS policies: `user_tenants` (2), `user_roles` (2), `role_permissions` (1),
  `customer_invites` (2), `team_invites` (2)
- 1 row deleted from `usuarios` (`admin@contexia.co`, confirmed stray, no FK references)

## Code changes (antigravity-app)

- Deleted `apps/backend/presentation/admin_onboarding_endpoints.py` — was never registered in
  `main.py`, imported a nonexistent `core.user_management` module
- Added `apps/backend/migrations/0015_role_based_rls_policies.sql` for repo migration history
  (applied out-of-band via Supabase MCP, not through the app's own migration runner)
- No `main.py` changes — no Railway redeploy required for this change

## Deferred (explicit follow-up, not a blocker for closing this change)

**T9.5 — Hermes Swarm role configuration.** Spec'd in `HERMES_HANDOFF.md`: a new
`onboarding-operator` Swarm role + `customer-onboarding` skill that watches
`customer_invites`/`team_invites` and executes tenant/user creation, using Hermes' own
Conductor/Tasks for audit trail. Requires local/WSL access to the running Hermes Workspace
install — out of reach from this session. To be picked up directly in Hermes Workspace.

## Why this counts as closed

The OpenSpec change's actual scope — correct identity data, enforced RLS, no dead/broken code —
is fully resolved and deployed. The one remaining item (live Hermes execution of onboarding) is
a deliberate architectural deferral to a different system/environment, not an unfinished task
within this repo's reach, and is documented with clear acceptance criteria for whoever picks it
up next.
