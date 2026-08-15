# Design — Hermes→Manus Poller Activation

## Context

The cloud half of the bridge exists and is deployed (`SELL_MACHINE_CANONICAL=true`). What is
missing is a local process that actually calls those endpoints. Verified 2026-08-12: zero requests
to `/sell-machine/tasks/pending` in Railway logs; task `661d395f…` (`post_content`) has been
`pending` since 2026-07-19.

## Confirmed external contract (Manus API v2)

Fetched from `https://open.manus.ai/docs/v2/*` on 2026-08-12. This resolves the parent change's
"shape unconfirmed" non-goal.

| Concern | Value |
|---|---|
| Base URL | `https://api.manus.ai` |
| Auth header | `x-manus-api-key: <key>` (alternative: `Authorization: Bearer` for OAuth2 — not used here) |
| Create | `POST /v2/task.create`, body `{"message": {"content": "<prompt>"}, "title": "...", "agent_profile": "manus-1.6"}` |
| Create response | `{"ok": true, "task_id": "...", "task_url": "...", "request_id": "..."}` |
| Poll | `GET /v2/task.detail?task_id=<id>` |
| Poll response | `{"ok": true, "task": {"id", "status", "credit_usage", "task_url", ...}}` |
| Status values | `running` \| `stopped` \| `waiting` \| `error` |

**Status mapping decision.** Manus's `stopped` means "finished or halted" — it is not distinguishable
from success at the API level. We therefore map `stopped → completed` and `error → failed`, and
carry `task_url` + `credit_usage` into the result payload so a human can audit what actually
happened. `waiting` means Manus is asking for input; we treat it as still-in-flight (not terminal)
and surface it in logs, because auto-answering a Manus prompt would be an unapproved action.

## Decisions

### D1 — One-shot per tick, not a long-running daemon
The Chatwoot bridge is a daemon because it serves HTTP. This poller has no inbound surface; it is a
loop with a 1-minute cadence. Running one-shot removes the entire liveness problem: no PID file, no
port probe, no restart policy, no memory growth. Task Scheduler's `MultipleInstances IgnoreNew`
prevents overlap if a tick runs long. A crashed tick costs one minute.

### D2 — Two-phase dispatch, state in the database
Tick N claims a `pending` task (`→ dispatched`) and creates the Manus task. Tick N+k polls
`task.detail` for tasks already `dispatched` and, if terminal, posts the result (`→ completed` /
`failed`). Nothing is held in poller memory, so the poller is freely restartable.

**Where the Manus task id lives:** the backend's `mark_dispatched` takes no payload, and modifying
the backend is out of scope. The poller therefore keeps a small local sidecar file
(`state/dispatched.json`) mapping `operator_task_id → manus_task_id`. This is acceptable because
losing it is recoverable and non-destructive: the affected task stays `dispatched` and is reported
via `list_orphans()` for manual resolution, rather than being silently re-dispatched (which would
double-post to Meta). Documented as the main known limitation; a future backend change could add a
`external_task_id` column and retire the sidecar.

### D3 — Fail-closed on missing credentials
`MANUS_API_KEY` defaults to `""`. With it unset the poller logs one line and exits **before**
claiming any task. This means the scheduled task can be registered now and stays inert until the
founder adds the key — no half-claimed tasks, matching the `send_whatsapp_message` precedent in
`channels/whatsapp.py`.

### D4 — Task-type → prompt is a pure, testable function
`build_manus_prompt(task)` turns an `operator_tasks` row into the Manus `message.content` string.
Kept pure (no I/O) so every `task_type` is unit-testable without network. Side-effecting types
(`post_content`, `run_ads_ab`) get an explicit instruction that the content is **already approved by
a human** and must be published as-is — Manus must not re-invent the copy that the Approval Queue
already gated.

### D5 — Backend auth reuses the Chatwoot bridge's JWT pattern
`sign_tenant_jwt()` (HS256, `CONTEXIA_JWT_SECRET`, `sub`/`tenant_id`/`exp`) is copied in shape from
`apps/chatwoot-bridge/backend_client.py` rather than imported, because the two services deploy
independently and a shared import would couple their release cycles. The duplication is ~15 lines
and is called out here so it is a known, deliberate copy, not drift.

Note: the `/tasks/*` endpoints are currently **unauthenticated** by design (parent change: Hermes
has no browser session). The poller sends the JWT anyway so that a future decision to gate those
routes does not require changing the poller.

### D6 — No new bypass of HITL
The poller reads `operator_tasks` only. `post_content`/`run_ads_ab` rows can only be created by
`dispatch_campaign_package`, which refuses anything whose `campaign_package` is not `approved`. The
poller therefore cannot publish anything the founder has not approved, and it never writes to
`approval_queue`.

## Risks

| Risk | Mitigation |
|---|---|
| Sidecar file lost → orphaned `dispatched` task | Never auto-re-dispatch; report via `list_orphans()` for manual handling (D2) |
| Manus `stopped` conflates success/abort | Store `task_url` + `credit_usage` in the result so a human can audit; documented in D0 mapping |
| Poller runs while founder is logged out | Accepted — same sovereign-local-node model as the Chatwoot bridge (`AtLogOn` trigger, no stored Windows password) |
| Double-dispatch if two ticks overlap | `MultipleInstances IgnoreNew` + `mark_dispatched` rejects a task that is not `pending` (backend already enforces this) |
