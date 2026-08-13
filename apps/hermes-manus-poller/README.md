# Hermes → Manus operator-task poller

Closes the last gap in the Sell Machine loop. The backend has been queuing approved campaign work
in `operator_tasks` since 2026-07-19, but nothing ever picked it up — this service is the missing
consumer.

```
Approval Queue (you approve in the Búnker)
      ↓
operator_tasks  [Railway]  ← the backend half, already built
      ↓  GET /tasks/pending          ← THIS SERVICE (local, one-shot every minute)
      ↓  POST /v2/task.create        → Manus executes (posts to Meta/FB/IG, runs A/B, research…)
      ↓  GET  /v2/task.detail        ← polls until terminal
      ↓  POST /tasks/{id}/result     → result lands back in operator_tasks
      ↓
telemetry feeds the next creative sprint
```

**Local only, by architecture.** Manus/Meta credentials never reach Railway
(`ARCHITECTURE.md` decision #1). Do not deploy this to Railway or Vercel.

## Install (founder, one time)

```powershell
cd C:\Users\contexia\Projects\antigravity-app\apps\hermes-manus-poller
C:\Users\contexia\AppData\Local\Programs\Python\Python311\python.exe -m pip install -r requirements.txt
```

Then create your Manus API key — **Manus webapp → Settings → API Integration → Create API Key**.
It is shown only once. Copy `.env.example` to `.env` and paste it into `MANUS_API_KEY`.

```powershell
copy .env.example .env
notepad .env
```

## Verify before scheduling

Dry run — reads real pending tasks, changes nothing, calls nothing:

```powershell
C:\Users\contexia\AppData\Local\Programs\Python\Python311\python.exe main.py --dry-run
```

You should see the long-pending `post_content` task logged as "would dispatch". Then one real tick:

```powershell
C:\Users\contexia\AppData\Local\Programs\Python\Python311\python.exe main.py
```

## Schedule it

```powershell
powershell -ExecutionPolicy Bypass -File .\register_poller_task.ps1
Start-ScheduledTask -TaskName "ContexiaHermesManusPoller"
```

Check it:

```powershell
Get-ScheduledTask -TaskName "ContexiaHermesManusPoller" | Get-ScheduledTaskInfo
Get-Content .\logs\poller-*.log -Tail 40
```

## How it behaves

| Situation | Behavior |
|---|---|
| `MANUS_API_KEY` unset | Logs one error and exits **without claiming anything**. Safe to schedule before you have the key. |
| Backend refuses the claim | No Manus task is created — prevents double-posting. |
| Claimed but `task.create` failed | Left as `dispatched` with no local mapping; reported as an orphan. **Never auto-retried** (a retry would double-post). |
| Manus `running` / `waiting` | Left in flight; retried next tick. `waiting` is never auto-answered. |
| Manus `stopped` | Reported as `completed`, carrying `task_url` + `credit_usage` so you can audit what actually happened. |
| Manus `error` | Reported as `failed`. |
| A tick crashes | Costs one minute. Next tick picks up from the database. |

## Files

| File | Role |
|---|---|
| `main.py` | Entry point (`--dry-run`, `--once`) |
| `poller.py` | The tick: resolve dispatched, then dispatch pending |
| `manus_client.py` | Manus API v2 (`task.create`, `task.detail`) |
| `backend_client.py` | Contexia `/sell-machine/tasks/*` |
| `prompts.py` | `operator_tasks` row → Manus prompt (pure, testable) |
| `state.py` | Sidecar `operator_task_id → manus_task_id` |

## Known limitation

The `operator_task_id → manus_task_id` mapping lives in `state/dispatched.json`, not the database,
because the backend's `mark_dispatched` accepts no payload and changing it was out of scope. If
that file is lost, affected tasks stay `dispatched` and are reported as orphans for manual
resolution — deliberately not re-dispatched. A future backend change could add an
`external_task_id` column and retire the sidecar. See `design.md` D2.

## Tests

```powershell
C:\Users\contexia\AppData\Local\Programs\Python\Python311\python.exe -m pytest tests\ -q
```

No credentials or network needed — everything is mocked.
