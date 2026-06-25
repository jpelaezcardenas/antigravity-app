## Why

Phase 5 (`agent-integration-phase5`, archived 2026-06-23) wired the 8 Hermes agents to the PWA over WebSocket and got real data flowing end-to-end. But it left the agent invocation layer **without the multi-tenant security and observability** that the later Phase 3B / T11–T16 track built for missions (`user_tenants`, `user_roles`, RLS, `cost_tracking`, `mission_audit_log`).

Today, `api/websocket_handler.py:invoke_agent()` trusts the `workspace_id` embedded in the JWT blindly: it never checks the caller actually belongs to that tenant (`user_tenants`), never persists what each agent did, and never records the cost of an operation. For a system whose go-to-market is **Cliente Cero → external tenants**, agent calls are the most exposed cross-tenant surface and currently the least governed. This is the explicit follow-up flagged in `agentic-performance-management-phase4/tasks.md` ("tenant scoping is not yet enforced — no tenant context flows through HTTP yet").

This change closes that gap by governing the single chokepoint every agent call already passes through.

## What Changes

- Enforce **tenant membership** before any agent runs: `invoke_agent()` rejects callers whose `user_id` is not in `user_tenants` for the requested `tenant_id` (defense-in-depth on top of DB RLS, since the backend connects with a broad key).
- Persist every agent invocation to a new **`agent_operations`** audit table (agent, user, tenant, operation_type, status, duration, cost, input/output, error) with RLS, mirroring the `0013` missions pattern.
- Record the **cost** of each agent operation (from a deterministic cost matrix) directly on the `agent_operations.cost` column. (The `cost_tracking` table from migration `0013` is **not present** in this database — `0013` was authored but never applied here — so cost is captured on `agent_operations` and aggregated per tenant from there.)
- Return cost in the WebSocket response (`{status, agent, data, cost, session_cost}`) without breaking existing consumers.
- Add multi-tenant isolation + cost E2E tests (no cross-tenant leakage).

## Capabilities

### New Capabilities
- `agent-operations-governance`: tenant-membership access control, per-operation audit log (`agent_operations` + RLS), and cost recording (reusing `cost_tracking`) applied at the WebSocket `invoke_agent()`/`agent_output_listener()` chokepoint.

## Non-Goals

- **Not** merging the two parallel agent layers (`api/agent_endpoints.py` stubs vs `presentation/*_endpoints.py` real agents). That divergence is real tech debt but out of scope; this change only instruments the shared chokepoint.
- **Not** building the Shadow GL or new agent business logic (that is `agentic-performance-management-phase4`).
- **Not** schema-based sharding or log archival/rotation (future, once volume justifies it).
- **Not** a frontend cost dashboard — cost is exposed in the WS payload only.

## Impact

- New table: `agent_operations` (+ RLS, indexes). Reuses existing `tenants`, `user_tenants` (with `is_active`), `user_roles` (inline `role` enum; no `roles` table exists).
- New code: `core/agent_access_control.py`, `services/agent_cost_tracker.py` (cost matrix + `resolve_cost`), `services/agent_operations_logger.py`, migration `0014_agent_operations_with_rls.sql`.
- Modified: `api/websocket_handler.py` (chokepoint instrumentation), `services/agent_context.py` (explicit `tenant_id` alias).
- Risk surface: RLS / auth / multi-tenant data — high. Stage 11 deploy gated, rollback plan required.
