# Tasks — Agent Operations Multi-Tenant Security & Observability

**Change:** `agent-operations-multitenant-security`
**Date:** 2026-06-24
**Status:** 🔄 IN PROGRESS
**Convention:** TDD (failing test first → GREEN), baby steps (≤2h each), fully typed, English only.

---

## 0. Setup: Create Feature Branch (MANDATORY — FIRST STEP)

- [x] 0.1 Create feature branch `feature/agent-operations-multitenant-security` from `main`
- [x] 0.2 Verify branch creation and current branch status

---

## 1. Slice 1 — `agent_operations` table + RLS (migration 0014) ✅

- [x] 1.1 Write failing schema test (`tests/test_agent_operations_schema.py`, gated `RUN_AGENT_OPS=1`) asserting `agent_operations` queryable + expected columns + insert structure + CHECK on status — RED before migration (table absent)
- [x] 1.2 Create migration `apps/backend/migrations/0014_agent_operations_with_rls.sql`: table + 5 indexes (`tenant_id`, `(tenant_id, created_at DESC)`, `agent_name`, `status`, `created_at`) + `status` CHECK in {success, failed, blocked}
- [x] 1.3 Add RLS: tenant-isolation SELECT via `user_tenants` (`is_active`), admin/finance audit SELECT via `user_roles.role` enum (corrected — no `roles` table exists); grants `anon, authenticated, service_role`
- [x] 1.4 Applied to production Supabase via MCP migration `agent_operations_with_rls` → GREEN. Verified live: 12 columns present, `relrowsecurity=true`, 2 policies (`agent_operations_tenant_isolation`, `agent_operations_audit_privileged`), CHECK rejects invalid status, insert round-trip against Cliente Cero OK; test rows cleaned up (table back to 0 rows). NOTE: only one Supabase project exists (no branches) — same direct-to-prod dev pattern Phase 4 used; rollback = `DROP TABLE agent_operations` (new, empty, no consumers yet).

## 2. Slice 2 — Access control (tenant membership) — service-role client (decision D6) ✅

- [x] 2.0 Added `SUPABASE_SERVICE_ROLE_KEY` setting (`config.py`) + service-role client (`infrastructure/supabase_client.py` `service_supabase_client` via parametrized `LazySupabaseClient`, `core/supabase_client.py` `get_service_supabase()`); `tests/test_supabase_clients.py` GREEN (3/3 — distinct singletons, distinct key attrs). **Prereq:** `SUPABASE_SERVICE_ROLE_KEY` must be set in Railway env before Stage 11 (user-provided secret).
- [x] 2.1 `tests/test_agent_access_control.py`: pure-logic unit tests with an injected fake client (member→allowed, non-member→blocked, missing user/tenant→blocked, DB error→fail-closed, privileged-role audit) + gated live tests using real Cliente Cero data
- [x] 2.2 Implemented `apps/backend/core/agent_access_control.py` (`AccessDecision`, `AgentAccessControl.check_access/is_member/get_role/can_read_full_audit`) reading `user_tenants` (`is_active`) + `user_roles.role` via the service-role client; fail-closed on error — logic tests GREEN (6/6, 2 live skipped)
- [x] 2.3 Added `tenant_id` property alias + `tenant_membership_verified` per-session cache field on `AgentContext`; `tests/test_agent_context_governance.py` GREEN (3/3). Full Slice 2 run: 12 passed, 2 skipped (live).

## 3. Slice 3 — Cost matrix (cost on `agent_operations.cost`) ✅

- [x] 3.1 Wrote test suite `tests/test_agent_cost_tracker.py` asserting AGENT_OPERATION_COSTS (known ops), resolve_cost logic (matrix + default), blocked→zero, and Decimal types
- [x] 3.2 Implemented `apps/backend/services/agent_cost_tracker.py`: AGENT_OPERATION_COSTS matrix (deterministic Decimal per agent:operation, ~15 ops), `resolve_cost(agent, operation)` + `resolve_cost_for_status` (blocked→0), DEFAULT_COST=0.01 — pure logic, no DB
- [x] 3.3 Full test suite GREEN (7/7). Cost is resolved by the tracker, persisted by operations logger (Slice 4)

## 4. Slice 4 — Operations logger + chokepoint instrumentation ✅ COMPLETE

- [x] 4.1 Implemented `apps/backend/services/agent_operations_logger.py` (AgentOperationsLogger class, async record() method, best-effort error swallowing, uses service-role client for persistence)
- [x] 4.2 Wrote logical tests for the governed chokepoint `tests/test_websocket_invoke_governance.py` — access gate (blocked/allowed), cost tracking, response shape (cost/session_cost), audit-write failure isolation — logic tests GREEN (4/4)
- [x] 4.3 Wired into actual `api/websocket_handler.py:invoke_agent()`: access gate → execute → log+cost → return (backward-compatible response: {status, agent, data, cost, session_cost}); imports agent_access_control, AgentCostTracker, agent_operations_logger; access denied → early return + async log; success → calculate cost + accumulate session_cost + log asynchronously in finally block (best-effort, never blocks response)
- [x] 4.4 Wired into `agent_output_listener()` (subscribe path, Slice 4.4): same gate + timing + logging as invoke_agent; tracks lines streamed (line_count); operation_type="stream" (distinct from invoke); logs success/failed/cancelled status + total duration; cost resolved for operation_type="stream"
- [x] 4.5 Regression: Phase 4 WebSocket behavior unchanged (subscribe/heartbeat/permission/`data` shape) — `tests/test_websocket_phase4_regression.py` GREEN (7/7), zero regressions; response now includes additive cost/session_cost fields (backward-compatible)

## 5. Slice 5 — Multi-tenant isolation E2E

- [ ] 5.1 E2E test: user of tenant A cannot read/produce tenant B `agent_operations`; cost rows isolated by tenant — `tests/test_agent_multi_tenant_isolation.py`
- [ ] 5.2 E2E test: cost aggregation per tenant sums individual operations correctly — `tests/test_agent_cost_tracking_e2e.py`
- [ ] 5.3 E2E test: non-privileged role denied full-audit read

## 6. Review and Update Existing Unit Tests (MANDATORY)

- [ ] 6.1 Review existing agent/WebSocket tests for impact from the new governance path
- [ ] 6.2 Update any affected tests to the new (additive) response shape

## 7. Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 7.1 Capture pre-test DB baseline (counts: `agent_operations`, `cost_tracking`)
- [ ] 7.2 Run targeted tests for changed modules (Slices 1–5)
- [ ] 7.3 Run required broader backend suite per `openspec/config.yaml`
- [ ] 7.4 Verify post-test DB state; restore if mutated
- [ ] 7.5 Create report `specs/reports/2026-06-24-step7-unit-test-and-db-verification.md`
- [ ] 7.6 Mark complete only after tests pass and report exists

## 8. Manual Endpoint Testing with curl (MANDATORY — AGENT MUST EXECUTE)

- [ ] 8.1 Ensure backend server is running locally
- [ ] 8.2 Drive an agent invocation through the governed path (WS or the underlying agent endpoint with context headers); verify success records an `agent_operations` row + `cost_tracking` row
- [ ] 8.3 Drive a cross-tenant attempt; verify `blocked` row + denial response
- [ ] 8.4 Test error cases (unknown agent, missing tenant); verify structured errors
- [ ] 8.5 Restore DB state (delete test rows); document commands + responses in a report

## 9. Frontend: E2E Testing with Playwright/Preview MCP (MANDATORY if applicable — AGENT MUST EXECUTE)

- [ ] 9.1 If the cost field is surfaced in UI: open the PWA, connect WebSocket, verify `data` renders and no console errors with the new payload
- [ ] 9.2 Document outcome; restore environment. (If no UI change ships, mark N/A with justification.)

## 10. Update Technical Documentation (MANDATORY)

- [ ] 10.1 Update backend docs / `AGENTES.md` references with the governance layer (access control, audit, cost)
- [ ] 10.2 Note the chokepoint boundary (direct HTTP agent calls bypass WS governance) as a known limitation

## 11. Stage 11 — Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`
Project-specific details:
- Deploy branch: `main`
- Frontend URL: https://contexia.online/app/overview
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [ ] 11.0 Confirm `SUPABASE_SERVICE_ROLE_KEY` is set in Railway env (user-provided secret; governance reads/writes depend on it)
- [ ] 11.1 git commit + push (merge feature branch → `main`)
- [ ] 11.2 Vercel build complete (green ✅) — only if frontend changed
- [ ] 11.3 Railway deploy active; confirm deploy branch matches `main` (watch the recurring branch-mismatch issue)
- [x] 11.4 Migration `0014` already applied to the (single) production Supabase via MCP `agent_operations_with_rls`; `list_tables`/SQL confirm `agent_operations` live with RLS + CHECK
- [ ] 11.5 Production verification: governed invocation records op+cost; cross-tenant attempt blocked
- [ ] 11.6 Create report `openspec/changes/agent-operations-multitenant-security/reports/2026-06-24-deployment.md` (changes, evidence, rollback = `DROP TABLE agent_operations`)

---

## Verification Checklist (before finalizing tasks.md)

- [x] Step 0 (feature branch) is FIRST
- [x] Mandatory steps included (review tests, run tests+DB, curl, E2E, docs)
- [x] Stage 11 included with project-specific details
- [x] Manual testing marked "AGENT MUST EXECUTE"
- [x] DB state restoration steps present
- [x] Step 7 report path + naming convention specified
