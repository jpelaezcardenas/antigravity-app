# Tasks — Hermes→Manus Poller Activation

## 1. Setup + verification
- [x] 1.1 Verified live that nothing polls the bridge: zero `/sell-machine/tasks/pending` requests
      in Railway logs; `operator_tasks` row `661d395f…` (`post_content`) `pending` since 2026-07-19.
- [x] 1.2 Confirmed the Manus API v2 contract from `open.manus.ai/docs/v2` (auth header, task.create,
      task.detail, status enum) — resolves the parent change's "shape unconfirmed" non-goal.
- [x] 1.3 Confirmed `hermes-workspace/` contains only two markdown docs (no code repo), so this
      service lives in `antigravity-app` under `apps/` alongside `chatwoot-bridge`.

## 2. Manus client — TDD
- [x] 2.1 Failing tests: `create_task` posts to the right URL with the right header/body and returns
      `task_id`; `get_task` returns status; missing API key short-circuits without any HTTP call;
      non-200 and `ok:false` are handled without raising.
- [x] 2.2 Implement `manus_client.py` against the confirmed contract.
- [x] 2.3 Green.

## 3. Backend client — TDD
- [x] 3.1 Failing tests: `list_pending`, `mark_dispatched`, `report_result` hit the right paths and
      fail soft (return `None`/`False`, never raise) on network/non-200.
- [x] 3.2 Implement `backend_client.py` (JWT signing shape copied from the Chatwoot bridge, D5).
- [x] 3.3 Green.

## 4. Prompt builder + poller tick — TDD
- [x] 4.1 Failing tests for `build_manus_prompt`: each `task_type` produces a prompt; side-effecting
      types state the content is human-approved and must be published as-is; unknown type is handled.
- [x] 4.2 Failing tests for the tick: no API key → exits without claiming; a `pending` task is
      claimed and dispatched; a `dispatched` task whose Manus task is terminal gets its result
      reported; `waiting`/`running` are left in flight.
- [x] 4.3 Implement `prompts.py`, `state.py` (sidecar), `poller.py`, `main.py`.
- [x] 4.4 Green — 23/23 poller tests passing.

## 5. Local scheduling
- [x] 5.1 `run_poller.ps1` + `register_poller_task.ps1` following the proven `ContexiaChatwootBridge`
      pattern (1-minute repeating trigger, `MultipleInstances IgnoreNew`, `AtLogOn`, no stored
      password). Simpler than the bridge's: no port self-check needed (one-shot, D1).
- [x] 5.2 `README.md` with the exact install/verify commands and the founder-only steps.
- [x] 5.3 `requirements.txt` + `.env.example`.

## 6. Founder actions (BLOCKING — cannot be done by an agent)
- [ ] 6.1 Create a Manus API key: Manus webapp → Settings → API Integration → Create API Key.
      **The agent must never handle this value.**
- [ ] 6.2 Copy `.env.example` → `.env` in `apps/hermes-manus-poller/` and fill `MANUS_API_KEY`
      (and `CONTEXIA_JWT_SECRET` if the `/tasks/*` routes ever get gated).
- [ ] 6.3 Register the scheduled task:
      `powershell -ExecutionPolicy Bypass -File apps\hermes-manus-poller\register_poller_task.ps1`
- [ ] 6.4 Smoke test one tick in the foreground:
      `python apps\hermes-manus-poller\main.py --once --dry-run`

## 7. Verify end-to-end (after 6.x)
- [ ] 7.1 Confirm the long-pending `post_content` task (`661d395f…`) transitions
      `pending → dispatched` and a Manus task is created.
- [ ] 7.2 Confirm a later tick reports the result and the row reaches `completed`.
- [ ] 7.3 Confirm Railway logs now show `/sell-machine/tasks/pending` traffic.

## Stage 11. Deploy to Production
**Deliberately N/A for cloud deploys** — this service is local-only by architecture
(ARCHITECTURE.md decision #1; Manus credentials must never reach Railway). "Production" for this
change means: registered as a scheduled task on the founder's node and confirmed dispatching (7.x).
- [ ] 11.1 git commit + push to main (code only; no Railway/Vercel change expected)
- [ ] 11.2 Confirm Railway/Vercel deploys stay green (no backend/frontend files touched)
- [ ] 11.3 Report: `openspec/changes/hermes-manus-poller-activation/reports/YYYY-MM-DD-deployment.md`

## 8. Archive
- [ ] 8.1 Sync the `hermes-manus-poller` capability spec into `openspec/specs/`, archive via `git mv`.
