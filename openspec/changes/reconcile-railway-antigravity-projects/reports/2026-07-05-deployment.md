# Deployment Report — reconcile-railway-antigravity-projects

**Date:** 2026-07-05
**Deploy branch:** main
**Commit:** `02c9e50`
**Backend URL:** https://antigravity-app-production-175a.up.railway.app
**Deployment ID:** `4a597f5f-4f7f-4890-8722-27070cf04bd6` — SUCCESS

## What shipped

1. **Confirmed `-175a` (`elegant-success`) as the sole live-traffic backend** via `vercel.json`'s `/api/v1/*` rewrite target — ground truth, not assumption.
2. **Migrated 7 genuinely-used environment variables** from the undocumented duplicate deployment `-dc78` (`enthusiastic-youthfulness`) to `-175a`: `JWT_SECRET`, `JWT_ALGORITHM`, `SUPABASE_JWT_SECRET`, `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `CEREBRAS_API_KEY`, `TELEGRAM_BOT_TOKEN`. Verified confirmed absent: the Bitwarden master-password-based secrets (`BW_MASTER_PASSWORD`/`BW_CLIENT_ID`/`BW_CLIENT_SECRET`/`SECRETS_BACKEND`/`BW_VAULT_URL`) — deliberately not replicated (separately tracked security issue, `task_d1ec7639`).
3. **Fixed a live production security gap discovered during investigation**: `apps/backend/config.py`'s `validate_production_config()` was defined but never called anywhere in the codebase. `-175a` was running with `DEBUG=False`, `ENVIRONMENT=production`, and an **empty `JWT_SECRET`** — used for real tenant-resolution JWT signing/verification in `core/tenant_middleware.py`. Wired the validation into `main.py`'s startup sequence; verified it now fails loudly on a deliberately-broken config and passes cleanly on the real one.
4. **Updated `ARCHITECTURE.md`** ("Decisiones asentadas" #9): documents `-175a` as sole canonical backend, `-dc78` as existing-but-non-canonical, pending a separate explicit decommission decision.

## Verification performed

- Health check: 200, `{"status":"healthy","service":"Contexia API"}` — 5/5 consecutive checks after one transient proxy-layer blip at container cutover (confirmed via deployment logs: no crash, no traceback — a Railway edge blip, not an app issue).
- Deployment logs: clean startup, no `ValueError` from the newly-wired validation (proving it passed with the real, now-complete config).
- Exercised `/api/v1/approval-queue` (routes through `TenantContextMiddleware`, the real JWT-dependent code path): got a clean, structured JSON error (`{"detail": "'pending' is not a valid ApprovalStatus"}`) — a **pre-existing, unrelated bug** (default status parameter mismatch, out of scope for this change), but its clean structured response proves the full chain (routing → tenant middleware → JWT verification → handler → error serialization) executes correctly under the new real `JWT_SECRET`.

## Explicitly NOT done (by design)

- **`-dc78` was not decommissioned.** Per this change's non-goals, decommissioning requires a separate, explicit founder decision after this verification — not an automatic consequence of closing this change. `-dc78` remains running, unchanged.
- **Telegram webhook was not registered.** `getWebhookInfo` confirmed no webhook is currently active on either project; re-enabling Taty's Telegram bot is a separate decision, not required to close this change.
- **Bitwarden Secrets Manager migration** remains a separate tracked follow-up (`task_d1ec7639`) — out of scope here.

## Rollback plan

All changes are additive: new env vars on `-175a` (no existing ones modified/removed) plus one new function call in `main.py`. Revert is a single commit reverting the `validate_production_config()` call if it ever unexpectedly blocks a valid future deploy; the env vars can simply be left in place (harmless if unused) or removed via Railway without any code change.

## Status: COMPLETE

All tasks in `tasks.md` groups 1-6 and Stage 11 (11.1-11.4, this report being 11.4) are done. Ready to archive.
