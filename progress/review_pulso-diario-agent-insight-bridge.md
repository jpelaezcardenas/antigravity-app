# Review — task pulso-diario-agent-insight-bridge

**Verdict:** APPROVED

## Checkpoints
- C1 (proposal/design/spec/tasks present and coherent): [x]
- C2 (`operator_task_service.submit_completed_insight()` creates `completed` row directly, no
  pending/dispatched hop, rejects unknown `tenant_id` via `tenant_exists`, never falls back to
  Cliente Cero): [x] — `apps/backend/services/operator_task_service.py:122-148`
- C3 (`list_completed_tasks(tenant_id=...)` filter applied, not silently ignored): [x] —
  `operator_task_service.py:105-119`, `.eq("tenant_id", tenant_id)` mirrors the existing
  `task_type` filter pattern
- C4 (`POST /insights` genuinely gated by `require_hermes_bridge_token`, imported not
  duplicated, service failure → 400): [x] — `presentation/pulso_diario_endpoints.py:17,75,96-97`;
  import confirmed sourced from `sell_machine_endpoints.py:44-56` (single definition, not
  copy-pasted)
- C5 (financials fallback ordering — unresolved-tenant branch returns before any fallback logic
  runs, non-empty status never triggers `list_completed_tasks`, malformed result fails closed):
  [x] — `financials_endpoints.py:186-200` confirms `if tenant_id is None: return _empty_snapshot()`
  executes and returns at line 187-188, strictly before `compute_pulso_daily_snapshot` (line 195)
  is even called, so a caller with no resolved tenant can never reach the Supabase insight query.
  The fallback call (`_latest_agent_insight_snapshot`, line 197) is nested inside
  `if snapshot.get("status") == "empty":` (line 196) — a healthy/non-empty snapshot short-circuits
  before that call. `_latest_agent_insight_snapshot` (lines 79-99) validates
  `required_keys.issubset(result.keys())` and returns `None` (not a crash) on a malformed/missing
  `result`, which the caller then treats as "no insight" and falls through to the original zeroed
  snapshot.
- C6 (delta spec is a genuine, non-contradictory addition to the live spec): [x] — diffed
  `openspec/specs/pulso-financials-api/spec.md` against the changed delta; the pre-existing
  requirement text (lines 1-17) is preserved verbatim, with only new paragraph + 3 new scenarios
  appended (lines 16-23, 52-67) that are additive, not competing, with the existing "Empty ledger
  returns zeroes" scenario (still true when no insight exists).
- C7 (tests green): [x] — `pytest tests/test_operator_task_service.py
  tests/test_pulso_diario_insight_endpoint.py tests/test_financials_agent_insight_fallback.py
  tests/test_financials_endpoint_tenant_scoping.py -q` → **38 passed**, ~78s. The 78s runtime and
  the `two_test_tenants`/`cleanup_test_entries` fixtures in
  `test_financials_endpoint_tenant_scoping.py` confirm live Supabase inserts/deletes against real
  hermetic throwaway tenants — this is a pre-existing pattern in that file (predates this change,
  used by `per-tenant-client-access`), not something this change introduced.
- C8 (no unrelated files in this change's diff): [x] — `git status --short` shows `AGENTES.md` and
  `progress/current.md` modified and `ai-specs/references/` untracked; diffed both modified files
  and confirmed their content (a WhatsApp inbound-only operating rule, and a `progress/current.md`
  session-pointer rewrite) is unrelated to this change — consistent with parallel sessions, not
  something this implementer touched for this task.
- C9 (docs-sync — no architecture container/dependency changed, so no `ARCHITECTURE.md` update
  required): [x] — this change reuses existing containers (`operator_tasks` table, Hermes bridge
  token, `/financials` endpoint) with no new external dependency or container; `ARCHITECTURE.md`
  correctly left untouched.

## Notes (non-blocking)
- `require_hermes_bridge_token` is fail-open when `HERMES_BRIDGE_TOKEN` is unset (see
  `sell_machine_endpoints.py:49-51`, "No-op when unset — preserves today's open behavior"). This is
  pre-existing behavior from `hermes-task-queue-tenant-scoping`, reused as-is by this change, not
  introduced here — flagging for awareness only, not a required fix for this change.
- Design explicitly defers a frontend "estimated" badge distinguishing agent-insight data from real
  Shadow GL data (D3) — a real founder product decision, correctly out of scope per the design doc
  rather than silently decided by the implementer.

## Required changes (if any)
None.
