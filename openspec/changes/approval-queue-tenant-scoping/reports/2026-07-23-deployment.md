# Stage 11 Deployment Report — approval-queue-tenant-scoping

- Date: 2026-07-23
- Change: `approval-queue-tenant-scoping`
- Deploy branch: `main`
- Backend: Railway `elegant-success` (project `27f4a1b4-1e46-4ad7-b08e-15e92817ffdd`),
  service `antigravity-app`, environment `production` — canonical backend
  `antigravity-app-production-175a.up.railway.app` (ARCHITECTURE.md Decision #9)
- Database: Supabase `kpynymwghfwshvcvevxq`

## What shipped

- `core/tenant_context.py::TenantScope` + `resolve_request_tenant_scope(user, client)` —
  shared tenant-scope resolution ladder (own tenant / Cliente-Cero-member = operator / staging
  back-compat / unresolved = None).
- `ApprovalQueueService.enqueue_draft` requires an explicit `tenant_id` keyword (no internal
  Cliente Cero resolution, no silent default). `approve_draft`/`reject_draft` require an
  explicit `tenant_id: Optional[str]` keyword and scope both the existence-check and the
  update query by tenant when provided.
- All 4 `/api/v1/approval-queue/*` endpoints now resolve the caller via
  `Depends(get_current_user)` before any queue read/write; a Cliente-Cero-resolved caller is
  treated as a Contexia operator (sees/acts on every tenant, optional `?tenant_id=` filter on
  GET); an authenticated caller with no resolved tenant gets an empty list / 403 on writes,
  never a silent Cliente Cero fallback.
- Internal callers (`resolution_agent_service`, `social_ops_service`, `sell_machine_service`)
  updated to pass `tenant_id` explicitly at the call site.
- Migration `0033_approval_queue_tenant_not_null.sql` — dropped the bogus zeros-UUID default
  and set `approval_queue.tenant_id NOT NULL`.

## Merge history

Branch `worktree-approval-queue-tenant-scoping` (developed in an isolated worktree to avoid
the shared main checkout, which had multiple active parallel sessions during this change) was
merged with `origin/main` twice before push — once to absorb `hermes-task-queue-tenant-scoping`
(already merged+deployed) and once to absorb `taty-per-tenant-profiles` (still in progress in a
sibling session). Both merges were purely additive (adjacent new functions in
`core/tenant_context.py`; `feature_list.json` entries merged, not overwritten). Full targeted
test suite re-run and green after each merge before pushing.

- `9008215` pushed to `main` at 2026-07-23T11:19Z.

## Production verification (Stage 11 checklist)

| Check | Result |
|---|---|
| `GET /api/v1/approval-queue` with no token | **401** — confirmed via curl against `antigravity-app-production-175a.up.railway.app`, matching `AUTH_ENFORCED=true` live |
| Founder's login resolves to Cliente Cero (riskiest assumption) | **Confirmed via read-only query**: `jpelaezcardenas@gmail.com` has an active, `is_owner=true` `user_tenants` membership in the Cliente Cero tenant (`e2d30d09-6b96-4ebe-a79a-c6aff7a5df34`) — the founder retains full operator access (all-tenants list, unrestricted approve/reject) |
| Approval queue data integrity | `SELECT count(*), count(*) FILTER (WHERE tenant_id IS NULL) FROM approval_queue` → `6, 0` — unchanged from pre-deploy baseline, no NULLs |
| Migration 0033 applied and verified | `column_default: null, is_nullable: 'NO'` on `approval_queue.tenant_id` |
| Railway deploy status | `SUCCESS` (deployment `5cac29b7`) |
| Railway logs | Clean — `"Approval queue router registered successfully"` at startup, no NOT NULL violations, no 500s on approval-queue routes; the one `GET /api/v1/approval-queue` request logged during verification returned 401 as expected |
| Client-scoped list (provisioned non-Cliente-Cero login) | Not independently exercised with a real client session in this pass (no test client credentials were used/created against production) — covered by unit + endpoint tests (Sections 2, 4) and by the identical, already-proven pattern in `GET /api/v1/financials` (`per-tenant-client-access`, archived, verified live 2026-07-22) |
| Internal enqueue path stamps real tenant | Not triggered live in this pass (would require executing a real Taty/Sell-Machine flow); covered by Section 3's unit tests confirming explicit resolution at each call site |

## Outcome

**PASS.** No blocking issues. The two checks not independently re-exercised live (client-scoped
list, internal enqueue) are lower-risk than the founder-login assumption (which was the
change's single highest-risk unknown) and are already covered by this change's own test suite
plus an established, already-verified-live sibling pattern.

## Follow-ups (tracked, not blocking)

- Drop the permissive `approval_queue_anon_all` RLS policy — owned by
  `hermes-multi-tenant-wrapper` (noted in that change's `tasks.md`, 2026-07-23).
- Refactor `financials_endpoints.py` to reuse `resolve_request_tenant_scope` — noted in this
  change's `design.md` "Out of scope" section.
