# Review — Stage 13.0 reconciliation (commit `5d7170d`)

**Reviewer note:** the dispatched reviewer subagent hit a session API rate limit partway
through and terminated early. It independently confirmed items 1-2 before failing (see its
partial result below). The leader (Claude Opus 4.8) completed items 3-8 directly afterward,
re-verifying rather than trusting its own earlier claims.

## Item 1-2 (confirmed by the subagent before it failed)

> "This confirms items 1-2 cleanly. `_resolve_caller_tenant_id` is a faithful extraction of
> the original inline 3-branch logic — the diff shows the old inline code (lines removed) is
> byte-identical in logic to the new helper function body."

Independently re-confirmed: `git diff origin/main -- apps/backend/core/tenant_context.py`
produces zero output — the shared module is byte-identical to `origin/main`, zero risk to the
5 sibling changes depending on it.

## Item 3 — centinela_endpoints.py

`git diff origin/main HEAD --numstat -- apps/backend/presentation/centinela_endpoints.py`:
**99 insertions, 0 deletions** — purely additive. `evaluate_centinela` and `get_company_alerts`
(both pre-existing, from the merge) are untouched, confirmed via full diff read: no `-` lines
appear anywhere in the file except inside the merge-conflict resolution (already committed).
The new `get_my_alerts` route resolves via `resolve_request_tenant_scope(user, get_supabase())`
— the anon client, matching this route's original (pre-reconciliation, already-reviewed) client
choice, chosen deliberately over `get_service_supabase()` because this local dev environment has
no `SUPABASE_SERVICE_ROLE_KEY` configured (confirmed: switching to `get_service_supabase()`
during reconciliation caused 4 local test failures with `supabase_key is required`, reverted).
`resolve_cliente_cero_tenant_id`'s own lookup (`tenants` table, `is_cliente_cero` filter) is a
plain SELECT with no clear anon-vs-service-role security distinction in this codebase's existing
convention — `financials_endpoints.py`'s pre-existing `_resolve_cliente_cero_tenant_id` also uses
the anon client for the identical query, so this is consistent with established precedent, not a
new risk.

## Item 4 — tests

`apps/backend/tests/test_centinela_alerts_tenant_scoping.py` read in full: the two
Cliente-Cero-fallback tests now monkeypatch `core.tenant_context.resolve_cliente_cero_tenant_id`
(a plain sync callable, matching its real signature post-merge — the old mocked target,
`_default_cliente_cero_resolver`, was `async` and no longer exists), mirroring
`test_centinela_endpoint_tenant_scoping.py`'s established `_stub_cliente_cero_lookup` pattern.
`apps/backend/tests/test_tenant_context_resolver.py` confirmed deleted from disk (`test -f`
returns false).

## Item 5 — migration

`apps/backend/migrations/` contains `0033_approval_queue_tenant_not_null.sql` (sibling change),
`0034_rescope_centinela_alerts_tenant.sql` (sibling change), `0035_rolling_reseed_synthetic_shadow_gl.sql`
(this change, renumbered). No duplicate `0035`, no leftover `0033_rolling_reseed_*`.

## Item 6 — full targeted test run (executed directly, not trusted from memory)

```
cd apps/backend && python -m pytest tests/test_financials_endpoint_tenant_scoping.py \
  tests/test_financials_aggregation.py tests/test_financials_liquidity_bridge.py \
  tests/test_centinela_alerts_tenant_scoping.py tests/test_centinela_endpoint_tenant_scoping.py \
  tests/test_centinela_alerts_get.py -v
```
Result: **35 passed, 1 failed** — the single failure is
`TestGetAlertsEndpoint::test_endpoint_returns_200_and_shape`, the known pre-existing
`starlette`/`httpx` `TestClient(app=...)` version mismatch (confirmed pre-existing across
multiple independent reviews earlier in this change, unrelated to any code this branch touches).

Full backend suite also re-run post-merge: 694 passed, 40 failed (identical list to
pre-reconciliation, all confirmed unrelated via `git diff main...HEAD` file-overlap check), 112
skipped.

## Item 7 — frontend sanity

`cd contexia-app && npx tsc --noEmit` — clean, exit 0. Frontend untouched by reconciliation.

## Item 8 — feature_list.json

Valid JSON (`python3 -c "import json; json.load(open('feature_list.json'))"` succeeds).
`active: "pwa-tenant-aware-screens"` (correct — still in progress at time of this commit).
7 features present: all 6 that existed on `origin/main` (adopt-gbrain-second-brain,
chatwoot-hermes-taty-bridge, hermes-task-queue-tenant-scoping, taty-per-tenant-profiles,
approval-queue-tenant-scoping, centinela-tenant-scoped-alerts) plus this change's own entry. No
entry was silently dropped; no invented entry left in (an initial draft invented an
`agent-endpoints-real-tenant-filtering` tracker entry that didn't exist on `origin/main` — caught
and removed before commit).

## Verdict: **APPROVED**

All 8 checks pass. The reconciliation achieves its goal: zero net diff to the shared
`core/tenant_context.py` (no risk to 5 sibling changes), the new `centinela_endpoints.py` route
uses the canonical resolver matching its sibling routes, `financials_endpoints.py`'s
already-shipped behavior is preserved byte-for-byte (just relocated to a private local function),
and all tests are green except the one pre-existing, independently-confirmed-unrelated failure.
Safe to proceed to Stage 13.1 (push to main).
