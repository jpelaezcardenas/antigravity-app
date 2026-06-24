# Task 6.3 Resolution — Dirección Confirmation

**Date:** 2026-06-24
**Status:** ✅ Resolved

## Question 1: Entidad A email for approval testing

**Answer (Juan David, 2026-06-24):** `jpelaezcardenas@gmail.com`

Use this as the `approved_by` value in `approval_queue` for Phase 4 testing traceability. No
schema/code change needed — this is a config/data value, not a code path.

## Question 2: Telegram bot token availability in Railway

**Investigated directly via Railway MCP (2026-06-24) instead of asking blind.**

Discovered two separate Railway projects, each running a service named `antigravity-app`:

| Project | Service domain | Has `TELEGRAM_BOT_TOKEN`? |
|---|---|---|
| `elegant-success` (`27f4a1b4-1e46-4ad7-b08e-15e92817ffdd`) | `antigravity-app-production-175a.up.railway.app` | ❌ No |
| `enthusiastic-youthfulness` (`ce9b9383-5bac-4367-99bf-7c4d1bf3fb58`) | `antigravity-app-production-dc78.up.railway.app` | ✅ Yes |

The repo's `CLAUDE.md` documents `175a` as the canonical production backend — which is the one
**without** the token. `dc78` has the token but isn't the documented production URL.

**Decision (Juan David, 2026-06-24):** Don't block Phase 4 archive on reconciling this. Both
projects stay active for now. Tracked as a separate technical-debt item (see `tasks.md` 6.3
follow-up note) — not Phase 4 scope.

**Practical implication:** The Taty Telegram webhook (`/api/v1/agents/taty/telegram-webhook`)
will only respond to real Telegram traffic if it's actually running on `dc78`. If production
traffic is routed to `175a`, the webhook is configured but the bot token is missing — Stage 11
verification for Slice 4's Telegram path should be considered **unverified in the canonical
production project** until the Railway reconciliation follow-up is done.

## Outcome

Task 6.3 is closed for Phase 4 purposes. Task 6.4 (archive readiness) can proceed.
