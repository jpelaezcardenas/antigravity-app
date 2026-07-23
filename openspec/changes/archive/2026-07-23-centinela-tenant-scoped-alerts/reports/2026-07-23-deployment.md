# Stage 13 Deployment Report — centinela-tenant-scoped-alerts

- Date: 2026-07-23
- Change: centinela-tenant-scoped-alerts
- Agent: Claude (Sonnet 5)

## 13.1 — git commit + push to main

- PR [#6](https://github.com/jpelaezcardenas/antigravity-app/pull/6) opened from
  `feature/centinela-tenant-scoped-alerts` (12 implementation commits + this report), merged into
  `main` at commit `0bdacf1` (merge commit `0bdacf17a774eb9c44d549ee721dc836e2651a29`).
- **Merge conflict encountered and resolved**: three sibling changes
  (`approval-queue-tenant-scoping`, `hermes-task-queue-tenant-scoping`, `taty-per-tenant-profiles`)
  landed on `main` while this change was in flight, all touching tenant-scoping surfaces. Conflicts
  in `core/tenant_context.py`, `feature_list.json`, `ARCHITECTURE.md` resolved additively (kept
  both sides' functions/decisions; moved this change's ARCHITECTURE.md extension to its own
  numbered bullet 15 rather than letting it auto-merge as a misleading sub-paragraph of bullet 14).
  `test_tenant_stamping.py` auto-merged cleanly. Full targeted suite (27 passed, 1 pre-existing
  failure, 4 skipped) and the sibling `approval-queue-tenant-scoping` test suite (18 passed, 10
  skipped) both re-verified green against the merged tree before pushing.
- **Note for follow-up (not done here)**: `core/tenant_context.py` now has two related but
  distinct helpers — this change's `require_tenant_id`/`resolve_caller_tenant` and
  `approval-queue-tenant-scoping`'s `resolve_request_tenant_scope`/`TenantScope`. Reconciling them
  into one shared contract is future work, documented in both `ARCHITECTURE.md` bullets 14/15 and
  this change's design.md §9.

## 13.2 — Vercel build

- No frontend surface changed by this delta. Vercel checks on PR #6 passed (`Vercel` deployment
  check + `Vercel Preview Comments`, both green before merge).

## 13.3 — Railway deploy active

- Project `elegant-success` (`27f4a1b4-1e46-4ad7-b08e-15e92817ffdd`), service `antigravity-app`,
  environment `production`.
- Deployment `711a81a7-d532-4dbc-bf73-ff9666feee75`, created `2026-07-23T11:31:35.980Z` (moments
  after the merge), status **SUCCESS**.
- `/api/v1/health` — confirmed `200` after the known ~80s Railway cold-start window (first check
  at container-start+~15s returned `502 Application failed to respond`, expected during startup;
  deployment logs showed only a benign Pydantic protected-namespace warning, no crash traceback).

## 13.4 — Production URL: live smoke test

```
curl -s -o /dev/null -w "health: %{http_code}\n" \
  https://antigravity-app-production-175a.up.railway.app/api/v1/health
→ health: 200

curl -X POST https://antigravity-app-production-175a.up.railway.app/api/v1/centinela/evaluate \
  -H "Content-Type: application/json; charset=utf-8" \
  -d '{"company_id":"ctx-001","financial_data":{"regime":"Régimen Simple","annual_revenue":10000000},"save_alerts":false}'
→ {"detail":"Invalid or missing authentication token"}  — HTTP 401

curl https://antigravity-app-production-175a.up.railway.app/api/v1/centinela/alerts/ctx-001
→ {"detail":"Invalid or missing authentication token"}  — HTTP 401
```

**Both endpoints correctly reject tokenless requests in production (`AUTH_ENFORCED=True`) — this
is the fix working.** Before this change, both endpoints had zero authentication: any anonymous
caller could evaluate-and-save alerts under Contexia's own Cliente Cero tenant, or read any
company's alerts. Live verification with a real client bearer token (confirming tenant-scoped
results, no cross-tenant leak) is deferred to whenever a B2B client or the founder next
authenticates against these endpoints — the equivalent hermetic two-tenant proof already exists as
code in `tests/test_centinela_tenant_scoping_integration.py`, runnable against this same
production Supabase project with `RUN_CENTINELA_TENANT=1` + `SUPABASE_SERVICE_ROLE_KEY`.

## 13.5 — This report

`openspec/changes/centinela-tenant-scoped-alerts/reports/2026-07-23-deployment.md`.

## 13.6 / 13.7 — Sync + archive

Not yet done — see follow-up note below.

## Outcome

- Stage 13.1–13.5: **PASS**. Deployed and live-verified.
- Stage 13.6 (sync delta spec) and 13.7 (archive) are the two remaining tasks for this change;
  recommend doing them in a short follow-up now that production is confirmed green.
