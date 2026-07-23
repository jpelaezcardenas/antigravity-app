# Design: hermes-task-queue-tenant-scoping

## Context

`apps/backend/services/operator_task_service.py` is the only write/read path for the
`operator_tasks` queue Hermes polls over HTTP (`apps/backend/presentation/sell_machine_endpoints.py`,
mounted at `/api/v1/sell-machine`, gated by `SELL_MACHINE_CANONICAL` — confirmed `true` in Railway
`production-175a`, alongside `AUTH_ENFORCED=true`). The table already has `tenant_id uuid NOT NULL
REFERENCES tenants(id)` with RLS (migration `0024_operator_tasks.sql`) — the gap is entirely in the
service and endpoint layers stamping/exposing/guarding that column, not in the schema.

A concurrently active change, `hermes-multi-tenant-wrapper` (Ground Truth Correction #3, commit
`a07bb93`, already merged to `main`), introduced `core/tenant_context.py::resolve_cliente_cero_tenant_id`
and added a `tenant_id` field to `ApprovalDecision`. This change is additive on top of that work and
does not modify anything `hermes-multi-tenant-wrapper` owns.

## Decisions

### D1 — Optional `tenant_id` param + logged Cliente Cero fallback lives in the SERVICE layer

`create_task(task_type, payload, tenant_id: Optional[str] = None)`. When `tenant_id` is omitted,
the service resolves Cliente Cero via the existing `_resolve_cliente_cero_tenant_id` and emits a
`logger.warning`. Rejected alternative: doing the fallback at the endpoint layer — that would
duplicate the fallback across 5 routes and break the `_resolve_cliente_cero_tenant_id` patch seam
every existing unit test relies on.

### D2 — Explicit column projection makes `tenant_id` contractual, not incidental

`list_pending_tasks()` currently does `select("*")`, so `tenant_id` is present in the Hermes
payload today only as a side effect of selecting everything. Switching to an explicit projection
(`"id, tenant_id, task_type, payload, status, created_at"`) turns "Hermes payload includes
tenant_id" into an enforced contract: a column removed from the table can never silently vanish
from what Hermes sees, and the projection itself is what the spec delta and tests assert against.

### D3 — `list_pending_tasks()` gains an optional `tenant_id` filter

Additive; default (`None`) preserves today's single-global-poller behavior. This is the natural
hook for a future per-tenant Hermes worker, but nothing in this change requires Hermes to use it.

### D4 — `dispatch_campaign_package()` derives tenant from the approval decision

`ApprovalDecision.tenant_id` (added by `hermes-multi-tenant-wrapper`, commit `a07bb93`) is stamped
at enqueue time and is the authoritative source for which tenant a campaign package belongs to.
The dispatch path now reads `decision.tenant_id` directly; it falls back to the Cliente Cero
resolver (with a logged warning) only when the field is empty — i.e. for decisions enqueued before
that field existed.

### D5 — Governance mitigation for the HTTP bridge

The 5 operator-task HTTP routes have never had any auth (`Depends(get_current_user)` is used
elsewhere in the same file for the creative/campaign-listing routes, never here) — a deliberate,
spec'd, accepted risk (archived `hermes-manus-execution-bridge` design.md, risk R1; also codified in
`openspec/specs/bunker-pwa-auth/spec.md:38-40`, "leaving the Hermes↔backend machine-to-machine
bridge endpoints ... unguarded, since Hermes has no browser session"). AGENTES.md:324 separately
documents that direct HTTP calls to agents bypass the `AgentAccessControl` governance enforced only
at the WebSocket chokepoint (`api/websocket_handler.py`, archived `agent-operations-multitenant-security`
Decision D1).

| Option | Cost | Benefit | Verdict |
|---|---|---|---|
| Document-only | ~0 | None operationally — anonymous writes into a service-role table remain anonymous | Insufficient alone |
| Env-gated bearer token + audit parity + tenant validation | ~40 LOC, 1 Railway var, 1 Hermes-side header (founder task) | Closes the anonymous-write hole (once activated), gives the bridge audit parity with the WebSocket path, and validates tenant integrity on every write | **CHOSEN** |
| Token + validation, no audit | Slightly smaller | Closes the write hole but leaves the bridge invisible in `agent_operations`, unlike every other agent path | Rejected — cheap to include, meaningfully improves observability parity |
| Full `AgentAccessControl` reuse | Provisioned machine identity + a `user_tenants` row per tenant, maintained forever | Reuses an existing framework | **Rejected** — `check_access` answers "is this user a member of this tenant"; for Hermes, a global machine operator with no user identity that legitimately serves every tenant, that check is vacuous by construction, and every tenant onboarding would need a new fake-membership row just to keep the check passing |

**Chosen package, three parts:**

1. **`HERMES_BRIDGE_TOKEN`** (new `config.py` setting, `Optional[str] = None`). A dependency on the
   5 operator-task routes reads it at call time (not import time, for testability) and is a no-op
   when unset. When set, requires `Authorization: Bearer <token>` (constant-time compare via
   `hmac.compare_digest`), else 401.
2. **Audit parity.** The 4 mutating endpoints (`POST /tasks`, `POST /campaigns/{id}/dispatch`,
   `POST /tasks/{id}/status`, `POST /tasks/{id}/result`) record a best-effort entry to
   `agent_operations` via the existing `AgentOperationsLogger`, with `agent_name="hermes-bridge"`
   and `user_id="machine:hermes"` — the column is `VARCHAR(255) NOT NULL`, no real auth user is
   required. The poll endpoint (`GET /tasks/pending`) is excluded — recording every poll cycle
   would spam the audit table.
3. **Write-time tenant validation** (D1/D4 above) — a task can no longer be silently stamped with a
   tenant that doesn't exist, and dispatch no longer defaults to Cliente Cero when a real tenant is
   available.

**Honesty about the fail-open window:** with `HERMES_BRIDGE_TOKEN` unset, production is exactly as
exposed after this change as before it. The security benefit activates only once the token is
configured on both sides. This is deliberate — it is what makes the change safely deployable without
coordinating downtime with the local Hermes poller, which today sends no `Authorization` header at
all. This change is **not** archived under the pretense that the bypass is closed; it is mitigated,
pending the founder follow-up in D7.

This decision **supersedes** the "unguarded machine-to-machine bridge" note in
`openspec/specs/bunker-pwa-auth/spec.md:38-40` (amended alongside this change) and extends — without
contradicting — the accepted-risk framing in the archived `hermes-manus-execution-bridge` design.md.

### D6 — `tenant_exists()` helper placement

```python
def tenant_exists(client, tenant_id: str) -> bool:
    """True iff a tenants row with this id exists."""
```

Added to `core/tenant_context.py` alongside `resolve_cliente_cero_tenant_id` — additive only. That
existing function is owned by the concurrently active `hermes-multi-tenant-wrapper` change and is
never modified here.

### D7 — Founder follow-up (out of this change's Stage 11)

Activating `HERMES_BRIDGE_TOKEN` requires coordinated action outside this repo:

1. Generate a token value.
2. Add `Authorization: Bearer <token>` to the Hermes-side poller (separate `hermes-workspace` repo)
   **and** to Hermes's local `.env` — **first**.
3. Only then set `HERMES_BRIDGE_TOKEN` in Railway `production-175a`.

Reversing steps 2 and 3 would 401 the live, currently-unauthenticated Hermes poller until its side
is updated — an avoidable outage. This is recorded here as a TODO for Juan David; it is explicitly
not part of this change's own Stage 11 (which verifies the code deploys correctly and that the
fail-open default behaves as designed).
