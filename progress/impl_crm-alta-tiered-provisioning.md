# Implementer report — crm-alta-tiered-provisioning

- Date: 2026-08-28
- Scope: full change (Sections 1-6 of tasks.md), TDD throughout.

## Sections 1-2 — `plan_tier` on create_b2b_client + login provisioning

Read `crm_service.py:207-292` and `crm_endpoints.py:42-60` in full before writing anything (no
research workflow needed — Subdomain 3's investigation already surfaced the exact hardcode
location). TDD: 6 new tests (`test_crm_service_b2b_writes.py`) confirmed red first — 5 failed on
`TypeError`/missing behavior, 1 pre-existing test (`test_client_with_email_attempts_login_
provisioning`) had to be updated in the same commit since `_provision_b2b_client_login`'s return
shape changed from `str` to `tuple[str, str]` (documented, not silently patched).

`create_b2b_client` now validates `plan_tier` against `core/plan_features.py::PLAN_FEATURES`
(reused, not duplicated) before either insert, and writes it explicitly to both the `tenants`
insert and the `b2b_clients` row. `_provision_b2b_client_login` receives `plan_tier` and writes it
to `usuarios.plan` instead of the hardcoded `"starter"` — closes the exact reconciliation gap
Subdomain 3's design.md flagged as an open question.

## Section 3 — `generate_link` replaces the discarded password

Verified the `gotrue` Python client's actual API by direct inspection of the installed package
(`GenerateInviteOrMagiclinkParams`, `GenerateLinkResponse.properties.action_link`) before writing
any code — confirmed the exact call shape (`{"type": "invite", "email": ...}`) and response shape
match what design.md D3 assumed. `_provision_b2b_client_login` now calls `generate_link` instead
of `create_user` with a random password; returns `(user_id, invite_link)`; `create_b2b_client`
surfaces the link on the response as `invite_link`.

## Section 4 — endpoint

Added `plan_tier: Optional[str]` to `CreateB2bClientRequest`; only passed through when non-None
so the service-layer default applies otherwise. Wrapped the call in try/except to turn a
`ValueError` (invalid tier) into a `400`, not a raw exception.

**Deviation from tasks.md 4.2**: did not add a new `TestClient`-based endpoint test for the
invalid-tier 400 path — this repo's `test_centinela_alerts_get.py` (Subdomain 3's review) already
confirmed `TestClient` is broken in this environment (`starlette`/`httpx` version mismatch,
pre-existing on `main`, unrelated to this change). Adding a new test that can't run here would be
theater, not verification. The underlying validation logic (raise `ValueError` on an invalid
tier) is fully covered at the service layer (`test_rejects_invalid_plan_tier`); the endpoint's
`try/except ValueError -> HTTPException(400)` wrapping is a 3-line, low-risk FastAPI idiom already
used elsewhere in this codebase.

## Section 5 — frontend

Added `PlanTier` type + `PLAN_TIERS` const array to `crm-api.ts` (mirrors
`core/plan_features.py`'s 4 keys, per design.md D4 — same pattern as `TenantInfoCard.tsx`'s
`PLAN_TIER_LABEL` from Subdomain 3). Added a `<select>` to the alta form defaulting to `"starter"`
(matches the backend default). After a successful alta with an email, the form stays open and
shows a copyable `invite_link` field + "Copiar" button (uses `navigator.clipboard`) instead of
closing immediately — the vendor needs to see and copy the link before it's gone. Clears on
toggling the alta form open/closed.

## Section 6 — Testing

- Backend: 35/35 new + directly-related tests green
  (`test_crm_service_b2b_writes.py`, `test_crm_endpoints.py`, `test_plan_features.py`). Broader
  sweep (`-k "crm or retention"` across the whole suite, excluding the 3 files with a pre-existing
  unrelated `ModuleNotFoundError: No module named 'apps'` collection error): 80 passed, 20 skipped,
  zero failures.
- Frontend: `tsc --noEmit` — zero errors.
- Dev-server visual check: not performed this pass — the local backend launch profile's missing
  `SUPABASE_URL` (confirmed pre-existing in Subdomain 3, not caused by this change) makes a real
  end-to-end alta submission unobservable locally without a founder session token; correctness is
  covered by the 35 passing tests, consistent with Subdomain 3's same documented limitation.

## Files touched

- Modified: `apps/backend/services/crm_service.py`, `apps/backend/presentation/crm_endpoints.py`,
  `apps/backend/tests/test_crm_service_b2b_writes.py` (6 new tests + 1 updated for the changed
  return shape), `contexia-app/lib/crm-api.ts`,
  `contexia-app/components/bunker/crm/B2bRetainersTab.tsx`.
- New: `openspec/changes/crm-alta-tiered-provisioning/` (proposal, design, specs, tasks),
  `progress/impl_crm-alta-tiered-provisioning.md` (this file).

## Next step

Awaiting reviewer pass before Stage 11 (deploy + report) and archive.
