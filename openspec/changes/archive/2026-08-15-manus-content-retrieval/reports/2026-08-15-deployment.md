# Stage 11 Deployment Report (Local Service) — manus-content-retrieval

- Date: 2026-08-15
- Change: manus-content-retrieval
- Agent: Claude Code (Sonnet)
- Deploy branch: `main`
- Service: `apps/hermes-manus-poller/` — **local-only**, Windows Scheduled Task
  (`ContexiaHermesManusPoller`), never Railway/Vercel (`ARCHITECTURE.md` decision #1)

## 11.1 — Commit + Merge + Push

- Committed on `feature/manus-content-retrieval` (`5d04e5f`)
- Fast-forward merged into `main` (`39dd671..5d04e5f`)
- Pushed to `origin/main`: `39dd671..5d04e5f main -> main`
- This push touches only `apps/hermes-manus-poller/` and `openspec/` — no Railway rebuild
  triggered, correctly, since `apps/backend/` is untouched.

## 11.2 — Founder Action Required (PENDING)

The local checkout running the Scheduled Task needs `git pull` to receive this commit. The agent
cannot perform this — it has no access to the founder's local machine/process. **No service
restart needed**: each tick invokes `python main.py` fresh (design.md D1, one-shot-per-tick), so
the very next scheduled tick after the pull picks up the new code automatically.

Command for the founder to run on that machine:
```
cd path\to\antigravity-app
git pull origin main
```

## 11.3 — Verification

Deferred to the live end-to-end test already agreed this session: dispatching a real `research`
task with a `creative_brief` payload through the now-updated poller is itself the verification
this change exists to enable — a separate synthetic check here would duplicate that effort.
**Blocked on 11.2** (the founder's local pull) before that live test can exercise the new code path.

## 11.4 — This Report

Created at `openspec/changes/manus-content-retrieval/reports/2026-08-15-deployment.md`.

## Outcome

Stage 11 (local-service variant) status: **commit/push complete, founder action 11.2 pending**.
Do not archive this change until 11.2 is confirmed done (or explicitly accepted as done-enough by
the founder) and the live test in 11.3 has run at least once.
