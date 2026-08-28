# Review — task crm-alta-tiered-provisioning

**Verdict:** APPROVED

## Checkpoints

- C1 (plan_tier validated before either insert): [x] `apps/backend/services/crm_service.py:226-229` raises `ValueError` on invalid `plan_tier` before the `tenants.insert` (line 235-239) and `b2b_clients.insert` (line 254). No partial-insert risk.
- C2 (plan_tier written to both tenants and b2b_clients): [x] `crm_service.py:237` (`tenants` insert dict includes `"plan_tier": plan_tier`), `crm_service.py:251` (`b2b_clients` row dict includes `"plan_tier": plan_tier`).
- C3 (generate_link, not create_user; no Auth password): [x] `crm_service.py:287` calls `client.auth.admin.generate_link({"type": "invite", "email": email})`. No `create_user`/password call for Auth. `password_hash: secrets.token_hex(32)` at line 298 writes to the legacy `usuarios` table column (unrelated to the Supabase Auth credential) — expected and documented.
- C4 (usuarios.plan gets real tier): [x] `crm_service.py:297` — `"plan": plan_tier` (no longer hardcoded `"starter"`).
- C5 (frontend tier options match plan_features.py exactly): [x] `core/plan_features.py` keys = `freemium, starter, growth, enterprise`; `contexia-app/lib/crm-api.ts:28-29` `PlanTier`/`PLAN_TIERS` match exactly; `B2bRetainersTab.tsx` renders from `PLAN_TIERS`.
- C6 (endpoint 400 on invalid tier, not raw exception): [x] `crm_endpoints.py:67-70` wraps `ValueError` → `HTTPException(400)`.
- C7 (tests actually pass): [x] Personally ran `python -m pytest tests/test_crm_service_b2b_writes.py tests/test_crm_endpoints.py tests/test_plan_features.py -q` → 35 passed (matches report). Broader sweep `-k "crm or retention"` (same exclusions) → 80 passed, 20 skipped, 0 failed (matches report exactly).
- C8 (gotrue API shape claim verified): [x] Inspected installed `gotrue.types` directly — `GenerateLinkResponse.__annotations__` = `{'properties': 'GenerateLinkProperties', 'user': 'User'}`, `GenerateLinkProperties.__annotations__` includes `action_link: str`. Matches design.md/impl claims exactly.
- C9 (TestClient pre-existing breakage, not introduced by this change): [x] Ran `tests/test_centinela_alerts_get.py` (untouched by this change) — fails with `TypeError: Client.__init__() got an unexpected keyword argument 'app'` in `starlette/testclient.py:399`, confirming the pre-existing `starlette`/`httpx` mismatch. The deviation from tasks.md 4.2 (no new `TestClient`-based 400 test) is justified — the same failure would hit any new test using `TestClient` here, and service-layer coverage exists (`test_rejects_invalid_plan_tier`).
- C10 (tsc clean): [x] `npx tsc --noEmit` in `contexia-app/` produced zero output (no errors).
- C11 (OpenSpec ADDED vs MODIFIED correct): [x] `openspec/specs/crm-b2b-retainers/spec.md` (current main spec) has no requirement mentioning alta/create/`plan_tier`/`invite_link` — only roster listing, payment ledger, payment grid, RLS, and the Búnker UI section. `ADDED Requirements` in the delta spec is the correct verb.
- C12 (docs-sync / ARCHITECTURE.md): [x] No new container, external dependency, or data-flow change introduced (reuses existing `gotrue`/Supabase Auth capability already in the architecture) — no `ARCHITECTURE.md` update required, and none was made. Correct to leave it untouched.
- C13 (Stage 11 / deploy): [ ] Not yet deployed — tasks.md Stage 11 (11.1-11.5) all unchecked, and `progress/impl_crm-alta-tiered-provisioning.md` explicitly says "Awaiting reviewer pass before Stage 11". This is expected at this stage of the workflow (review precedes deploy), not a defect in the implementation — flagging so the change is not archived until Stage 11 completes.

## Required changes (if any)

None. Code review confirmed all claims in proposal.md/design.md/impl report are accurate to the
actual code (not just self-reported): validation ordering, dual writes, generate_link usage
(no Auth password), usuarios.plan fix, frontend/backend tier parity, and the documented
TestClient limitation. All test runs and the tsc check were independently reproduced by the
reviewer with matching results.

Before archiving: implementer/leader must still complete Stage 11 (deploy to Railway/Vercel,
verify `POST /api/v1/crm/b2b/clients` on production accepts `plan_tier` and returns
`invite_link`, and write the deployment report) per `CLAUDE.md` §8 and `ARCHITECTURE.md`
Decision #2 — this review approves the code/tests only, not a finished, deployed change.
