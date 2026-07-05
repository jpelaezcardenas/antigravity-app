## Why

Contexia has two Railway projects both running a service named `antigravity-app`, both pointing at the same Supabase database: `elegant-success` (public URL `-175a`, documented in `ARCHITECTURE.md` as canonical production) and `enthusiastic-youthfulness` (public URL `-dc78`, undocumented). This was flagged as technical debt in the archived `agentic-performance-management-phase4` change with an explicit decision to keep both alive "for now" and a follow-up ("reconcile the two Railway projects... update CLAUDE.md") that was never turned into an actual OpenSpec change — it has sat unresolved since 2026-06-24.

Real investigation (this change) found: `-175a` is confirmed via Vercel's `/api/v1/*` rewrite to be the actual live-traffic backend. No Telegram webhook is currently registered on either project (`getWebhookInfo` → empty URL), so the originally-assumed "active dependency" isn't currently live — but `-dc78` holds `TELEGRAM_BOT_TOKEN` (which `-175a` lacks) and the Telegram integration is webhook-based by design (not polling), so re-enabling it without reconciling first would silently target the wrong project. Deeper variable diffing also found `-dc78`'s `SUPABASE_KEY` is an anon-role JWT while `-175a`'s is service_role — a real privilege divergence — and `-dc78` lacks `GLM_API_KEY` entirely, meaning it can't do Contexia's current GLM 5.2 interactive-model routing.

## What Changes

- Migrate `-dc78`'s unique-and-needed environment variables (`TELEGRAM_BOT_TOKEN` confirmed necessary; others assessed per task 2) to `-175a`.
- Document `-175a` unambiguously as the sole canonical backend in `ARCHITECTURE.md`/`CLAUDE.md` (already true in practice per Vercel routing; makes it true in the docs too).
- Verify Telegram bot functionality end-to-end on `-175a` before any decommissioning.
- Decommission `-dc78` only after end-to-end verification passes — **not part of this change's automatic scope**; requires a separate explicit go-ahead once verification succeeds (see Non-Goals).

## Non-Goals

- **Does not decommission `-dc78` as part of this change.** Per the original task's explicit instruction, decommissioning only happens after end-to-end verification (Telegram bot responds, health checks pass) — that verification gate is itself a task in this change, and the actual decommission is a follow-up action requiring explicit founder confirmation, not an automatic step.
- **Does not resolve the Bitwarden master-password exposure on `-dc78`** — already tracked separately (`task_d1ec7639`, the Bitwarden Secrets Manager migration). This change's env-var migration explicitly excludes `BW_MASTER_PASSWORD`/`BW_CLIENT_ID`/`BW_CLIENT_SECRET` from being copied to `-175a` — copying them would spread the same insecure pattern, not fix it.
- **Does not re-enable the Telegram webhook** as part of this change unless verification requires it — registering a webhook is itself a meaningful production action or the founder's own agent-config decision, not something to flip on as a side effect of infra cleanup.

## Capabilities

### New Capabilities
- `railway-deployment-topology`: Documents which Railway project is canonical, what env vars are required for `-175a` to be fully functional (including anything currently only on `-dc78`), and the verification gate required before any future decommission of a duplicate deployment.

### Modified Capabilities
_None._ No existing spec covers Railway deployment topology.

## Impact

- **Affected infra**: Railway env vars on `-175a` (additions only — `TELEGRAM_BOT_TOKEN` and any other confirmed-needed `-dc78`-only variables, excluding Bitwarden secrets).
- **Affected docs**: `ARCHITECTURE.md`, `CLAUDE.md` (canonical backend clarification).
- **Affected functionality**: Telegram bot (Taty) — currently non-functional on both projects (no webhook registered); this change makes `-175a` capable of hosting it correctly if/when re-enabled.
- **Risk carried forward**: `-dc78` remains live and undocumented until a separate, explicit decommission decision is made after this change's verification tasks pass.
