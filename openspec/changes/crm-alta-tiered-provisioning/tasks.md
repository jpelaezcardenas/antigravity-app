## 1. Backend: `create_b2b_client` accepts and writes `plan_tier`

- [ ] 1.1 Write a failing test asserting: `create_b2b_client(name=..., plan_tier="growth")`
      results in both the created `tenants` row and `b2b_clients` row having `plan_tier ==
      "growth"`; and `create_b2b_client(name=...)` (no `plan_tier`) defaults both to `"starter"`.
- [ ] 1.2 In `crm_service.py::create_b2b_client`, add a `plan_tier: str = "starter"` parameter,
      validate it against `core/plan_features.py::PLAN_FEATURES.keys()` (raise `ValueError` with
      a clear message on an invalid value, checked before either insert), and add `"plan_tier":
      plan_tier` to both the `tenants` insert dict and the `b2b_clients` row dict.

## 2. Backend: `_provision_b2b_client_login` writes the real tier, not hardcoded "starter"

- [ ] 2.1 Write a failing test asserting: provisioning a login with `plan_tier="enterprise"`
      results in `usuarios.plan == "enterprise"`, not the literal `"starter"`.
- [ ] 2.2 Add a `plan_tier: str` parameter to `_provision_b2b_client_login`, pass it through from
      `create_b2b_client`, and use it in the `usuarios.upsert(...)` call instead of the hardcoded
      `"starter"` string.

## 3. Backend: replace the discarded password with `generate_link`

- [ ] 3.1 Write a failing test asserting: provisioning a login calls
      `client.auth.admin.generate_link` with `{"type": "invite", "email": ...}` (not
      `create_user` with a random password), and `_provision_b2b_client_login` returns both the
      `user_id` and the `action_link`.
- [ ] 3.2 Rewrite `_provision_b2b_client_login` to call `generate_link` instead of `create_user`;
      remove the `secrets.token_urlsafe(12)` password generation entirely (the docstring's
      "distribution is the founder's responsibility" note is now obsolete — update it to describe
      the invite-link handoff instead).
- [ ] 3.3 `create_b2b_client` surfaces the returned link on the response dict as `invite_link`
      when provisioning succeeded; confirm the response is `None`/absent for that field when no
      email was supplied or provisioning failed (best-effort path unchanged).

## 4. Backend: endpoint + request model

- [ ] 4.1 Add `plan_tier: Optional[str] = None` to `CreateB2bClientRequest`
      (`crm_endpoints.py`), pass it through to `create_b2b_client` (let the service-layer default
      apply when omitted, per design.md D1 — don't duplicate the default in the Pydantic model).
- [ ] 4.2 Confirm via the existing `test_crm_endpoints.py` suite (or add a case if none covers
      alta) that a request with an invalid `plan_tier` string returns a clear 4xx, not a raw
      Postgres constraint error.

## 5. Frontend: tier selector + invite-link display

- [ ] 5.1 Add a `plan_tier` field to `CreateB2bClientInput` and `invite_link`/`plan_tier` to the
      `B2bClient` interface in `contexia-app/lib/crm-api.ts`.
- [ ] 5.2 Add a tier `<select>` to the alta form in `B2bRetainersTab.tsx`, populated from a local
      constant array mirroring `core/plan_features.py`'s 4 keys (comment referencing that file,
      per design.md D4) — default selection `"starter"`, matching the backend default.
- [ ] 5.3 After a successful alta that returns `invite_link`, display it in a copyable field/alert
      in the form area (not just logged to console) so the vendor can immediately copy it for
      WhatsApp/email delivery — clears when the vendor starts a new alta.

## 6. Testing

- [ ] 6.1 Full backend suite green for the touched files (`test_crm_endpoints.py`,
      `crm_service.py`'s existing test coverage, plus the new tests from tasks 1.1/2.1/3.1);
      confirm no regression to `set_b2b_client_status`/payments/contact flows.
- [ ] 6.2 `npx tsc --noEmit` in `contexia-app/` — zero errors.
- [ ] 6.3 Dev-server check: open the Búnker CRM/Ventas → B2B/Retainers tab, confirm the tier
      selector renders and the alta form still submits successfully end-to-end against a local or
      the production backend (whichever is reachable), same verification-depth caveat as
      Subdomain 3 (local Supabase env gap, real correctness covered by the pytest suite).

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build complete (green)
- [ ] 11.3 Railway deploy active (backend change)
- [ ] 11.4 Production URL: confirm `POST /api/v1/crm/b2b/clients` accepts `plan_tier` and returns
      `invite_link` for an email-bearing alta (curl or Búnker UI test with a throwaway client,
      cleaned up after)
- [ ] 11.5 Create report: `openspec/changes/crm-alta-tiered-provisioning/reports/YYYY-MM-DD-deployment.md`
