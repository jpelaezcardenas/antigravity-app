# Centinela Fiscal — Tenant-Scoped Alert Writes and Reads

## Why

`CentinelaService.save_alerts()` (`apps/backend/services/centinela_service.py:407`) stamps
`tenant_id = resolve_cliente_cero_tenant_id()` on every alert dict lacking a `tenant_id` — and no
current caller ever supplies one. An alert generated from a B2B client's own financial data (e.g.
Medic, which has its own tenant since `per-tenant-client-access`) is silently archived under
Contexia's own Cliente Cero tenant. This is a cross-tenant data leak with no visible error: the
insert succeeds, logs look normal, and the client's alert simply disappears into Contexia's own
ledger of alerts.

The read side has the mirror problem: `GET /api/v1/centinela/alerts/{company_id}` has no auth and
filters only by `company_id`, so any caller can read any company's alerts. Two internal readers
compound this — `pulso_diario_service.py` passes a tenant UUID into a `company_id` filter (always
matches nothing) and `radar_service.py` never filters by tenant at all.

Contexia already has a proven, production-verified pattern for exactly this problem
(`GET /api/v1/financials` — see ARCHITECTURE.md Decisión #13): resolve the caller's tenant from the
authenticated session; fall back to Cliente Cero only for the explicit no-auth staging identity;
degrade to empty (never Cliente Cero) for an authenticated caller whose tenant hasn't resolved.
Centinela needs the same contract, and the resulting helper needs to be reusable by the Approval
Queue and Hermes queue write paths, which share the identical implicit-Cliente-Cero bug.

## What Changes

- **Fail-loud tenant guard**: new `TenantResolutionError` + `require_tenant_id()` in
  `core/tenant_context.py`. `CentinelaService.save_alerts()` and `get_alerts_for_company()` take a
  REQUIRED `tenant_id` parameter; missing/empty raises instead of silently defaulting to Cliente
  Cero.
- **Caller-tenant resolution**: new `resolve_caller_tenant(user, client)` implementing the proven
  3-branch pattern (resolved tenant → use it; staging no-auth identity → explicit Cliente Cero;
  authenticated-unresolved → `None`, caller degrades). Both `POST /api/v1/centinela/evaluate` and
  `GET /api/v1/centinela/alerts/{company_id}` gain `Depends(get_current_user)` and use it.
- **Evaluate-without-save degradation**: an authenticated caller with no resolved tenant still gets
  the rule evaluation (pure, no side effects) but the response reports
  `save_skipped_reason="tenant_unresolved"` and nothing is persisted — never Cliente Cero.
- **Tenant-scoped reads**: `GET /alerts/{company_id}` filters by `company_id` AND the caller's
  tenant; unresolved tenant returns an empty list, not Contexia's own alerts.
- **Internal reader fixes**: `radar_service.py` adds the tenant filter (tenant already in hand);
  `pulso_diario_service.py`'s tenant-as-company_id bug is corrected alongside the tenant filter.
- **Resolution poller**: `centinela_resolution_service._alert_payload` stamps the `tenant_id` it
  already receives as a parameter (currently dropped before the insert).
- **Proposed-only backfill**: migration `0034_rescope_centinela_alerts_tenant.sql` re-stamps the
  ~40 existing mis-scoped rows via `company_id → tenants.company_id` mapping. Written and verified
  by query, but marked "DO NOT APPLY without founder approval" — applying it is a separate,
  explicit decision.

## Impact

- **Specs:** `openspec/specs/centinela-alerts/spec.md` gains 4 new requirements (tenant-scoped
  writes, evaluate-endpoint resolution, tenant-scoped reads, internal-reader scoping).
- **Code:** `core/tenant_context.py`, `services/centinela_service.py`,
  `services/centinela_resolution_service.py`, `presentation/centinela_endpoints.py`,
  `services/pulso_diario_service.py`, `services/radar_service.py`, plus their test files.
- **Data:** one proposed (not applied) migration touching ~40 existing `centinela_alerts` rows in
  production Supabase.
- **Non-goals:** `ApprovalQueueService.enqueue_draft` and the Hermes queue write path have the
  identical implicit-Cliente-Cero bug (see `test_tenant_stamping.py`'s
  `TestEnqueueDraftStampsTenantId`) but are explicitly **out of scope** here — this change designs
  `require_tenant_id`/`resolve_caller_tenant` as a reusable contract for those sibling changes to
  adopt later. Also out of scope: cleaning up the currently-ineffective RLS allow-all policies on
  `centinela_alerts`; the wizard's `auditoria-sombra` flow (calls `evaluate()` but never persists,
  so it's unaffected); applying the 0034 backfill (renamed from 0033 — numbering collision fix) (founder decision, separate from this change).
