# Design — centinela-tenant-scoped-alerts

## 1. Reusable helpers in `core/tenant_context.py`

Keep the existing `resolve_cliente_cero_tenant_id(client)` untouched (still the single source of
truth for "what is the Cliente Cero tenant UUID"). Add:

```python
class TenantResolutionError(ValueError):
    """A tenant-scoped read/write path was invoked without an explicit tenant_id.
    Cliente Cero is never an implicit fallback — it must be resolved explicitly
    by the caller (see ARCHITECTURE.md Decisión #13)."""


def require_tenant_id(tenant_id: Optional[str], *, context: str) -> str:
    """Return tenant_id if truthy; otherwise raise TenantResolutionError naming `context`
    (e.g. 'centinela.save_alerts') so failures are traceable to the call site."""


def resolve_caller_tenant(user: dict, client) -> Optional[str]:
    """3-branch caller-tenant resolution, reusable by Centinela, Approval Queue, and the
    Hermes queue:
      1. user.get("resolved_tenant_id") truthy -> return it.
      2. user.get("id") == STAGING_USER_ID      -> resolve_cliente_cero_tenant_id(client)
         (EXPLICIT Cliente Cero, only for the no-auth local/staging identity).
      3. authenticated, no resolved tenant      -> None. Caller MUST degrade
         (skip the write / return empty), NEVER fall back to Cliente Cero.
    """
```

**Why `ValueError` subclass, not bare `ValueError` or a bespoke base exception:** `save_alerts`
already handles malformed alert dicts where a bare `ValueError` could mean "bad data," not "missing
tenant." A dedicated, greppable class disambiguates and gives sibling changes (Approval Queue,
Hermes queue) a stable contract to catch. Subclassing `ValueError` means any existing broad
`except ValueError` handler upstream keeps working unchanged.

**Why a function, not a class/DI dependency, for `resolve_caller_tenant`:** it mirrors the
already-proven inline logic in `financials_endpoints.py:64-71` almost verbatim — extracting it as a
plain function (not a FastAPI dependency) keeps it callable from non-endpoint contexts too (e.g. a
future scheduler/poller that has a `user`-shaped dict but isn't behind FastAPI's DI).

**`STAGING_USER_ID` constant:** one new line in `core/deps.py`
(`STAGING_USER_ID = _STAGING_USER["id"]`), exported alongside `_STAGING_USER`. `tenant_context.py`
imports it. This does not touch JWT verification, `_verify_supabase_token`, or JWKS handling in any
way — those stay exactly as the 2026-07-22 hotfix left them.

## 2. `CentinelaService.save_alerts` — fail-loud, single source of truth per batch

```python
def save_alerts(self, alerts: List[Dict], tenant_id: str) -> List[str]:
    tenant_id = require_tenant_id(tenant_id, context="centinela.save_alerts")
    if not alerts:
        return []
    try:
        supabase = get_service_supabase()
        saved_ids = []
        for alert in alerts:
            row = {**alert, "tenant_id": tenant_id}   # parameter always wins
            ...
```

Two changes from today's code:
1. The guard runs **before** the try/except, so `TenantResolutionError` propagates to the caller
   instead of being swallowed by the existing `except Exception: return []` (which is preserved
   for genuine DB errors — out of scope to change that behavior).
2. The old `row = alert if "tenant_id" in alert else {**alert, "tenant_id": tenant_id}` (line 411)
   — "caller-supplied per-alert tenant_id wins" — is removed. The parameter is now authoritative
   for the whole batch. **Trade-off:** a caller can no longer smuggle a different tenant_id inside
   an individual alert dict. This is intentional: it closes the exact seam that produced today's
   bug (nobody sets it, so it silently fell through) and prevents a single `save_alerts` call from
   writing a mixed-tenant batch by accident.

## 3. `CentinelaService.get_alerts_for_company` — tenant-scoped reads

```python
def get_alerts_for_company(
    self, company_id: str, tenant_id: str, limit: int = 20, severity: Optional[str] = None
) -> List[Dict]:
    tenant_id = require_tenant_id(tenant_id, context="centinela.get_alerts_for_company")
    ...
    .eq("company_id", company_id)
    .eq("tenant_id", tenant_id)
    ...
```

The demo-profile fallback (`_evaluate_demo_profile`, used when Supabase is unreachable) is
unchanged — it's synthetic, in-memory, and carries no tenant data.

## 4. `centinela_resolution_service` — stamp the tenant_id it already has

`_alert_payload(company_id, tenant_id, discrepancy)` gains the parameter and includes
`"tenant_id": tenant_id` in the returned dict. `poll_shadow_gl_discrepancies(tenant_id)`'s
signature is unchanged (it already receives `tenant_id`) but gets
`require_tenant_id(tenant_id, context="centinela.poll_shadow_gl")` at the top — this function has
no production caller today (tests only), so the guard is pure hardening, not a behavior change for
any live path.

## 5. Endpoint behavior — `presentation/centinela_endpoints.py`

Both endpoints add `user: dict = Depends(get_current_user)` and resolve the tenant **before**
calling into the service, so tenant-resolution failures never get mapped to the endpoint's generic
`except Exception: raise HTTPException(500, ...)` — that block stays reserved for genuine internal
errors.

| Caller state | `POST /evaluate` | `GET /alerts/{company_id}` |
|---|---|---|
| Authenticated, `resolved_tenant_id` present | Evaluate; if `save_alerts=True`, persist stamped with caller's tenant. `save_skipped_reason=None` | 200; rows filtered `company_id` AND caller's tenant |
| Staging identity (`AUTH_ENFORCED=False`, no token) | Evaluate; persist stamped with the **explicitly resolved** Cliente Cero tenant | 200; rows filtered by Cliente Cero tenant (preserves today's local-dev / Contexia-overview behavior) |
| Authenticated, tenant NOT resolved | Evaluate (pure, no side effects); **do NOT save**; `saved_alert_ids=[]`, `save_skipped_reason="tenant_unresolved"` | 200; empty list, `source="none"`. `resolve_cliente_cero_tenant_id` is never invoked on this branch |
| No/invalid token, `AUTH_ENFORCED=True` (production) | 401 from `get_current_user` | 401 |

**Why evaluate-without-save, not a 403, for the authenticated-unresolved case:** `evaluate()` is
pure — it computes a risk preview from `financial_data` the caller supplied in the request body,
with no DB access. Refusing to compute that preview (403) conflates "cannot persist" with "cannot
compute," and would break legitimate use during the transient window between a client's login being
wired and their `user_tenants` row landing. Nothing is written in this branch, so there is no
leak risk to guard against with a hard failure — the response field makes the skip observable
(fixing today's *silent* mis-stamp, which is the actual problem) without over-blocking. This mirrors
`financials_endpoints.py`'s empty-snapshot degradation for the same caller state.

`GET /centinela/health` stays open (no data returned). The `@router.options("/evaluate")` CORS
preflight route is unaffected — OPTIONS requests never reach the auth dependency on the POST route.

New response field: `CentinelaEvaluateResponse.save_skipped_reason: Optional[str]`.

## 6. Internal reader fixes

- **`radar_service.py`** already resolves `tenants.id → tenants.company_id` correctly before
  filtering alerts; it just never added a tenant filter to the alerts query. Fix: add
  `.eq("tenant_id", tenant_id)` (tenant is already in hand at that call site).
- **`pulso_diario_service.py`** has an existing bug: it filters `centinela_alerts` with
  `.eq("company_id", tenant_id)` — passing a tenant UUID into the company_id column, which matches
  nothing today (comment in the file already acknowledges the mismatch). Fix: resolve
  `tenants.id → tenants.company_id` (same pattern radar already uses) and filter by BOTH the
  correct `company_id` AND `tenant_id`. This is a genuine bug fix bundled into this change because
  it's the same tenant-scoping mechanism — Pulso's alert count moves from "always 0" to a real
  number, which is called out explicitly in the deployment report so it isn't mistaken for a
  regression.

## 7. Migration `0034_rescope_centinela_alerts_tenant.sql` — proposed only

Written and verifiable by query in this change; **application is a separate founder decision**,
flagged with a header comment. Rationale for not auto-applying: it mutates ~40 existing production
rows based on a `company_id → tenants.company_id` heuristic, and the founder may prefer to run it
himself via the Supabase SQL editor (established pattern for `auth.*`-adjacent and data-mutating
migrations in this repo).

```sql
-- STATUS: PROPOSED — DO NOT APPLY without founder approval.
-- Re-stamps centinela_alerts rows that were mis-scoped under Cliente Cero (via the
-- silent-default bug fixed by this change) to the tenant that actually owns each
-- company_id. Idempotent: re-running matches no rows once tenant_id already equals
-- the mapped tenant. Rows whose company_id maps to no non-Cliente-Cero tenant stay
-- untouched (they are legitimately Contexia's own alerts).

-- Step 0 (audit — run first, keep the output for the record):
SELECT id, company_id, tenant_id
FROM public.centinela_alerts
WHERE tenant_id = 'e2d30d09-6b96-4ebe-a79a-c6aff7a5df34'  -- Cliente Cero
  AND company_id IN (
    SELECT company_id FROM public.tenants
    WHERE company_id IS NOT NULL AND is_cliente_cero = false
  );

-- Step 0b (ambiguity check — must return 0 rows before Step 1 is safe to run):
SELECT company_id, count(*)
FROM public.tenants
WHERE company_id IS NOT NULL
GROUP BY company_id
HAVING count(*) > 1;

-- Step 1 (the re-stamp):
UPDATE public.centinela_alerts a
SET    tenant_id = t.id
FROM   public.tenants t
WHERE  t.company_id = a.company_id
  AND  t.is_cliente_cero = false
  AND  a.tenant_id IS DISTINCT FROM t.id;

-- Step 2 (verify — expect 0 mismatched rows):
SELECT count(*) AS mismatched
FROM   public.centinela_alerts a
JOIN   public.tenants t ON t.company_id = a.company_id
WHERE  a.tenant_id IS DISTINCT FROM t.id;
```

## 8. Risks and trade-offs

- **Curl/E2E docs break under enforced auth.** `POST /evaluate` and `GET /alerts` start requiring a
  bearer token once `AUTH_ENFORCED=True` (production). The existing E2E docs (`specs/T5-CENTINELA-*`,
  `specs/E2E-TESTING-*`) show tokenless curls — those now 401 in production. This is the intended
  fix: today's tokenless access to any company's alerts IS the leak. Docs get updated with an
  auth-header example (Stage 12); local/staging dev keeps working tokenless via the staging identity
  branch (`AUTH_ENFORCED=False`).
- **Breaking service-layer API.** `save_alerts` and `get_alerts_for_company` change arity
  (`tenant_id` becomes required). The caller set is closed and fully enumerated by this change's
  exploration (the one production endpoint, the resolution poller, and their tests) — no
  un-migrated caller exists in the repo today. Any future caller that forgets the parameter fails
  loudly (`TypeError` at minimum, `TenantResolutionError` if it passes `None`) rather than silently
  mis-stamping.
- **`test_tenant_stamping.py` semantic inversion.** Two existing tests currently assert the bug
  itself: that `save_alerts` falls back to Cliente Cero when no tenant_id is given, and that a
  per-alert `tenant_id` key overrides the resolved one. Both are rewritten (not deleted) to assert
  the opposite — the rewrite is 1:1 traceable to the old test names so the change in behavior is
  auditable in the diff, not silently dropped.
- **Pulso's alert count changes from 0 to real numbers.** Because of the bug fix in §6, any
  dashboard or report reading `pulso_diario_service`'s alert count will show non-zero values for
  the first time. Flagged explicitly in the Stage 10 DB-verification report so it isn't mistaken
  for a new regression during review.
- **Historical alerts stay invisible until the founder applies 0034 (renamed from 0033 — numbering collision fix).** Until then, B2B tenants see
  empty alert history for anything generated before this change shipped — the fail-safe direction
  (nothing leaks) is preserved; it's a visibility gap, not a security gap.
- **Why the parameter always wins in `save_alerts` (§2) is itself a trade-off**, not a free
  improvement: a hypothetical caller that legitimately wanted to write a mixed-tenant batch (none
  exists today) would need to call `save_alerts` once per tenant instead. Accepted because no such
  caller exists and the single-tenant-per-batch invariant is easier to reason about.

## 9. Reuse contract for sibling changes (non-goal here, designed for adoption)

`ApprovalQueueService.enqueue_draft` has the identical implicit-Cliente-Cero stamp, covered today by
`test_tenant_stamping.py`'s `TestEnqueueDraftStampsTenantId` (including a test that asserts it
"stamps None without crashing" — a second silent-failure mode, same root cause). A future
`approval-queue-tenant-scoped-writes` change (and, later, the Hermes queue write path) can adopt
`require_tenant_id(tenant_id, context="approval_queue.enqueue_draft")` and `resolve_caller_tenant`
directly — same contract, same exception type, same 3-branch resolution — without touching
`tenant_context.py` again. That test class is left untouched in this change (comment added marking
it as the next change's target) so the two changes stay independently reviewable.
