# Hermes Handoff: Onboarding Execution

This is configuration work to be done **inside Hermes Workspace** (local/WSL, where Hermes
actually runs — not reachable from a cloud Claude Code session). It is out of scope for the
`hermes-user-sync-and-onboarding` OpenSpec change itself (see `tasks.md` T9.5), but documented
here so it can be picked up directly, by Juan David or by an agent with local/WSL access.

## What the cloud side already does (done, this change)

- `customer_invites` and `team_invites` tables exist in Supabase project `kpynymwghfwshvcvevxq`.
- RLS policies (migration `0015_role_based_rls_policies.sql`) restrict `INSERT` to admins only —
  Contexia admin for `customer_invites`, tenant admin for `team_invites` — and scope `SELECT`
  accordingly.
- The PWA (or any authenticated Supabase client call) can insert a new invite row directly —
  no backend endpoint needed for the trigger.

## What Hermes needs to do (not yet configured)

### 1. New Swarm role: `onboarding-operator`

Add to the Swarm role table (same place as `orchestrator`, `builder`, `ops-watch`, etc.):

| Field | Value |
|---|---|
| Worker | `onboarding-operator` |
| Wrapper | `onboarding:invite` |
| Tools | `terminal`, `file`, `web`, Supabase MCP (project `kpynymwghfwshvcvevxq`), Gmail MCP (for invite emails) |
| Skills | new skill `customer-onboarding` (see below) |
| MCP | Supabase, Gmail |

### 2. New Hermes skill: `customer-onboarding`

Procedure the worker should follow when it sees a new row in `customer_invites` or `team_invites`:

**For `customer_invites` (new customer/tenant):**
1. Read the pending row (`status = 'pending'`, not expired).
2. Validate `plan` is one of `starter`/`pro`/`enterprise`.
3. Create a new row in `tenants` (legal_name = customer_name, plan = plan).
4. Create the admin user in `usuarios` if not already present (likely needs Supabase Auth
   invite/signup flow, not just a raw insert — confirm against `usuarios` schema before writing).
5. Insert `user_tenants` (is_owner=true, is_active=true) and `user_roles` (role='admin')
   linking the new user to the new tenant.
6. Update `customer_invites.status = 'accepted'`, set `accepted_at`.
7. Send a welcome email via Gmail MCP.
8. Log the whole sequence as a Conductor mission / Task — this is the audit trail, no separate
   `onboarding_workflows` write needed unless a structured query over history is required later.

**For `team_invites` (new team member on existing tenant):**
1. Read the pending row.
2. Validate `role` is allowed for the tenant's `plan` (reuse the plan/role matrix logic —
   currently duplicated in `apps/backend/core/rbac.py::is_role_allowed_for_plan`; consider
   moving this matrix into Hermes Memoria so both sides read the same source of truth).
3. Create/link the user in `usuarios`, insert `user_tenants` (is_owner=false) and `user_roles`.
4. Update `team_invites.status = 'accepted'`.
5. Send welcome email, log via Conductor/Tasks.

### 3. Trigger mechanism

Decide how the `onboarding-operator` worker discovers new invite rows — options:
- Poll `customer_invites`/`team_invites` for `status = 'pending'` on a cron (Hermes has
  `cronjob` tool access already in several roles).
- Subscribe to Supabase Realtime on those tables, if Hermes' Supabase MCP supports it.

### 4. Verification (T9.5 acceptance criteria)

- [ ] Insert a test row into `customer_invites` directly in Supabase.
- [ ] Confirm the `onboarding-operator` worker picks it up within the polling/realtime window.
- [ ] Confirm `tenants`, `usuarios`, `user_tenants`, `user_roles` rows are created correctly.
- [ ] Confirm a Conductor mission / Task entry exists showing the execution, visible in Hermes
      Workspace's Trabajos/Tasks panel.
- [ ] Repeat for `team_invites` against the existing Contexia SAS tenant.

## Why this design (context for whoever picks this up)

The original `PHASE3B_EXECUTION_PLAN.md` already assumed Hermes would execute onboarding
("Customer clicks invite link → Hermes operator registers them"). A FastAPI service layer
(`core/user_management.py`) was scaffolded as endpoint stubs but never actually implemented,
and would have duplicated orchestration/audit Hermes already provides natively (Conductor
missions, Tasks/Trabajos history). Building it would have been ~6h of new Python code solving
a problem Hermes' existing primitives (Swarm roles, Conductor, Tasks) already solve. Decision
confirmed by Juan David on 2026-06-24.
