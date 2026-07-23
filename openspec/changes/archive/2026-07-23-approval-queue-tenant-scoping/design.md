# Design — Approval Queue Tenant Scoping

## Pre-work verification (2026-07-23)

Live query against Supabase project `kpynymwghfwshvcvevxq`:

```sql
SELECT aq.tenant_id, t.is_cliente_cero, t.legal_name, count(*)
FROM public.approval_queue aq
LEFT JOIN public.tenants t ON t.id = aq.tenant_id
GROUP BY aq.tenant_id, t.is_cliente_cero, t.legal_name;
```

Result: a single group — `tenant_id = e2d30d09-6b96-4ebe-a79a-c6aff7a5df34` (Contexia SAS,
`is_cliente_cero=true`), `count = 6`. **No NULL or zeros-UUID rows remain.** Confirms
`hermes-multi-tenant-wrapper`'s Ground Truth Correction #2 backfill is complete — migration
`0033` in this change only needs to guard against regression (drop default + NOT NULL), not
re-backfill.

## Tenant scope resolution (shared helper)

Extends `core/tenant_context.py` (created by `hermes-multi-tenant-wrapper`, do not duplicate):

```python
@dataclass(frozen=True)
class TenantScope:
    tenant_id: str
    all_tenants: bool = False

def resolve_request_tenant_scope(user: dict, client) -> Optional[TenantScope]:
    ...
```

Resolution ladder (mirrors `financials_endpoints.py`'s three-way policy, plus a 4th outcome
for the admin/operator case that approval queue — unlike financials — needs):

1. `cliente_cero_id = resolve_cliente_cero_tenant_id(client)`.
2. `user["resolved_tenant_id"] == cliente_cero_id` (both truthy) →
   `TenantScope(cliente_cero_id, all_tenants=True)` — **operator**: a caller whose own
   membership resolves to Contexia's tenant is treated as a Contexia admin.
3. `user["resolved_tenant_id"]` truthy (and not Cliente Cero) →
   `TenantScope(resolved_tenant_id, all_tenants=False)` — normal B2B client, sees only its
   own queue.
4. `user["id"] == _STAGING_USER["id"]` (only reachable when `AUTH_ENFORCED=False` and no
   token was supplied) → `TenantScope(cliente_cero_id, all_tenants=True)` — preserves
   today's local-dev/demo behavior exactly.
5. Else (authenticated, no resolved tenant) → `None` — **never** Cliente Cero. Endpoints
   treat `None` as "no queue access": empty list on GET, 403 on writes.

### Admin detection: why the simple rule, not `user_roles`

`user_roles` (migration `0015`) has a `role='admin'` value and could gate operator access
more strictly. We use the simpler "resolves to Cliente Cero" rule instead, because:

- A caller whose `user_tenants` membership resolves to Cliente Cero **already** sees
  Contexia's own financials via `GET /api/v1/financials` (same resolution chain, same
  membership table). This change introduces no new hole — the membership itself is the
  trust boundary, provisioned manually via migrations `0007`/`0029`/`0032`.
- Adding a second, independent role check here would create two sources of truth for "is
  this caller a Contexia operator" that could drift.

Deferred hardening (documented, not built): require `user_roles.role='admin'` **in addition
to** Cliente Cero membership before granting `all_tenants=True`, if/when non-owner accounts
are ever added to Cliente Cero's tenant.

## Service-layer contract

`enqueue_draft` no longer resolves a tenant itself — it requires one:

```python
async def enqueue_draft(draft_id, draft_type, journal_entry, memo="", *, tenant_id: str)
```

A falsy `tenant_id` returns `(False, None, "tenant_id is required")` before any DB call —
this makes a caller that forgets to pass a tenant fail loudly (test-visible), instead of
silently falling back to Cliente Cero as it does today.

`approve_draft` / `reject_draft` take a **required, Optional-typed** keyword:

```python
async def approve_draft(decision_id, approval_reason, approved_by, *, tenant_id: Optional[str])
```

Required-but-Optional forces every call site to make an explicit choice: pass a real UUID to
scope, or pass `None` deliberately for the admin/unrestricted path. When `tenant_id` is not
`None`, both the existence-check `SELECT` and the `UPDATE` add `.eq("tenant_id", tenant_id)`.
A cross-tenant `decision_id` returns the same `"Decision {id} not found"` error as a
genuinely missing id — the service never reveals that a row exists under a different tenant.

`list_drafts(status=None, draft_type=None, tenant_id=None)` is unchanged — filtering is
optional by design, since `all_tenants=True` callers and internal Contexia-side services
(`sell_machine_service`, `operator_task_service`) legitimately want an unfiltered read.

## Endpoint wiring

All 4 routes in `presentation/approval_queue_endpoints.py` add
`user: dict = Depends(get_current_user)`, then
`scope = resolve_request_tenant_scope(user, get_service_supabase())`:

| Endpoint | `scope is None` | `scope.all_tenants` | normal client |
|---|---|---|---|
| `GET ""` | empty list (200) | optional `?tenant_id=` filter, else unfiltered | forced `tenant_id=scope.tenant_id`; ignores any client-supplied `?tenant_id` |
| `POST /enqueue` | 403 | `tenant_id=scope.tenant_id` (= Cliente Cero) | `tenant_id=scope.tenant_id` |
| `POST /approve` | 403 | `tenant_id=None` (unrestricted) | `tenant_id=scope.tenant_id` |
| `POST /reject` | 403 | `tenant_id=None` | `tenant_id=scope.tenant_id` |

The dead `request.state.tenant_id` read (`approval_queue_endpoints.py:112`) is deleted.
`DraftListItem` gains `tenant_id: Optional[str] = None`, always populated from the row — a
client seeing its own tenant id back is harmless, and the admin view needs it to distinguish
rows.

## Internal callers — explicit, never a silent default

- `resolution_agent_service.py` (`enqueue_draft` at two call sites) — the enclosing functions
  already receive `tenant_id`; just thread it through to the call.
- `social_ops_service.py` / `sell_machine_service.py` — these are Contexia-internal agent
  flows with no per-request tenant in scope. Each now calls
  `resolve_cliente_cero_tenant_id(get_supabase())` **at the call site**, immediately before
  `enqueue_draft`, and logs + skips the enqueue if it returns `None`. This satisfies "Cliente
  Cero nunca como default mudo": the resolution is visible in the diff and in logs, not
  buried inside the service.
- `operator_task_service.py`'s `list_drafts` call is unchanged (unfiltered internal read).

## Migration `0033_approval_queue_tenant_not_null.sql`

Idempotent, three statements: (1) safety re-backfill of any `NULL`/zeros-UUID row to the real
Cliente Cero id — a no-op today per the verification query above, but keeps the migration
correct if it's ever re-run against a database that regressed; (2) `ALTER COLUMN tenant_id
DROP DEFAULT` — removes the bogus zeros-UUID default so a future write that forgets
`tenant_id` fails loudly (`NOT NULL` violation) instead of writing a ghost tenant; (3)
`ALTER COLUMN tenant_id SET NOT NULL`.

**Application to the live database is gated on explicit founder confirmation** before this
change reaches Stage 11 — it is a schema change to a production table, distinct from the
read-only verification already performed.

## Out of scope (explicitly)

- Dropping the permissive `approval_queue_anon_all` RLS policy — owned by
  `hermes-multi-tenant-wrapper` (still open there); this change's defense is
  application-layer (explicit tenant_id + endpoint auth), same posture financials already
  has today.
- Refactoring `financials_endpoints.py` to reuse `resolve_request_tenant_scope` — its tests
  monkeypatch module-level names (`_resolve_cliente_cero_tenant_id`,
  `compute_pulso_daily_snapshot`) and a refactor would need to update those in lockstep; noted
  as a follow-up, not bundled here.
- An admin-supplied `tenant_id` override on `POST /enqueue` (stamp a draft under a tenant
  other than the caller's) — no current caller needs it; add only if a real use case appears.
