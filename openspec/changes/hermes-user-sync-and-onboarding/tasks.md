# Tasks: User Sync & Multi-Tenant Onboarding

Supersedes the loose `PHASE3_*.md` docs in this folder, which are kept for historical
reference only. Status below reflects verified ground truth (DB queries + code reads on
2026-06-24), not the (stale) claims in those docs.

## Already Complete (verified, no action needed)

- [x] T1 `user_tenants` table — migration `0004_user_tenants_table.sql`, live, 3 rows
- [x] T2 `user_roles` table + `role_type` enum — migration `0005_user_roles_table.sql`, live, 3 rows
- [x] T3 `role_permissions` table + enums — migration `0006_role_permissions_table.sql`, live
- [x] T4 Assign 3 initial users to Contexia SAS tenant — migration `0007`, verified via SQL
- [x] T5 Assign initial roles (admin/marketing/viewer) — migration `0008`, verified via SQL
- [x] T6 Seed role_permissions matrix — migration `0009`, 31 rows across 6 roles, verified via SQL
- [x] T7 RBAC middleware (`apps/backend/core/rbac.py`) — exists, wired into
      `mission_endpoints.py` and `admin_onboarding_endpoints.py`. **Correction:** prior docs
      marked this PENDING; it is done.

## Remaining Work

### T8. RLS Policies for Role-Based Filtering
**Status:** ✅ Done (2026-06-24) — migration `0015_role_based_rls_policies.sql`, applied via
Supabase MCP to `kpynymwghfwshvcvevxq`. Extended to also cover `customer_invites`/`team_invites`
(see T9 redesign below) since both needed the same role-based gating.

- [x] 8.1 `user_tenants`: self-read own row + admin reads all rows in own tenant
- [x] 8.2 `user_roles`: self-read own row + admin reads all rows in own tenant
- [x] 8.3 `role_permissions`: read-only for any authenticated user (reference data)
- [x] 8.4 Applied — verified 9 policies live across 5 tables via
      `SELECT tablename, count(*) FROM pg_policies WHERE tablename IN (...)`
- [ ] 8.5 Manual verify as a non-admin authenticated user (deferred — needs a real non-admin
      Supabase Auth session to test against; current admin-only testing can't exercise the
      "blocked" path)

### T9. Hermes-Native Onboarding Execution (REDESIGNED 2026-06-24 — supersedes original plan)
**Original plan superseded.** `apps/backend/presentation/admin_onboarding_endpoints.py` imports
`core.user_management` (`CustomerInviteService`, `TeamInviteService`, `OnboardingWorkflowService`),
which **does not exist** — building it would mean writing ~6h of new Python service code that
duplicates orchestration Hermes already does natively. The original PHASE3B docs themselves said
"Customer clicks invite link → Hermes operator registers them" — the intended executor was always
Hermes, not a FastAPI service layer.

**Decision (confirmed by Juan David, 2026-06-24): go Hermes-native.** Split into two layers:

- **Cloud layer (thin trigger, no new backend code):** RLS policies on `customer_invites` and
  `team_invites` (extends T8's migration) gate `INSERT`/`SELECT` by role — admin-only insert,
  tenant-scoped read. The PWA (or a direct Supabase client call) writes the invite row directly;
  no Python service needed.
- **Local layer (Hermes Workspace, configured outside this repo):** a Swarm role
  (e.g. `onboarding:invite`) with Supabase MCP access watches `customer_invites`/`team_invites`
  for new rows and executes the actual onboarding (create tenant, insert `user_tenants`/
  `user_roles`, send welcome email via Gmail MCP). Conductor missions + Tasks/Trabajos provide
  the audit trail for free — `onboarding_workflows` table becomes optional/redundant, kept only
  if Hermes needs a structured log table to write to (decide at implementation time).

- [x] 9.1 Confirm migrations `0010_customer_invites_table.sql`, `0011_team_invites_table.sql`,
      `0012_onboarding_workflows_table.sql` are applied in `kpynymwghfwshvcvevxq` — verified live.
- [x] 9.2 Deleted `apps/backend/presentation/admin_onboarding_endpoints.py` (dead code, never
      mounted, imports a nonexistent module) — superseded by the Hermes-native design.
- [x] 9.3 Extended the T8 RLS migration (`0015_role_based_rls_policies.sql`) to cover
      `customer_invites` (admin-only insert/select) and `team_invites` (tenant-admin insert,
      tenant-scoped select) — applied and verified.
- [x] 9.4 Hermes handoff spec written:
      `openspec/changes/hermes-user-sync-and-onboarding/HERMES_HANDOFF.md`
- [ ] 9.5 (Out of scope for this change, tracked for follow-up) Actually configure the Swarm role
      and skill inside Hermes Workspace (requires local/WSL access where Hermes runs — not
      reachable from this session), and verify end-to-end: insert a row in `customer_invites`
      → Hermes worker picks it up → tenant + user created + audit visible in Tasks

### T10. Onboard Remaining Tenant Members
**Status:** Resolved — both candidates from `PHASE3_OVERVIEW.md` turned out to be invalid.

- [x] 10.1 Confirm both users exist in `usuarios` (auth):
      `growth@contexia.online` — **does not exist**, never signed up. Cannot onboard until
      the user actually registers; not actionable now.
      `admin@contexia.co` — existed (`id=3c937bea-c669-46fa-931f-3a87c4cc0db3`), but Juan David
      confirmed (2026-06-24) this was a stray/erroneous account ("esta malo, elimina todo lo de
      ese email") — not a real intended tenant member.
- [x] 10.2 Checked for FK references before deletion: 0 rows in `user_tenants`, 0 in `user_roles`
      for that user_id — safe to delete outright.
- [x] 10.3 Deleted the `admin@contexia.co` row from `usuarios` (2026-06-24, via Supabase MCP).
- [x] 10.4 Tenant membership remains at the verified 3 users
      (`jpelaezcardenas@gmail.com`, `contexia.marketing@gmail.com`, `cliente@demo.co`). No
      additional onboarding pending — `PHASE3_OVERVIEW.md`'s 5-user list was inaccurate.

### T11. Final Verification Before Phase 2 Launch
**Status:** Partially blocked — depends on a separate, already-tracked identity issue.

- [ ] 11.1 All 3 users can authenticate and resolve to a UUID-keyed `user_tenants`/`user_roles` row
      — **blocked** by the identity-model fix tracked in
      `agent-operations-multitenant-security/tasks.md` §11.7 (current backend JWTs carry string
      IDs, not UUIDs). Note: this RLS work uses Supabase `auth.uid()` directly, which is
      independent of that backend-JWT issue — Supabase Auth sessions already resolve to UUIDs
      correctly. The §11.7 blocker only affects the separate agent-governance UUID lookup.
- [x] 11.2 RLS policies verified live (9 policies across 5 tables) — cross-tenant block behavior
      not manually tested end-to-end (no second tenant exists yet to test against); deferred,
      same as 8.5.
- [x] 11.3 N/A — admin dashboard was deleted, not deployed (see T9 redesign). No endpoint to verify.
- [x] 11.4 No regressions: the only backend code change was deleting an unmounted, never-imported
      file (`admin_onboarding_endpoints.py`) — nothing else in `main.py` or `rbac.py` changed.

## Stage 11. Deploy to Production (MANDATORY)

- [ ] 11.5 git commit + push to main
- [ ] 11.6 Vercel — N/A, no frontend changes
- [ ] 11.7 Railway — N/A, no `main.py`/router changes (dead file removal only; RLS policies
      were applied directly to Supabase via MCP, not through the app's migration runner — note
      `0015_role_based_rls_policies.sql` exists in `apps/backend/migrations/` for the repo's
      migration history, but was actually applied out-of-band)
- [ ] 11.8 Production verification: confirm RLS policies still active in Supabase (already done,
      9/9 policies confirmed)
- [ ] 11.9 Create report: `openspec/changes/hermes-user-sync-and-onboarding/reports/YYYY-MM-DD-deployment.md`
