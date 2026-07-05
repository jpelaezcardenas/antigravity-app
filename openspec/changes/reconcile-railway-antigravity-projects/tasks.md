## 1. Ground-Truth Investigation (done during proposal/design)

- [x] 1.1 Confirm which project receives real traffic via `vercel.json`'s API rewrite target (found: `-175a`)
- [x] 1.2 Query Telegram's `getWebhookInfo` directly to establish actual current webhook state (found: no webhook registered on either project)
- [x] 1.3 Full env var diff between both Railway services, re-fetched fresh (found: 7 genuinely-used variables missing from `-175a` beyond the known `TELEGRAM_BOT_TOKEN`)
- [x] 1.4 Grep the codebase to confirm which diffed variables are actually referenced (found: `GEMINI_API_KEY`/`MISTRAL_API_KEY`/`CEREBRAS_API_KEY` in `llm_engine.py`; `JWT_SECRET`/`JWT_ALGORITHM`/`SUPABASE_JWT_SECRET` in `core/security.py`)
- [x] 1.5 Investigate the `SUPABASE_KEY` role divergence (service_role vs anon) — documented in design.md, not blindly reconciled
- [x] 1.6 **Unplanned but critical finding, investigated fully**: confirmed `validate_production_config()` is defined in `config.py` but never called anywhere (full-repo grep), and that `-175a` is currently running production with an empty `JWT_SECRET` used for real tenant-resolution JWT signing (`core/tenant_middleware.py` chain)

## 2. Migrate Genuinely-Needed Variables to `-175a`

- [x] 2.1 Add `JWT_SECRET` (reuse `-dc78`'s real, working value) to `-175a` — highest priority, closes a live production auth weakness
- [x] 2.2 Add `JWT_ALGORITHM`, `SUPABASE_JWT_SECRET` to `-175a` (same source)
- [x] 2.3 Add `GEMINI_API_KEY`, `MISTRAL_API_KEY`, `CEREBRAS_API_KEY` to `-175a` — restores the full documented LLM fallback cascade
- [x] 2.4 Add `TELEGRAM_BOT_TOKEN` to `-175a` — needed before Telegram bot could ever be re-enabled correctly
- [x] 2.5 Explicitly do NOT add `BW_MASTER_PASSWORD`, `BW_CLIENT_ID`, `BW_CLIENT_SECRET`, `SECRETS_BACKEND`, `BW_VAULT_URL` — verify they remain absent from `-175a` after this task group

## 3. Wire the Dead Validation Into Real Startup

- [x] 3.1 Read `apps/backend/main.py` (or the actual app-factory/startup entrypoint) to find where to call `validate_production_config()`
- [x] 3.2 Call it during startup, gated so it fails loudly (not silently) when production config is invalid
- [x] 3.3 Verify locally/in a non-prod context that a deliberately-broken config (empty `JWT_SECRET`) actually fails startup with the expected error, proving the check now has teeth
- [x] 3.4 Verify `-175a`'s real config (post task group 2) passes the check cleanly

## 4. Deploy and Verify `-175a`

- [ ] 4.1 Deploy `-175a` with the new variables + wired validation
- [ ] 4.2 Confirm health check passes post-deploy
- [ ] 4.3 Exercise a real authenticated request path that depends on tenant-resolution JWT verification (`core/tenant_middleware.py`) and confirm it works correctly under the new, real `JWT_SECRET`
- [ ] 4.4 Confirm no regression: existing Groq/OpenRouter/GLM-based LLM routing still works, and the newly-added Gemini/Mistral/Cerebras fallback paths are reachable if invoked

## 5. Documentation

- [x] 5.1 Update `ARCHITECTURE.md`: state `-175a` (`elegant-success`) as the sole documented canonical backend; note `-dc78` (`enthusiastic-youthfulness`)'s status explicitly (still running, pending a separate decommission decision, not currently documented as production)
- [x] 5.2 Checked `CLAUDE.md`'s Railway references — already only mention `-175a` (never `-dc78`), nothing incorrect to fix; no change needed
- [x] 5.3 Add a "Decisiones asentadas" entry recording this reconciliation and the explicit non-decommission of `-dc78` as part of this change

## 6. Verification Gate (required before any future decommission decision — not this change's job to decommission)

- [ ] 6.1 Confirm `-175a` health check green post-deploy
- [ ] 6.2 Confirm tenant-resolution JWT flow works end-to-end (task 4.3)
- [ ] 6.3 Document remaining known unknowns about `-dc78` (if any) that would need resolving before a founder decommission decision
- [ ] 6.4 Explicitly leave `-dc78` running — do not stop/delete/pause it as part of this change

## Stage 11. Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online (Vercel, unaffected by this change)
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push `apps/backend/main.py` (validation wiring) + `ARCHITECTURE.md`/`CLAUDE.md` doc updates to main
- [ ] 11.2 Railway auto-deploys `-175a` from main; confirm deploy SUCCESS
- [ ] 11.3 Production verification: health check + tenant-JWT-dependent request path both pass on the live `-175a` URL
- [ ] 11.4 Create report: `openspec/changes/reconcile-railway-antigravity-projects/reports/YYYY-MM-DD-deployment.md`, explicitly noting `-dc78`'s status is unchanged (still running, not decommissioned) as of this report
