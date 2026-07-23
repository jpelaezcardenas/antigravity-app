# Review — task 3 (taty-per-tenant-profiles): Endpoint Auth + Tenant Resolution

**Verdict:** APPROVED

## Scope check

Diff limited to `apps/backend/presentation/taty_endpoints.py` (modified) and
`apps/backend/tests/test_taty_endpoints_tenant_scoping.py` (new), plus
`progress/impl_taty-per-tenant-profiles-task3.md`. Matches tasks.md §3 (3.1-3.3)
exactly. No touches to `core/deps.py`, `financials_endpoints.py`,
`telegram_endpoints.py`, `agents_endpoints.py`, `taty_service.py` — confirmed
via `git status --porcelain`.

## Design contract (D3) compliance

`apps/backend/presentation/taty_endpoints.py:174-187` implements the exact
3-way precedence from design.md D3 / spec.md scenarios:
1. `resolved_tenant_id` truthy -> used directly (line 174-176).
2. Else `user["id"] == _STAGING_USER["id"]` -> `_resolve_cliente_cero_tenant_id()`
   (line 177-178), a local helper (lines 26-36) copying `financials_endpoints.py`'s
   `tenants.is_cliente_cero=True` query verbatim in spirit.
3. Else -> in-band `TatyAskResponse(error_code="tenant_not_resolved", ...)`,
   HTTP 200, static Spanish message, `requires_human_review=True` (lines
   180-187). No tenant data of any kind is read or returned in this branch —
   confirmed non-leaking.

`_STAGING_USER` (core/deps.py:94-99) is only reachable when
`settings.AUTH_ENFORCED=False` and no valid bearer token is present
(core/deps.py:113-146) — there is no path for an authenticated-but-unresolved
caller to land on the Cliente Cero branch; the `elif` on `user["id"] ==
_STAGING_USER["id"]` is the sole and correct gate.

## `company_id` audit (grep, all 4 hits classified)

- `taty_endpoints.py:45` — `TatyAskRequest.company_id` field definition,
  `Optional[str] = None`, docstring states "ignored for resolution." (a)
- `taty_endpoints.py:146` — docstring mention only. (b)
- `taty_endpoints.py:228` — deprecated GET query param, `Optional[str] = None`,
  same "ignored" description. (a)
- `taty_endpoints.py:241` — passed only into `TatyAskRequest(company_id=...)`
  construction in `ask_taty_get`; that constructed request's `company_id` is
  never read inside `ask_taty`'s resolution block. (c)

No validator (`@field_validator`/`@root_validator`) exists on `TatyAskRequest`
that could resurrect implicit trust in `company_id` — grepped, none present.

## GET delegation

`ask_taty_get` (lines 223-247) builds a `TatyAskRequest` from query params and
calls `await ask_taty(request, x_hermes_profile=..., user=user)` directly —
one resolution code path, not a duplicated one. `Depends(get_current_user)` is
present on both handlers (financials-endpoint pattern requires it per-route
since FastAPI dependency injection is per-handler, not inherited by a plain
function call — correct here since GET calls POST's function directly in
Python, still injecting FastAPI-resolved `user`).

## Test quality (non-tautological, verified by reading bodies)

`apps/backend/tests/test_taty_endpoints_tenant_scoping.py`:
- `test_resolved_user_is_scoped_to_own_tenant` — asserts `ask_calls[0]["tenant_id"]
  == "tenant-a-uuid"`, real assertion against fake service call args.
- `test_staging_identity_falls_back_to_cliente_cero` — patches
  `_resolve_cliente_cero_tenant_id` to set a flag AND return a distinguishable
  uuid; asserts both the flag and the tenant_id used downstream.
- `test_authenticated_unresolved_caller_gets_error_and_never_calls_cliente_cero`
  — monkeypatches `_resolve_cliente_cero_tenant_id` to `raise AssertionError`
  if invoked (hard failure, not a soft counter check) — genuinely proves the
  Cliente Cero path is never touched, not just "wasn't called this particular
  way."
- `test_spoofed_company_id_is_ignored` — user resolves to `"tenant-a-uuid"`,
  supplied `company_id="tenant-b-fake-spoofed-id"` is a distinct, clearly
  different-tenant string (not a coincidental match) — asserts the call still
  used `"tenant-a-uuid"`.
- `test_get_handler_shares_resolution_logic` — calls `ask_taty_get` directly,
  asserts the same tenant_id reaches the fake service, proving delegation.

Ran independently:
- `pytest apps/backend/tests/test_taty_endpoints_tenant_scoping.py -v` — 5/5 PASSED
- `pytest apps/backend/tests/test_taty_endpoints_tenant_scoping.py
  apps/backend/tests/test_taty_ask_tenant_scoping.py
  apps/backend/tests/test_taty_tenant_profiles.py -q` — 18/18 PASSED
- `bash init.sh` — green (canon/harness structure OK; RUN_TESTS opt-in skipped
  by design, targeted pytest run above covers this task's surface)

## Adversarial trace — no bypass found

Hand-traced every request shape:
- Missing/malformed auth header, `AUTH_ENFORCED=False` -> `_STAGING_USER` ->
  Cliente Cero (intended, back-compat only).
- Missing/malformed auth header, `AUTH_ENFORCED=True` -> `get_current_user`
  raises 401 before `ask_taty` body runs (core/deps.py:138-143) — endpoint
  never reached.
- Valid token, `resolved_tenant_id` present, `company_id` in body pointing at
  a different tenant -> tenant A's own id used, `company_id` inert (matches
  spoof scenario exactly).
- Valid token, `resolved_tenant_id` absent (real client with no active
  `user_tenants` membership) -> in-band `tenant_not_resolved`, never Cliente
  Cero, no data leak in the static response.

No path found where a caller can read another tenant's profile.

## Checkpoints (DEPLOYMENT_STAGE/CHECKPOINTS.md, scoped to this task)

- Auth genuinely enforced via `Depends`, not decorative: [x]
- Tenant resolution matches canonical pattern (financials_endpoints.py): [x]
- TDD: failing tests first, then green: [x] (documented in impl report, verified independently)
- No fabricated stubs / no disabled type-checking / no hand-edited `app/`: [x] (N/A surface, backend only)
- No scope creep beyond tasks.md §3: [x]
- Docs-sync: no container/dependency change in this task; ARCHITECTURE.md
  decision #13 already documents the per-tenant resolution pattern this task
  extends to Taty — no update required for this specific task's diff. [x]

## Notes / non-blocking

- This is task 3 of 12; remaining sections (4, 5, 6, 7 DB verification, 8
  manual curl, 10 docs, 11 deploy, 12 archive) are correctly left unchecked
  and out of scope for this review, per the implementer's own "Not done in
  this task" section.
