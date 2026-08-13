# Hermes→Manus Poller Activation

## Why

`hermes-manus-execution-bridge` (archived 2026-07-19) built the **cloud half** of the bridge:
`operator_tasks` plus `GET /api/v1/sell-machine/tasks/pending`,
`POST /tasks/{id}/status`, `POST /tasks/{id}/result`. It explicitly left the **local half** out of
scope: *"Building the Hermes-side Manus API client or any Manus/Meta credential handling — that
lives in the separate `hermes-workspace` repo"*, and noted *"Exact Manus API request/response shape
is still unconfirmed."*

Verified live 2026-08-12: **nothing polls those endpoints.** Railway request logs show zero hits on
`/sell-machine/tasks/pending`, and a `post_content` task created 2026-07-19 is still `pending` —
unclaimed for weeks. Every approved campaign package therefore dies in `operator_tasks`; Manus never
receives it. This is the single blocker preventing the Renta Natural 2026 campaign from running
autonomously.

Two things changed that make this buildable now:
1. **The Manus API contract is confirmed** (fetched from `open.manus.ai/docs/v2`, 2026-08-12):
   base `https://api.manus.ai`, header `x-manus-api-key`, `POST /v2/task.create`
   (`{"message":{"content":...}}` → `task_id`), `GET /v2/task.detail?task_id=` → `task.status` ∈
   `running|stopped|waiting|error`. The "unconfirmed shape" non-goal is resolved.
2. **`hermes-workspace/` holds only two markdown docs** — there is no code repo there to put this
   in. Waiting on a separate repo that does not exist is what left this unbuilt.

## What Changes

A new local-only service `apps/hermes-manus-poller/` that closes the loop:

- **One-shot per tick, not a daemon.** Each run claims and dispatches, then exits. Windows Task
  Scheduler fires it every minute (same watchdog pattern as `ContexiaChatwootBridge`, reusing its
  proven `MultipleInstances IgnoreNew` + repeating-trigger approach). No PID file, no port check,
  no crash-recovery logic needed — a crashed tick is simply retried next minute.
- **Backend client**: pulls `pending` tasks, marks `dispatched`, posts `result`.
- **Manus client**: real v2 API (`task.create` / `task.detail`) against the confirmed contract.
- **Two-phase per task**: dispatch creates the Manus task and records its id; a later tick polls
  `task.detail` and reports the terminal result back. This survives restarts because state lives in
  `operator_tasks`, never in the poller.
- **Fail-closed on credentials**: with `MANUS_API_KEY` unset the poller logs and exits without
  claiming anything — it can be installed and scheduled before the founder adds the key.

## Impact

- **Specs:** NEW `hermes-manus-poller`. Consumes the existing, unmodified
  `hermes-manus-execution-bridge` endpoints — zero backend changes.
- **Code:** new `apps/hermes-manus-poller/` only. No change to `apps/backend/`, `contexia-app/`,
  or `apps/chatwoot-bridge/`.
- **Runs:** local laptop/WSL node only (ARCHITECTURE.md decision #1 — Manus/Meta credentials never
  reach Railway). Deliberately NOT deployed to Railway or Vercel.
- **HITL preserved:** the poller only ever sees tasks that already exist in `operator_tasks`, and
  side-effecting types (`post_content`, `run_ads_ab`) can only get there via
  `dispatch_campaign_package` from an already-approved `campaign_package`. The poller adds no new
  path that bypasses the Approval Queue.
- **Non-goals:** Meta/Facebook credential handling (Manus owns that); retry/backoff for tasks stuck
  in `dispatched` (carried over from the parent change); webhook-based completion (polling first —
  Manus supports webhooks, but that needs a public callback URL, which is the still-open named
  Cloudflare tunnel).
