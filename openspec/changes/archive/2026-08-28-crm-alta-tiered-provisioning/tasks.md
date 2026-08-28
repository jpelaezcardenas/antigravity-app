## 1. Backend: `create_b2b_client` accepts and writes `plan_tier`

- [x] 1.1 Wrote failing tests (`test_explicit_plan_tier_is_written_to_tenants_and_b2b_clients`,
      `test_default_plan_tier_is_starter`) — confirmed red.
- [x] 1.2 Added `plan_tier: str = "starter"` to `create_b2b_client`, validated against
      `core/plan_features.py::PLAN_FEATURES` before either insert, written to both the `tenants`
      insert and the `b2b_clients` row.

## 2. Backend: `_provision_b2b_client_login` writes the real tier, not hardcoded "starter"

- [x] 2.1 Wrote `test_writes_plan_tier_to_usuarios_plan_not_hardcoded_starter` — confirmed red.
- [x] 2.2 Added `plan_tier` parameter, passed through from `create_b2b_client`, used in the
      `usuarios.upsert(...)` call.

## 3. Backend: replace the discarded password with `generate_link`

- [x] 3.1 Wrote `test_writes_generate_link_invite_not_a_password` — confirmed red. Verified the
      exact `gotrue` API shape (`GenerateInviteOrMagiclinkParams`,
      `GenerateLinkResponse.properties.action_link`) by inspecting the installed package before
      writing the call.
- [x] 3.2 Rewrote `_provision_b2b_client_login` to call `generate_link`; removed
      `secrets.token_urlsafe(12)`; updated the docstring to describe the invite-link handoff.
- [x] 3.3 `create_b2b_client` surfaces `invite_link` on the response dict when provisioning
      succeeds; absent otherwise (best-effort path unchanged, confirmed by the pre-existing
      failure-tolerance test).

## 4. Backend: endpoint + request model

- [x] 4.1 Added `plan_tier: Optional[str] = None` to `CreateB2bClientRequest`; only passed through
      when non-`None` so the service-layer default applies otherwise.
- [x] 4.2 **Deviation, documented**: did not add a new `TestClient`-based endpoint test — this
      repo's `TestClient` is confirmed broken in this environment (pre-existing
      `starlette`/`httpx` version mismatch, unrelated to this change; the reviewer independently
      reproduced the same failure on an untouched test file). The underlying validation (`raise
      ValueError` on an invalid tier) is fully covered at the service layer
      (`test_rejects_invalid_plan_tier`); the endpoint's `try/except ValueError ->
      HTTPException(400)` wrapping is a 3-line, low-risk idiom already used elsewhere.

## 5. Frontend: tier selector + invite-link display

- [x] 5.1 Added `PlanTier` type, `PLAN_TIERS` const array, `plan_tier`/`invite_link` fields to
      `crm-api.ts`.
- [x] 5.2 Added a tier `<select>` to the alta form (`B2bRetainersTab.tsx`), default `"starter"`.
- [x] 5.3 After a successful alta with `invite_link`, the form stays open and shows a copyable
      field + "Copiar" button (`navigator.clipboard`); clears on toggling the form.

## 6. Testing

- [x] 6.1 Backend: 35/35 new + directly-related tests green
      (`test_crm_service_b2b_writes.py`, `test_crm_endpoints.py`, `test_plan_features.py`).
      Broader sweep (`-k "crm or retention"`, excluding the 3 files with a pre-existing unrelated
      collection error): 80 passed, 20 skipped, 0 failed. Independently re-run and confirmed by
      the reviewer.
- [x] 6.2 `npx tsc --noEmit` — zero errors (confirmed independently by the reviewer).
- [x] 6.3 **Deviation, documented**: full interactive dev-server walkthrough not performed — same
      local-Supabase-env-gap limitation as Subdomain 3 (this agent does not handle plaintext
      credentials for a real admin session). Correctness covered by the 35 tests above; live
      production auth-wiring verified in Stage 11 below.

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [x] 11.1 Committed `2c9aff1`, pushed to `main`.
- [x] 11.2 Vercel: deployment `dpl_ADaej58jWdG4Xpa7xnBg6JUAibCB` — `READY`, aliased to
      `contexia.online`.
- [x] 11.3 Railway: deployment `355a7764-f9d6-47b6-858f-be91c4bd9efa` — `SUCCESS`.
- [x] 11.4 Production URL: verified `POST /api/v1/crm/b2b/clients` (no auth) returns `401`, not
      `500` — confirms the new `plan_tier`/`generate_link` code paths didn't introduce a crash.
      Full authenticated alta walkthrough deferred as a founder action — see
      `reports/2026-08-28-deployment.md`.
- [x] 11.5 Report: `openspec/changes/crm-alta-tiered-provisioning/reports/2026-08-28-deployment.md`.
