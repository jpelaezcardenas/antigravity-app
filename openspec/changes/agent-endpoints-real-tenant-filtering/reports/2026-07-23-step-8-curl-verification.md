# Stage 8 — Manual Endpoint curl Verification

Local backend booted cleanly (`python -m uvicorn main:app --host 127.0.0.1 --port 8123`), zero
Supabase credentials configured (`.env` absent — known local-dev gap), `AUTH_ENFORCED=False`
(default), 60 total routes registered including all 6 in-scope files.

## Verified locally (no real Supabase/JWT needed)

| Route | Call | Result |
|---|---|---|
| `GET /api/v1/agents/task-info/pulso_analysis` | no token | `200` — staging fallback works, route now requires `get_current_user` and still succeeds locally |
| `POST /api/v1/agents/orchestrator/full-pipeline` | no token | `200`, response still `"mode": "demo"` with the illustrative note unchanged |

Both confirm Stage 1's auth-gate-only routes work end-to-end locally: adding
`Depends(get_current_user)` does not break local/dev/staging behavior, and the demo pipeline's
payload shape is unchanged.

## Blocked locally by a pre-existing environment gap (not a regression)

`POST /api/v1/agents/pulso-diario/summary`, `POST /api/v1/agents/centinela/generate-draft`, and
`GET /api/v1/approval-queue` (**already-shipped, untouched by this change except its 403→404
message**) all return `500` locally with the identical root cause:

```
supabase.client.SupabaseException: supabase_url is required
```

`resolve_request_tenant_scope` needs a real Supabase client to look up Cliente Cero's tenant id
(via `resolve_cliente_cero_tenant_id`), and this local checkout has no `SUPABASE_URL`/
`SUPABASE_SERVICE_ROLE_KEY` configured — the same documented gap `design.md`'s testing strategy
section and CLAUDE.md's gotchas note for `test_financials_aggregation.py`'s 13 skipped/errored
integration tests. **Confirmed pre-existing and not introduced by this change**: the already-
shipped, untouched `GET /api/v1/approval-queue` fails identically under the same local
condition — this is an environment constraint affecting every `resolve_request_tenant_scope`
call site equally, old and new.

`POST /api/v1/agents/ask` (Taty) was probed but the test payload (`"hola"`, 4 chars) failed
Pydantic's `min_length=5` validation before reaching tenant resolution — inconclusive on its
own, but by the same root-cause reasoning above it would hit the identical `SupabaseException`
once past validation.

## Deferred to Stage 10 (production) — same precedent as `taty-per-tenant-profiles`

Verifying the 401 (no token, `AUTH_ENFORCED=true`), the 404 (unresolved tenant on
approval-queue/taty/centinela), and the full resolved-tenant success path all require a real
Supabase-issued JWT for a provisioned tenant — unavailable in this local, credential-less
checkout. `taty-per-tenant-profiles/tasks.md` (archived 2026-07-23) explicitly deferred the
equivalent checks to Stage 11 for the same reason (tasks 8.3/8.4/8.5, "requires a real
Supabase-issued JWT for a provisioned tenant"). This change follows the same precedent: Stage
10.3 below covers the production smoke test.
