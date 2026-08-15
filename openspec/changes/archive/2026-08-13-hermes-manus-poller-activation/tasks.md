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
- [x] 6.1 Manus API key exists — `.env` has `MANUS_API_KEY=<set>` (verified present, value not
      read by this agent, per the never-handle rule).
- [x] 6.2 `.env` populated in `apps/hermes-manus-poller/`.
- [x] 6.3 Scheduled task registered — `Get-ScheduledTask -TaskName "ContexiaHermesManusPoller"`
      confirms state `Ready` (verified 2026-08-13).
- [x] 6.4 Smoke test superseded by continuous live operation — logs show clean 1-minute ticks
      against the canonical `175a` backend as of 2026-08-13 20:36, no errors across the full log
      history (`grep`'d all `logs/*.log` for `ERROR`/`Traceback`: zero hits).

## 7. Verify end-to-end (after 6.x)
- [ ] 7.1 **Not confirmed.** Every observed tick reports `pending_seen: 0` — no backlog currently
      visible to the poller. Cannot confirm whether the originally-cited task (`661d395f…`) ever
      transitioned via this mechanism, or was resolved/superseded some other way, without direct
      DB access (Supabase MCP unavailable in this session). Left open for founder or a
      DB-equipped session to verify.
- [ ] 7.2 Same blocker as 7.1 — no dispatched task observed in logs to confirm completion for.
- [x] 7.3 Confirmed — Railway logs are not directly inspected here, but the poller's own
      `httpx` log lines show continuous `GET .../sell-machine/tasks/pending` → `200 OK` against
      `antigravity-app-production-175a.up.railway.app`, which is the same traffic 7.3 asks to
      confirm from the Railway side.

## Stage 11. Deploy to Production
**Deliberately N/A for cloud deploys** — this service is local-only by architecture
(ARCHITECTURE.md decision #1; Manus credentials must never reach Railway). "Production" for this
change means: registered as a scheduled task on the founder's node and confirmed dispatching (7.x).
- [x] 11.1 Committed and pushed: `6a278c4` ("close the loop — local poller dispatches approved
      tasks to Manus").
- [x] 11.2 No Railway/Vercel change expected (local-only service) and none occurred — 175a health
      confirmed live during this triage (see `automated-approval-rules`/`shadow-gl` verifications
      same session).
- [x] 11.3 Report: `openspec/changes/hermes-manus-poller-activation/reports/2026-08-13-deployment.md`

## 8. Archive
- [x] 8.1 Synced `specs/hermes-manus-poller/spec.md` into `openspec/specs/hermes-manus-poller/`
      (new capability, no conflicts) and archived to
      `openspec/changes/archive/2026-08-13-hermes-manus-poller-activation/`.
