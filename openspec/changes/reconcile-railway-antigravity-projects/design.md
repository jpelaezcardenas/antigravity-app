## Context

Two Railway projects (`elegant-success`/`-175a`, `enthusiastic-youthfulness`/`-dc78`) run duplicate `antigravity-app` services against the same Supabase DB. This has been known technical debt since the archived `agentic-performance-management-phase4` change (2026-06-24), with an explicit founder decision to keep both alive and a follow-up that never became a real change. Investigation for this change established ground truth rather than relying on the original assumption:

- **Vercel's `/api/v1/*` rewrite points at `-175a`** — this is the actual live-traffic backend, confirmed by reading `vercel.json` directly, not inferred.
- **No Telegram webhook is currently registered on either project** (`getWebhookInfo` on the real bot token → `"url":""`). The originally-assumed "active risk" (breaking a live webhook) isn't currently manifesting. The Telegram integration is webhook-based by design (`apps/backend/presentation/telegram_endpoints.py`, a `POST /webhook` handler — no polling code found), so if it's ever re-enabled, it must be registered against whichever project holds `TELEGRAM_BOT_TOKEN` and can serve the endpoint — currently only `-dc78` has the token.
- **A full env var diff (both projects, re-fetched fresh for this change) found more than the known `TELEGRAM_BOT_TOKEN` gap**: `-dc78`-only vars are `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `CEREBRAS_API_KEY`, `JWT_SECRET`, `JWT_ALGORITHM`, `SUPABASE_JWT_SECRET`, plus the already-separately-tracked Bitwarden secrets (`BW_MASTER_PASSWORD`/`BW_CLIENT_ID`/`BW_CLIENT_SECRET`/`SECRETS_BACKEND`/`BW_VAULT_URL`) and cosmetic ones (`PORT`, `NIXPACKS_IGNORE_DOCKERFILE`).
- **`GEMINI_API_KEY`/`MISTRAL_API_KEY`/`CEREBRAS_API_KEY` are genuinely used** (`apps/backend/agents/llm_engine.py`, part of Contexia's documented LLM fallback cascade) — `-175a` is missing three of its five documented fallback providers.
- **`SUPABASE_KEY` differs by role, not just value**: `-175a` uses a service_role JWT; `-dc78` uses an anon-role JWT. This is a privilege divergence, not a missing-variable gap.
- **Critical, unplanned finding**: `apps/backend/config.py` defines `validate_production_config()` — a safety check that raises if `JWT_SECRET` is empty/weak in production — but it is **never called anywhere** in the codebase (confirmed via full-repo grep). `-175a` runs with `DEBUG=False`, `ENVIRONMENT=production`, and an **empty `JWT_SECRET`**. `apps/backend/core/security.py` uses `settings.JWT_SECRET` directly for `jwt.encode`/`jwt.decode` (HS256), and this is real, load-bearing auth code — used by `core/tenant_middleware.py` for tenant resolution (confirmed via grep: `auth_service.py`, `core/deps.py`, `tenant_middleware.py`, plus their tests, all import `core.security`). An empty HMAC secret means any custom JWT this backend issues/verifies is forgeable. This is live on the actual production backend right now, discovered as a side effect of investigating the Railway duplication, not something this change set out to find.

## Goals / Non-Goals

**Goals:**
- Make `-175a` the fully documented, fully functional canonical backend — migrating every genuinely-needed `-dc78`-only variable to it (excluding Bitwarden secrets, which stay out per the separate tracked remediation).
- Fix the empty-`JWT_SECRET`-in-production gap on `-175a` as part of this change (it's directly tied to the env var migration already in scope, and the severity doesn't warrant waiting for a separate change cycle).
- Wire `validate_production_config()` into actual application startup so this class of misconfiguration can't recur silently.
- Verify Telegram bot functionality and general health end-to-end on `-175a` before any decommission decision.

**Non-Goals:**
- Decommissioning `-dc78` — gated behind verification passing, and even then requires a separate explicit founder go-ahead, not an automatic step of this change.
- Fixing the Bitwarden master-password exposure on `-dc78` — tracked separately (`task_d1ec7639`).
- Re-enabling the Telegram webhook itself (registering it with Telegram) — a meaningful production action in its own right, only done if/when the founder wants Taty's Telegram bot live, not a required step to close this change.
- Auditing `-175a`/`-dc78` for every possible configuration divergence beyond what's needed for the reconciliation — scoped to variables confirmed used by real code paths.

## Decisions

**1. Migrate genuinely-used `-dc78`-only variables to `-175a`; explicitly exclude Bitwarden secrets.**
Alternative considered: copy every `-dc78`-only variable wholesale for completeness. Rejected — copying `BW_MASTER_PASSWORD`/`BW_CLIENT_ID`/`BW_CLIENT_SECRET` would spread the exact insecure pattern already flagged separately, onto a second project. Only variables confirmed referenced by real code (`GEMINI_API_KEY`, `MISTRAL_API_KEY`, `CEREBRAS_API_KEY`, `JWT_SECRET`, `JWT_ALGORITHM`, `SUPABASE_JWT_SECRET`, `TELEGRAM_BOT_TOKEN`) get migrated. `PORT`/`NIXPACKS_IGNORE_DOCKERFILE` are Railway/build-environment specific, not needed on `-175a` (it already boots successfully with its own settings).

**2. Fix the JWT_SECRET gap now, as part of this change, not a separate one.**
Alternative considered: flag it as yet another separate follow-up task (matching the pattern used for the Bitwarden and skill-conformance findings this session). Rejected — this one is small, directly caused by the exact migration already in scope (dc78 already has a strong, working `JWT_SECRET`; migrating it *is* the fix), and it's a live production auth weakness, not a someday-cleanup item. Wiring `validate_production_config()` into startup is the preventive complement — small, same file, same change.

**3. `SUPABASE_KEY` role divergence is investigated, not blindly reconciled.**
`-175a` uses service_role (elevated); `-dc78` uses anon (restricted). Rather than assume one is "wrong," this change's tasks verify what `-175a`'s actual code paths require (it's already running successfully with service_role, so no change needed there) and note the divergence in the design record — `-dc78` running on anon-role privileges may itself explain some of its more limited historical behavior, relevant context if `-dc78` is ever restored to active use before a decommission decision.

## Risks / Trade-offs

- **[Risk]** Migrating `JWT_SECRET` to `-175a` while it's live could invalidate any currently-issued tokens signed under the old (empty) secret → **[Mitigation]** Given the secret was empty, no legitimately-issued token depended on a *real* secret anyway; this is a strict improvement, not a breaking change to any working flow. Verify via health check + a real authenticated request post-deploy.
- **[Risk]** Wiring `validate_production_config()` into startup could reveal *other* latent misconfigurations and fail the deploy → **[Mitigation]** Run it first in a way that logs rather than crashes (or verify all required fields are actually set before flipping it to raise), so this change doesn't itself cause new downtime.
- **[Risk]** `-dc78` may still be genuinely needed for something not yet identified → **[Mitigation]** Explicit non-goal: do not decommission as part of this change regardless of how clean the migration looks.

## Migration Plan

1. Add the confirmed-needed variables to `-175a`: `TELEGRAM_BOT_TOKEN`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `CEREBRAS_API_KEY`, `JWT_SECRET`, `JWT_ALGORITHM`, `SUPABASE_JWT_SECRET` (reuse `-dc78`'s existing values — they're real, working secrets, not placeholders).
2. Wire `validate_production_config()` into `apps/backend/main.py` (or wherever the app factory/startup sequence lives) so it actually runs.
3. Deploy `-175a`, verify health check + a real authenticated request path exercises the tenant-resolution JWT code without error.
4. Update `ARCHITECTURE.md`/`CLAUDE.md` to state `-175a` is the sole documented canonical backend (already true in practice; this makes the docs match reality).
5. Stage 11 per this repo's mandatory deployment standard.
6. `-dc78` decommission is explicitly **not** part of this change's task list — a follow-up decision after this closes.

**Rollback:** all changes are additive env vars on `-175a` plus a startup validation call; if `validate_production_config()` unexpectedly blocks a valid deploy, it can be reverted in one commit without touching `-dc78` or any data.

## Open Questions

- Does `-175a` need `SUPABASE_JWT_SECRET` specifically, or is it dead configuration left over from an earlier auth approach (Supabase's own JWT verification vs. the custom `core/security.py` HS256 tokens)? Migrate it regardless (harmless if unused, matches `-dc78`'s working config) but worth a code-owner follow-up look, not blocking this change.
