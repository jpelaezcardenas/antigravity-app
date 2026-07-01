# Proposal: User Sync & Multi-Tenant Onboarding

## Why

Phase 2 (agent integration) launch on the multi-tenant model requires every active Contexia
user to be correctly assigned to the Contexia SAS tenant with a role, and requires role-based
authorization to actually be enforced — not just modeled in the database.

This work was started informally (no `proposal.md`/`design.md`/`tasks.md`) under a set of loose
`PHASE3_*.md` docs in this change folder, which violates the project's OpenSpec discipline
(CLAUDE.md §7 — "documentation is the source of truth"). Those docs also drifted from reality:
they mark RBAC middleware and the admin dashboard as "PENDING" when the code already exists,
while understating a real gap (RLS policies, and two users never actually assigned to the tenant).
This proposal formalizes the change with the verified ground truth before any further execution.

## Ground Truth (verified 2026-06-24, via direct Supabase SQL + code read)

- **Identity/role tables live in the `contexia-content-os` Supabase project**
  (`kpynymwghfwshvcvevxq`), not the project named "Contexia" (`wzqymuzpjbagnbgsiqig`).
- `user_tenants`: 3 rows. `jpelaezcardenas@gmail.com` is_owner=true, is_active=true.
  `contexia.marketing@gmail.com` and `cliente@demo.co` is_owner=false, is_active=true.
- `user_roles`: 3 rows — admin / marketing / viewer respectively, matching the assignment above.
- `role_permissions`: 31 rows covering all 6 roles (admin, finance, marketing, growth, operator, viewer).
- **RLS policies on `user_tenants`, `user_roles`, `role_permissions`: 0.** Tenant/role isolation
  is enforced only at the application layer (via `rbac.py`), not at the database layer.
- `apps/backend/core/rbac.py` exists and is wired into real endpoints
  (`mission_endpoints.py`, `admin_onboarding_endpoints.py`) — the RBAC middleware is done,
  contradicting `PHASE3_TASKS.md`'s "PENDING" status for T7.
- `apps/backend/presentation/admin_onboarding_endpoints.py` exists with 5 working endpoints
  (customer invite, list customers, team invite, list/update/remove team members, audit trail)
  but **is not registered in `main.py`** — it is dead code, never mounted on the running API.
- `growth@contexia.online` and `admin@contexia.co` are named in `PHASE3_OVERVIEW.md` as tenant
  members but are **absent from `user_tenants`/`user_roles`**. Resolved during execution
  (2026-06-24): `growth@contexia.online` never registered (not actionable yet);
  `admin@contexia.co` was a stray account, confirmed invalid by Juan David, and deleted.

## What Changes

- Formalize this change under standard OpenSpec structure (this file + `tasks.md`).
- Close the real remaining gaps: RLS policies for role-based filtering (T8), mounting the admin
  dashboard router (part of T9), onboarding the two missing users, and final verification (T10/T11).
- Retire the loose `PHASE3_*.md` docs as historical reference once `tasks.md` supersedes them
  (not deleted — kept for traceability, but no longer the source of truth).

## Impact

- Affected code: `apps/backend/main.py` (router registration), `apps/backend/migrations/`
  (new RLS policy migration), Supabase `kpynymwghfwshvcvevxq` project.
- Affected users: `jpelaezcardenas@gmail.com`, `contexia.marketing@gmail.com`, `cliente@demo.co`
  (already onboarded — full tenant membership, no further onboarding pending).
- No breaking changes — additive (RLS policies, router mount, two new tenant memberships).
