# Stage 11 Deployment Report — taty-per-tenant-profiles

- Date: 2026-07-23
- Deploy branch: main
- Backend: Railway `elegant-success` / `antigravity-app-production-175a`

## What shipped

Merged `feature/taty-per-tenant-profiles` (12 commits, tasks 1-10) directly to `main` via
`git push origin feature/taty-per-tenant-profiles:main` (fast-forward, `630b78b..18fd7a1`) —
no push classifier block encountered. Rebased onto `origin/main` first to pick up
`hermes-task-queue-tenant-scoping`'s merge (unrelated files, only `feature_list.json` and
`progress/history.md` conflicted — both append-only, trivially resolved) and to correct a
stale claim: `chatwoot-hermes-taty-bridge` was marked `done` in this change's task 0.3, but
`origin/main`'s `feature_list.json` (updated by its owning session) showed it as `blocked`
(Task Groups 1-14 done except 14.3/14.4 — Docker/WhatsApp number pending — not archived).
Corrected during the rebase.

A sibling session (`approval-queue-tenant-scoping`) merged 3 more commits to `main` shortly
after (`18fd7a1..427c828`), including one that fixes the pre-existing
`test_shadow_gl_stage8_e2e.py` self-recursion bug this change's task 2/7 reviewers had
flagged as unrelated. Railway auto-deployed `427c828` (deployment `5cac29b7`, SUCCESS).

## Production verification

Ran against the live `427c828` deployment (health-polled until 200 after the restart window):

| Check | Result |
|---|---|
| `POST /api/v1/agents/taty/ask` (deleted route) | **404** `{"detail":"Not Found"}` ✓ |
| `GET /api/v1/agents/ask` unauthenticated (`AUTH_ENFORCED=true` in prod) | **401** `{"detail":"Invalid or missing authentication token"}` ✓ |
| `GET /api/v1/health` | **200** `{"status":"healthy",...}` ✓ |
| Railway deployment logs (both the deploy that briefly went live and the prior one, ~4h of traffic) checked for any pre-existing `/agents/ask` caller relying on the old unauthenticated behavior | **None found** — only same-session smoke-test traffic hitting unrelated/mismatched paths (404s on old-style paths, 422s on `orchestrator/full-pipeline`). No real end-user or external consumer traffic against `/agents/ask` observed. |

**11.6 / 11.6b / 11.8 — NOT executed by this session.** They require:
- 11.6: a real Supabase-issued session JWT for a provisioned B2B client (founder's Bitwarden
  credentials — this agent does not have and should not be given plaintext credentials per
  its operating constraints).
- 11.6b: a real authenticated session with no active `user_tenants` membership (same
  constraint).
- 11.8: sending a live Telegram message to Cliente Cero's configured chat (requires access to
  that Telegram account/bot).

Deferred honestly rather than fabricated — matches the precedent already established by
tasks 1/6/7/8 for the same "no live credentials in this environment" limitation. **Founder
action needed** to close these three before archiving (see tasks.md 11.6/11.6b/11.8).

## Risk assessment (per design.md)

- Risk #2 (unknown external consumer of `/agents/ask`) — checked, clear. No traffic pattern
  suggesting a real caller depended on the pre-auth behavior.
- Risk #3 (stale demo `telegram_chat_mappings` rows) — checked in task 7, clear.
- No DB migration in this change (per design D1) — nothing to roll back beyond the code diff.

## Outcome

Code is live in production and behaving correctly for every check this session could run
without founder-held credentials. Auth flip verified safe. Three founder-dependent checks
remain before this change can be archived.
