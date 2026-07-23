# Review — task 2 (taty-per-tenant-profiles)

**Verdict:** APPROVED

## Scope verified

`git status --short` shows exactly the claimed diff:
- `M apps/backend/services/taty_service.py`
- `?? apps/backend/tests/test_taty_ask_tenant_scoping.py`
- `?? progress/impl_taty-per-tenant-profiles-task2.md`

No file under `apps/backend/presentation/` or elsewhere was touched — the report's claim of
"no other section touched" holds. This matches tasks.md section 2 (2.1–2.3) exactly; no scope
creep into sections 3–5 (endpoint auth, Telegram translation, route deletion — correctly deferred).

## Checkpoints

- C1 (`ask()` renamed `company_id`→`tenant_id`, calls `_get_tenant_profile` directly): [x] —
  `taty_service.py:115-153`. `_get_agent_profile` is genuinely gone (`grep -rn
  "AGENT_PROFILES|_get_agent_profile" apps/backend` returns zero hits outside the test file that
  asserts its absence via `not hasattr(...)`, `test_taty_ask_tenant_scoping.py:93-98`).
- C2 (`_retrieve_chunks` keyed by `kb_client_id`, not `company_id`): [x] — `taty_service.py:276`,
  `client_id = profile["kb_client_id"]`. Independently verified D7's claim against
  `kb_seeding_service.py:254-271`: both pgvector and in-memory `retrieve_similar` branches already
  retry with `client_id="__global__"` — no change needed there, confirmed correct.
- C3 (régimen omission, no dangling artifact): [x] — `taty_service.py:316-317`, `regimen_clause =
  f" (Régimen {regimen})" if regimen else ""`. When `regimen` is falsy the clause is the empty
  string — no "(Régimen )" or "Régimen None" artifact, confirmed by reading the interpolation
  site directly (line 320) and by the `context`-empty branch (330-336) which never references
  `regimen` at all. Compliant with `.antigravity/GROUND_TRUTH.md:52` ("Nunca inventar claims
  regulatorios") and design D1.
- C4 (remaining `company_id` hits in `taty_service.py` are legitimate): [x] — `grep -n
  "company_id" apps/backend/services/taty_service.py` returns 3 hits, all sourced from the
  `tenants` row (`.select(...company_id)`, `profile["company_id"] = row.get("company_id")`,
  `kb_client_id = row.get("company_id") or row["id"]`) — none are leftover `ask()`-param
  references.
- C5 (design D5 "hard rename, no compat shim"): [x] — deleting `_get_agent_profile` outright
  (rather than deprecating) is the correct reading of D5, which explicitly rejects a compat
  alias as "exactly the kind of ownerless duplicate surface this change is closing." A shim would
  also have silently masked a caller still passing a legacy demo key instead of surfacing
  `tenant_not_found`.
- C6 (3 broken live callers, temporary state): [x] — independently confirmed via `grep -rn
  "\.ask\(" apps/backend/presentation/`: exactly 3 hits (`agents_endpoints.py:63`,
  `taty_endpoints.py:144`, `telegram_endpoints.py:154`), matching the report with no 4th caller
  missed. Also confirmed no test file calls `.ask(` other than the new
  `test_taty_ask_tenant_scoping.py` (`grep -rn "\.ask\(" apps/backend/tests` → 2 hits, both in
  that file). Per design D5, all 3 callers are explicitly planned to be fixed "in this same
  change" (tasks 3–5); leaving them TypeError-broken between committed-but-unmerged tasks within
  a single OpenSpec change (not yet deployed, not yet merged to `main`) is the disclosed,
  acceptable state D5 describes — not a hazard the leader must jump the task order to fix.
  `taty_endpoints.py`'s call site is wrapped in `try/except Exception` (line 137/159-164), so the
  failure mode today is a caught 500, not an uncaught crash — consistent with "temporary, not
  catastrophic."
- C7 (test quality — the two "accidentally passed at RED" tests are correct at GREEN): [x] —
  independently re-derived the report's reasoning:
  `test_regimen_set_includes_regimen_clause` was trivially true at RED (old code always
  interpolated régimen unconditionally) but is a real assertion at GREEN (now conditional, and
  still correctly included when `regimen` is set — verified by reading the GREEN code path at
  `taty_service.py:317`, not just trusting the claim).
  `test_cliente_cero_profile_retrieves_with_ctx_001_client_id` passed at RED only because the old
  fallback `profile.get("company_id", "__global__")` coincided with the Cliente Cero fixture also
  setting `company_id="ctx-001"` — the real assertion under test ("`_retrieve_chunks` reads
  `kb_client_id` specifically") is validated by its sibling test
  (`test_retrieve_chunks_passes_through_kb_client_id_to_retrieve_similar`), which *did* fail at
  RED and passes at GREEN for the right reason. Both are genuine, non-tautological assertions at
  GREEN.
- C8 (docs-sync): [x] — this task changes no container/dependency in `ARCHITECTURE.md`'s sense
  (internal service refactor only); no `ARCHITECTURE.md` update was required or owed.

## Test run (independently executed, not just trusted from the report)

```
pytest apps/backend/tests/test_taty_ask_tenant_scoping.py apps/backend/tests/test_taty_tenant_profiles.py -v
======================= 13 passed, 19 warnings in 4.05s =======================
```
13/13 confirmed, matching the report exactly test-for-test.

`bash init.sh` (structural gate, no `RUN_TESTS`): green — "Harness ready. You can start working."

`RUN_TESTS=1 bash init.sh` (full backend suite): **red** (multiple F/E markers). Investigated:
this is pre-existing and unrelated to task 2's diff — `git status --short` confirms this task
touches only `taty_service.py` + the new test file; the failing/hanging behavior traces to
`test_shadow_gl_stage8_e2e.py`, last modified at commit `95b9d44` (well before this branch's
task 1/2 work) and observed spawning many orphaned nested `pytest` subprocesses under load. Per
`tasks.md` section 7 ("Run Unit Tests and Verify Database State"), the full `RUN_TESTS=1 bash
init.sh` pass is explicitly a *separate, later* mandatory task (7.3), not part of task 2's
contract. Task 2's own scoped tests plus its collateral regression check (`test_taty_intent_router.py`
+ `test_taty_lead_router.py`, 47 passed, reported and spot-confirmed by grep showing neither
suite references `.ask(` or `_get_agent_profile`) are the correct green bar for *this* task.
Flagging for whoever executes task 7: confirm `test_shadow_gl_stage8_e2e.py`'s resource behavior
before relying on a clean `RUN_TESTS=1` run.

## Required changes

None for task 2 as scoped.

## Note for the leader (not a task-2 defect)

`progress/current.md` still reflects the prior `chatwoot-hermes-taty-bridge` session and hasn't
been updated for `taty-per-tenant-profiles` — routine housekeeping, not this reviewer's job to
fix, but worth updating before the next session starts. Also: verify `test_shadow_gl_stage8_e2e.py`'s
subprocess-spawning behavior separately before task 7's full-suite gate is attempted, since it
appears to make `RUN_TESTS=1 bash init.sh` unreliable/slow regardless of this change.
