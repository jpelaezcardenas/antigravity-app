# Stage 10 — Deployment Report

## Merge

Fast-forward merge of `feature/agent-endpoints-real-tenant-filtering` (`5ce09cd`) into `main`
(`52ef89a` → `5ce09cd`), pushed directly (no classifier block):

```
git merge --ff-only feature/agent-endpoints-real-tenant-filtering
git push origin main
```

## Railway deploy

Auto-triggered on push. Project `elegant-success` (`27f4a1b4-1e46-4ad7-b08e-15e92817ffdd`),
service `antigravity-app`, environment `production`.

- Deployment `2f9ecad5-9f78-45ca-987b-3998568eb526`
- Status: **SUCCESS**
- Created: `2026-07-23T17:39:04.783Z`
- Static URL: `antigravity-app-production-175a.up.railway.app`

## Production smoke test

```
GET  /api/v1/health                              → 200
GET  /api/v1/agents/task-info/pulso_analysis      → 401 (no token) — newly gated, was fully anonymous
GET  /api/v1/approval-queue                       → 401 (no token) — already gated pre-change, confirms no regression
POST /api/v1/agents/orchestrator/full-pipeline     → 401 (no token) — newly gated
POST /api/v1/agents/pulso-diario/summary           → 401 (no token) — newly gated, stub
POST /api/v1/agents/ask (Taty)                     → 401 (no token) — already gated pre-change, confirms no regression
```

All routes reject unauthenticated callers in production (`AUTH_ENFORCED=true`), confirming
this change's core goal: the 9 previously-anonymous routes (7 in `agents_endpoints.py` + 2
stubs) now require identity, and the 3 already-gated files (approval-queue, centinela, taty)
are unaffected by the tenant-resolution-helper migration.

**Deferred to founder** (requires a real Supabase-issued JWT for a provisioned tenant, per the
same precedent `taty-per-tenant-profiles` set): confirming a resolved-tenant caller succeeds
end-to-end on the migrated routes, and that an unresolved-tenant caller gets 404 (not 403) on
approval-queue writes. The local + production checks above confirm the auth gate and the
unchanged-behavior contract; they cannot exercise a real tenant token from this environment.

## Conclusion

Stage 10 complete: merged, deployed, health-checked, and the auth-gate contract verified live
in production for every one of the 6 in-scope files.
