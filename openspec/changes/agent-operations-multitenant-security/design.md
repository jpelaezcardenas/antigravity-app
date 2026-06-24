# Design — Agent Operations Multi-Tenant Security & Observability

## Context

The original `PHASE5_UPDATED_INTEGRATION_PLAN.md` proposed editing each agent endpoint to add `tenant_id`, cost tracking, and audit logging. Reading the real code changes the design materially:

- Every agent call already funnels through **one function**: `api/websocket_handler.py:invoke_agent()` (synchronous `agent_invoke`) and `agent_output_listener()` (streaming `subscribe`). `AgentContext` already carries `workspace_id`, `user_id`, `user_email`, `permissions`.
- The foundation the plan wanted to "build" mostly **already exists** from the T11–T16 track: `user_tenants`, `user_roles`, `roles`, `cost_tracking` (generic `operation_type` + `DECIMAL(10,6)` + RLS finance-only), and the `mission_audit_log` audit pattern (migration `0013`).
- There are **two parallel agent layers** (`api/agent_endpoints.py` stubs that ignore `tenant_id`; `presentation/*_endpoints.py` real agents). `invoke_agent()` already bridges both.

So the right design is to **govern the chokepoint**, not touch 8 endpoints, and to **reuse** existing tables rather than add redundant schema.

This mirrors the Nominal APM "Governance / Task Management" pillar: agents execute, but every action is access-controlled, recorded with a forensic trail, and costed — without each agent re-implementing governance.

## Key Decisions

### D1 — Instrument the chokepoint, not the endpoints
**Decision:** Wrap `invoke_agent()` and `agent_output_listener()` with: (1) access-control gate, (2) operation recording, (3) cost recording.
**Why over per-endpoint:** one place to enforce/observe; works identically for stub and real agents; no churn across 8 files; impossible to "forget" governance on a new agent.
**Trade-off:** governance is coupled to the WebSocket path. Direct HTTP calls to the agent endpoints bypass it — acceptable because the PWA only reaches agents via WebSocket, and direct endpoints remain DB-RLS protected. Documented as a known boundary.

### D2 — `workspace_id` IS `tenant_id`; enforce membership in app code
**Decision:** Treat `AgentContext.workspace_id` as the tenant id; add `tenant_id` as an explicit alias. Before invoking, verify `user_id ∈ user_tenants WHERE tenant_id = workspace_id`. Reject with a typed error if not.
**Why app-level on top of RLS:** Phase 4 established the backend connects to Supabase with a **broad (anon) key** and RLS policies grant `anon, authenticated, service_role`. That means DB RLS alone does **not** isolate tenants for the service connection. App-level membership enforcement is the real isolation boundary; RLS is defense-in-depth for any future least-privilege connection.
**Trade-off:** one extra query per first invocation per session; mitigated by caching the membership check on `AgentContext` for the connection lifetime.

### D3 — One `agent_operations` table; cost lives on the row (no `cost_tracking`)
**Decision:** Create a single audit-grade `agent_operations` table (agent_name, user_id, tenant_id, operation_type, status ∈ {success, failed, blocked}, duration_ms, cost, input_data JSONB, output_data JSONB, error_message). Cost is stored on `agent_operations.cost`; per-tenant cost reporting is an aggregation over this table.
**Why not the plan's 3 tables (`agent_operations` + `agent_audit_log` + `cost_tracking`):** `agent_operations` already captures input/output/status/error — it *is* the audit log, so a separate `agent_audit_log` duplicates it. And **`cost_tracking` does not exist in this database** — migration `0013` (missions + cost_tracking + mission_audit_log) was authored in the repo but never applied here (verified live 2026-06-24: `tenants`, `user_tenants`, `user_roles`, `role_permissions`, the Shadow GL tables and `approval_queue` exist; `missions`/`cost_tracking`/`roles` do not). Rather than pull in unrelated `0013` schema, keep cost on the operation row.
**Trade-off:** no dedicated financial ledger; cost reporting is by aggregation. Acceptable — a separate ledger can be added later without touching this design. `agent_operations` rows can grow large (JSONB); mitigated by indexes + a future archival job (non-goal now).

### D4 — Deterministic cost matrix in code
**Decision:** `AGENT_OPERATION_COSTS: dict[str, Decimal]` keyed by `"{agent}:{operation}"`, default fallback for unknown ops. `AgentCostTracker.resolve_cost(agent, operation)` returns the `Decimal`; the operations logger writes it to `agent_operations.cost`.
**Why:** costs are policy, not data; keeping them in code keeps them versioned and testable, consistent with the T11.6 cost-matrix precedent.

### D5 — Backward-compatible response shape
**Decision:** Extend the WS `agent_output` payload with `cost` and `session_cost`; keep `status`, `agent`, `data` unchanged.
**Why:** the frontend reads `data`; additive fields don't break it.

### D6 — Governance runs on a dedicated service-role Supabase client
**Decision:** Add a second Supabase client built from `SUPABASE_SERVICE_ROLE_KEY` (`infrastructure/supabase_client.py` → `service_supabase_client` / `core/supabase_client.py` → `get_service_supabase()`). `AgentAccessControl` (read `user_tenants`/`user_roles`) and `AgentOperationsLogger` (insert `agent_operations`) use it; the existing anon client is untouched for everything else.
**Why (verified live 2026-06-24):** the backend connects with the **anon key** and authenticates users with its **own HS256 JWT** (not Supabase Auth), so inside RLS policies `auth.uid()` is **NULL** for the backend. Consequences: (a) `user_tenants`/`user_roles` have RLS enabled with **zero policies** → unreadable by the anon client; (b) anon cannot `INSERT` into `agent_operations` without a permissive policy. A service-role client bypasses RLS for these governance operations **without** widening anon's exposure of identity data (the rejected alternative — granting anon SELECT on `user_tenants` — would let any anon-key holder read all memberships).
**Trade-off:** a new secret (`SUPABASE_SERVICE_ROLE_KEY`) must live in Railway env; the service client must be used **only** for these governance paths, never exposed to request input. The `agent_operations` `auth.uid()`-based SELECT policies remain as defense-in-depth for any future Supabase-authenticated direct reads, but are not the backend's isolation mechanism — app-level tenant scoping is (D2).
**Boundary note:** `workspace_id` is already JWT-signed and server-read (`payload.get("workspace_id")`), so a client cannot target an arbitrary tenant via the WebSocket; the membership check is defense-in-depth + audit + closes the body-param `tenant_id` path in the centinela stub.

### D7 — Resolve JWT identities to canonical UUIDs before the membership check
**Decision:** Introduce `core/identity_resolver.py` (`IdentityResolver`, service-role client) that maps the JWT's identifiers to the canonical UUIDs the governance tables use, applied once when the `AgentContext` is built in the WebSocket connect flow:
- **User:** prefer `usuarios.email → usuarios.id` (email is unique and always present in the JWT); fall back to the JWT `sub` when it is already a UUID and the email lookup fails. Result is `usuarios.id` (UUID).
- **Tenant:** if the JWT `workspace_id` is a UUID, use it; else treat it as `tenants.company_id → tenants.id`; else fall back to the user's single active `user_tenants` membership (block if zero or ambiguous).
**Why this was missing:** D2 assumed `AgentContext.workspace_id` already *was* the tenant UUID and that `sub` already *was* the user UUID. Verified live 2026-06-24 this is false: login (`application/auth_service.py`) issues HS256 JWTs with **string** identities — demo users hardcoded (`usr_cliente_demo`), and `create_access_token` defaults `workspace_id` to the literal string `"contexia-org-1"`. `user_tenants`/`user_roles` key on **UUID** (`usuarios.id`, `tenants.id`), so `is_member()` cast-errored → fail-closed → every user blocked, `agent_operations` stayed empty. The membership data itself was already correct (e.g. `cliente@demo.co` = `usuarios.id 26216a03…` is an active member of tenant `e2d30d09…` / `company_id ctx-001`); only the JWT→DB identity bridge was missing.
**Why resolve server-side (not change the JWT):** keeps the existing token shape and all current consumers (PWA, `tenant_middleware`, `deps`) untouched; resolution is a controlled backend step on the service-role client. Resolving once at context creation makes `check_access`, audit logging, and the RADAR/AUDIT tenant params all use the same canonical UUIDs.
**Fail-closed:** any resolution error or unresolved identity yields a `blocked` result with reason `identity_unresolved`; the WS still connects (resolution failure does not crash the socket), but invocations are blocked and audited.
**Trade-off:** one resolution round-trip per connection (cached on the context for the session). The hardcoded `"contexia-org-1"` default in `create_access_token` is corrected at resolution time via the company_id/membership fallback; replacing that default with a real signed tenant claim is a follow-up that belongs to the auth layer, not this change.

### D8 — `agent_operations.user_id` stores the resolved UUID (column stays VARCHAR)
**Decision:** Persist the **resolved** user UUID (as text) to `agent_operations.user_id`; keep the column `VARCHAR(255)` rather than migrating it to `uuid`.
**Why:** the column is an audit subject, not a strict FK, and may need to record non-UUID system actors in the future; writing the resolved UUID makes per-user audit/cost joins to `usuarios`/`user_tenants` work without a breaking type migration on a live table.
**Trade-off:** joins must cast (`user_id::uuid`) when correlating with UUID-keyed tables; acceptable and documented.

## Data Model (migration 0014)

`agent_operations` follows the established conventions: `tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE`, `cost DECIMAL(10,6)`, `status` with a CHECK in {success, failed, blocked}, `created_at TIMESTAMPTZ`, indexes on `tenant_id`, `(tenant_id, created_at DESC)`, `agent_name`, `status`. `user_id` is `VARCHAR(255)` (the JWT `sub`, an audit subject — not a strict FK).

RLS enabled with two SELECT policies, written against the **real** auth schema (verified live 2026-06-24):
- tenant isolation: `tenant_id IN (SELECT tenant_id FROM user_tenants WHERE user_id = auth.uid() AND is_active)`;
- privileged audit: `EXISTS (SELECT 1 FROM user_roles ur WHERE ur.user_id = auth.uid() AND ur.tenant_id = agent_operations.tenant_id AND ur.role IN ('admin','finance'))` — note `user_roles.role` is an inline `role_type` enum (`admin, finance, marketing, growth, operator, viewer`); **there is no `roles` table**, so the `0013`-style `JOIN roles` was corrected.

Grants follow the established `anon, authenticated, service_role` pattern (same pre-existing broad-key boundary noted in Phase 4, not a new gap).

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| RLS grant pattern blocks the backend (anon key) | Mirror Phase 4 grants (`anon, authenticated, service_role`); isolation enforced in app code (D2) |
| Membership check adds latency to every call | Cache result on `AgentContext` for the session; single indexed query |
| Cost/audit write failure breaks agent response | Record best-effort: log + continue; never fail the user-facing call because audit write failed (audit failures raise a metric, not a 500) |
| Existing WS consumers break on new fields | Additive-only response (D5); regression test on Phase 4 behavior |
| Production migration on live Supabase | Stage 11 gated; idempotent `CREATE TABLE IF NOT EXISTS`; rollback = `DROP TABLE agent_operations` (new table, no data dependency) |
| Dev venv missing deps (jose/passlib/email-validator, per Phase 4 notes) | Use the isolated TestClient/router-only test pattern Phase 4 used; install missing test deps if needed |

## Open Questions

- Should `blocked` (access-denied) operations be persisted to `agent_operations` too? **Resolved: yes** — a blocked attempt is exactly what an audit trail must capture. Cost = 0 for blocked.
- Per-tenant cost budgets / throttling? Out of scope; `cost_tracking` makes it possible later.
