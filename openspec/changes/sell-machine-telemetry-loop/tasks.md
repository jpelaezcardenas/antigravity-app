## 1. Setup + verification

- [x] 1.1 Created branch `feature/sell-machine-telemetry-loop`.
- [x] 1.2 Re-confirmed `operator_task_service.py`'s existing functions and `crm_leads`'s
      `VALID_LEAD_STAGES` by reading the live source directly.
- [x] 1.3 Re-confirmed no scheduler/cron library exists in this repo (grep, no real match).

## 2. `list_completed_tasks` + funnel snapshot — TDD

- [x] 2.1 Wrote tests for `operator_task_service.list_completed_tasks(task_type=None)`: returns
      only `status="completed"` rows, optionally filtered by `task_type`, mocking
      `get_service_supabase` directly. Confirmed failing (function didn't exist).
- [x] 2.2 Authored `list_completed_tasks` in `apps/backend/services/operator_task_service.py`.
- [x] 2.3 Wrote tests for `crm_service.get_funnel_snapshot()` (module-level function, not a
      `CrmService` method — no tenant filtering needed for this Cliente Cero-only funnel) returning
      lead counts per `VALID_LEAD_STAGES` stage, mocking Supabase directly.
- [x] 2.4 Authored `get_funnel_snapshot()` in `apps/backend/services/crm_service.py`.
- [x] 2.5 4/4 new tests green. Full targeted suite (52 tests: this change + operator task + CRM)
      green, zero regression.

## 3. Copywriter/orchestration optional-parameter extension — TDD

- [x] 3.1 Wrote tests confirming `generate_hooks(count)` (no `report`) behaves identically to
      today (regression-guard: `_llm_generate_hooks` called with `report=None`), and
      `generate_hooks(count, report={...})` passes the report through to the isolated
      `_llm_generate_hooks` call point, still falling back to the deterministic hook set on LLM
      failure regardless of `report`. Confirmed failing (new parameter didn't exist).
- [x] 3.2 Extended `generate_hooks`/`_llm_generate_hooks` in
      `apps/backend/services/copywriter_service.py` with the optional
      `report: Optional[Dict] = None` parameter; added `_format_telemetry_report` to render it
      into the prompt, tolerant of an empty/thin report.
- [x] 3.3 Wrote tests for `run_creative_loop(count, target_segment=None, use_telemetry=False)`:
      `use_telemetry=False` (default) never calls `get_telemetry_report`; `use_telemetry=True`
      fetches the report (mocked) and passes it through to `generate_hooks`.
- [x] 3.4 Extended `run_creative_loop` in `apps/backend/services/sell_machine_service.py`; added
      `get_telemetry_report()` (aggregates `list_completed_tasks` for `post_content`/`run_ads_ab`
      via `_summarize_task_results` + `get_funnel_snapshot()` + `generated_at`) and imports from
      `crm_service`/`operator_task_service`.
- [x] 3.5 9/9 Sell Machine service tests green. Full targeted suite (49 tests: this change + Sell
      Machine + operator task) green, zero regression.

## 4. Telemetry report endpoint — TDD

- [x] 4.1 Wrote `test_telemetry_endpoint.py` (isolated FastAPI app + `httpx.AsyncClient` +
      `ASGITransport` + `pytest.mark.asyncio`, matching the established idiom): `GET
      /telemetry/report` returns the expected shape with a mocked `get_telemetry_report`; an
      empty/zeroed report still returns 200. Confirmed failing (route didn't exist).
- [x] 4.2 Added the route to `apps/backend/presentation/sell_machine_endpoints.py` (same file/flag
      as Changes E/F — reusing `SELL_MACHINE_CANONICAL`, no new flag).
- [x] 4.3 2/2 new endpoint tests green. Full targeted suite (106 tests: this change + Sell Machine
      + operator task + CRM + WhatsApp) green, zero regression.

## 5. (Optional) Búnker telemetry panel

- [x] 5.1 Skipped — not required for this change to be complete (Hermes/a human can already call
      the endpoint directly), and no real Manus telemetry exists yet to make a Búnker panel
      meaningful today. Noted explicitly in the deployment report.

## 6. Verify + DB state (MANDATORY before Stage 11)

- [x] 6.1 Ran the full targeted suite: 106/106 green (17 new + 89 pre-existing, zero regression).
      Confirmed via `git status --short` no `contexia-app/` files touched (Section 5 skipped).
- [x] 6.2 Confirmed live in Supabase (via MCP, direct SQL simulation pre-deploy): inserted a
      representative `operator_tasks` row with `status="completed"`, `task_type="post_content"`,
      `result={"impressions":500,"clicks":20}` (explicitly labeled pre-deploy verification data),
      confirmed the equivalent query returns it correctly, cleaned up.
- [x] 6.3 Wrote `openspec/changes/sell-machine-telemetry-loop/reports/2026-07-20-step6-verification.md`.

## 7. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 7.1 Commit backend changes in scoped commits referencing this change id.
- [ ] 7.2 Merge to `main` (check for conflicts) and push.
- [x] 7.3 Railway backend deploy (commit `86c99dd`) reached `SUCCESS` and responded normally (no
      extended cold-start this time). Reuses the already-`true` `SELL_MACHINE_CANONICAL` flag —
      the new endpoint was live immediately, no dark-deploy step needed.
- [x] 7.4 No frontend changes (Section 5 skipped) — noted explicitly, no sw.js bump needed.
- [x] 7.5 Live smoke test: inserted one representative `operator_tasks` row
      (`status="completed"`, `result={"impressions":1200,"clicks":45}`, explicitly labeled
      smoke-test data) via direct Supabase SQL; `GET /telemetry/report` correctly reflected it
      alongside the real `crm_leads` funnel counts; `POST /hooks/generate` (no `report` param)
      still returned a valid hook shape, confirming zero regression from the signature extension.
- [x] 7.6 Created deployment report at
      `openspec/changes/sell-machine-telemetry-loop/reports/2026-07-20-deployment.md`, noting the
      `origin/main` divergence incident (concurrent Wompi sandbox archive, resolved as a clean
      fast-forward since no actual history divergence existed) and that the smoke-test row is
      synthetic, not real Manus data.

## 8. Archive

- [x] 8.1 Sync the `sell-machine-telemetry-loop` capability into `openspec/specs/` (using `git mv`
      for the archive move, per the process fix established after Change A's tree-drift incident)
      and archive this change once Stage 11 is confirmed complete and verified live.
