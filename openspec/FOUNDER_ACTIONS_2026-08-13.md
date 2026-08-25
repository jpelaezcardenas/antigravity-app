# Founder Actions — Pre-GTM Tech-Debt Triage (2026-08-13)

Consolidated from archiving 9 of 11 accumulated OpenSpec changes and deferring 2. Every item here
was verified live during the triage, not copied from stale docs — see the individual change's
`reports/2026-08-13-*.md` for the evidence trail behind each one.

> **Re-verified 2026-08-25.** Items 1, 2 and 8 were rewritten after re-checking them live — the
> Keeper migration is **closed**, not pending (see §"Keeper — CLOSED" below). A new item **12**
> was added for a credential exposure found during that re-check. Nothing else changed.

## HIGH priority

| # | Action | From change | What's blocked | Evidence |
|---|---|---|---|---|
| 12 | **Rotate the Bitwarden master password.** Its live value was committed in plaintext in `ARCHITECTURE.md` Decision #12 — a canon doc that auto-loads into every agent session — and in `docs/supabase-mcp-admin.md`. Both were redacted 2026-08-25, but **git history keeps the value forever**, so redaction alone does not close this. Rotate in Bitwarden, then update `BW_MASTER_PASSWORD` on Railway `-175a`. | found 2026-08-25 | The Bitwarden master password unlocks the vault holding effectively every Contexia secret. This outranks every other security item on this page. | `git log -S 'Lindafea' -- ARCHITECTURE.md`; redaction commit 2026-08-25 |
| 3 | Obtain the Meta App Secret and set 4 Railway env vars (`WHATSAPP_APP_SECRET`, `WHATSAPP_WEBHOOK_VERIFY_TOKEN`, `META_APP_SECRET`, `META_WEBHOOK_VERIFY_TOKEN`) — **ONLY needed to activate the alternate direct Meta→Railway ingress; NOT a blocker for the currently-live path** | `taty-channel-consolidation` / `whatsapp-durable-inbox` | **CORRECTION (2026-08-14):** the earlier "WhatsApp inbound 100% rejected" claim was WRONG. There are two inbound paths. **Live today: WhatsApp → Chatwoot (Docker, holds Meta creds) → local `chatwoot-bridge` (`POST /webhook`, authed by `WEBHOOK_TOKEN`, NOT Meta HMAC) → `TatyAgentService`** — works WITHOUT the App Secret (see `apps/chatwoot-bridge/main.py:37-38`, which is explicit that the bridge runs "before WHATSAPP_APP_SECRET exists in Railway"). Meta reaches local Chatwoot via the Cloudflare tunnel. The 403/`X-Hub-Signature-256` gate belongs to the SEPARATE direct Meta→Railway durable-inbox path (`whatsapp_endpoints.py`), which is OFF by default (`INBOX_POLLER_ENABLED`). Founder confirmed live: messages from a second line reach Taty and are visible in Chatwoot. So this is a **future architecture option, not a campaign blocker.** | `apps/chatwoot-bridge/main.py:37`, `apps/backend/presentation/whatsapp_endpoints.py:1-13`, `ARCHITECTURE.md` Decision #19 |
| 4 | Provide the two Renta Natural pricing tiers (asalariado / independiente-freelancer) | `taty-whatsapp-renta-sales-capability` | Until provided, Taty must not state a specific price to a WhatsApp lead. `crm_service.py`'s single fixed price ($89.000) contradicts the founder's own recollection of tiered pricing (~$300.000, varies) — confirmed against all 7 real transactions, all consistently $89.000. Real code change needed once numbers exist (tier-aware `checkout_lead_payment`), not just a KB update. | `archive/2026-08-13-taty-whatsapp-renta-sales-capability/tasks.md` §2.1b/2.1c |

## MEDIUM priority

| # | Action | From change | What's blocked | Evidence |
|---|---|---|---|---|
| 5 | Complete ONE real Renta Natural checkout (real card, real money) and report the transaction reference | `wompi-production-go-live` | Production credentials are live and stable, but the go-live is unverified with a real payment — never simulated by an agent, per this change's own explicit constraint. | `archive/2026-08-13-wompi-production-go-live/reports/2026-08-13-deployment.md` |
| 6 | Send a WhatsApp message from a physical phone to +57 310 6229289 and confirm: it lands in Chatwoot inbox 1 (not conversation 3), Taty replies once (not duplicated), and a human's reply typed in Chatwoot also reaches the phone | `taty-whatsapp-renta-sales-capability` | Backend round-tripping is proven via real/synthetic messages, but nobody has confirmed it from an actual phone screen since the last fix (Stage 5's incident chain). Also covers the production smoke test (14.5). | `archive/2026-08-13-taty-whatsapp-renta-sales-capability/tasks.md` §5.7/14.5 |
| 7 | Start Meta Business Verification (raises `TIER_250`); re-verify the WhatsApp display name (currently `EXPIRED`); create `es_CO` message templates for >24h re-engagement | `taty-whatsapp-renta-sales-capability` | Not blocking the inbound-first motion already live, but needed for outbound campaign scale. | Same tasks.md §6.2-6.4 |
| 9 | Decide and execute the merchant-of-record fix: set up/verify a Wompi account for Entidad A | `taty-wompi-link-hitl-gate` (deferred, not archived) | This change's own HITL gate is a safety brake, not a substitute for this decision. | `changes/taty-wompi-link-hitl-gate/tasks.md` §5.1 |

## LOW priority

| # | Action | From change | What's blocked | Evidence |
|---|---|---|---|---|
| 10 | Formal code-review sign-off | `automated-approval-rules` | The Stage 10.2 DoD checklist's "Reviewer: [Pending]" was never filled — code has been live and stable since 2026-06-25, this is a follow-up sign-off, not a defect. | `archive/2026-08-13-automated-approval-rules/reports/2026-06-25-deployment.md` (closure note) |
| 11 | Confirm (via direct Supabase access) whether the originally-cited stuck task `661d395f…` was ever resolved | `hermes-manus-poller-activation` | The poller is confirmed operational (clean logs, zero errors, continuous ticks) but currently shows `pending_seen: 0` — cannot confirm the specific historical task's fate without DB access (Supabase MCP was unavailable this session). | `archive/2026-08-13-hermes-manus-poller-activation/reports/2026-08-13-deployment.md` |

## Keeper — CLOSED (2026-08-25). Do not reopen.

**Keeper is legacy. It is not part of Contexia's architecture and no work on it is pending.**
Bitwarden Cloud fully replaced it in `keeper-migration-2026-06-15` (archived 2026-08-13).

Verified live 2026-08-25:

- `GET /api/v1/secrets/health` on canonical `-175a` →
  `{"status":"healthy","provider":"bitwarden-cloud","vault_url":"https://vault.bitwarden.com"}`
- `apps/backend/core/secrets_provider.py` implements only `BitwardenCloudProvider` and
  `VaultwardenProvider`. **There is no Keeper provider, client, or code path anywhere in the repo.**

Cleanup done in the same pass: deleted `START_HERE_KEEPER_MIGRATION.txt` and `CURSOR_GO_NOW.txt`
from the repo root. Both were stale handoff docs instructing an agent to "continue T2–T14" of a
migration that had already finished, and both pointed at three reference files
(`CURSOR_PROMPT.md`, `KEEPER_MIGRATION_HANDOFF.md`, `ESTADO_ACTUAL.md`) that no longer exist.
They are recoverable from git history; the real record lives in
`openspec/changes/archive/2026-08-13-keeper-migration-2026-06-15/`.

**Agent rule:** if you encounter a Keeper reference, treat it as historical. Do not propose
resuming the migration, do not create a change for it, and do not re-add it to any status doc.

Two things survive, and neither is a Keeper migration task:

| Was | Now |
|---|---|
| ~~#1 Delete the Keeper vault (HIGH, "40 days overdue")~~ | **Founder housekeeping, LOW.** The external Keeper account still holds a copy of ~330 historical secrets. Deleting it is one manual action in Keeper's own app. It is not a blocker for anything and no code depends on it — but item **12** (rotate the Bitwarden master password) genuinely does outrank it and should happen first. |
| ~~#2 Fix the `dc78` Bitwarden secrets-health decryption failure~~ | **Decommission `dc78`, don't fix it.** Re-confirmed 2026-08-25: `dc78`'s endpoint still returns `unhealthy` (`bw unlock` cryptography error) because its `BW_MASTER_PASSWORD` was never updated in the 2026-07-05 rotation. Per `ARCHITECTURE.md` Decision #9, `dc78` receives no real traffic and supports no Contexia functionality. Fixing its env var would keep a zombie service alive; the correct action is to shut the project down. |
| ~~#8 Decide Bitwarden Cloud vs. self-hosted Vaultwarden~~ | **Bitwarden Cloud is the decision, by default and by evidence.** It has run healthy on the canonical backend for ~10 weeks. The `VaultwardenProvider` class and its compose file stay in-repo as an unused escape hatch. Revisit only if there is an actual reason to leave Bitwarden Cloud. |

## Pre-existing debt, not touched by this triage (carried forward from prior audits)

- **Secrets rotation ~60 days overdue** — `keeper-security-audit-2026-06-15` flagged 15+ exposed
  secrets (Supabase PAT, Vercel token, LLM keys, Telegram token). Railway secrets were rotated
  2026-06-14; the rest were not confirmed. **Now folded into item 12** — do the Bitwarden master
  password first, then sweep the rest in the same session.
- **3 unmerged security PRs** from 2026-06-14 (`fix/security-bug-audit-2026-06-14`): antigravity
  PR#4, copiloto PR#1, contexia-content-os PR#1.
- ~~**`AUTH_ENFORCED=False`** in production~~ — **STALE, corrected 2026-08-25.** The production
  auth surface is closed. Verified live on canonical `-175a`: `/api/v1/financials` → `401`,
  `/api/v1/agents/ask` → `401`, `/api/v1/approval-queue` → `401`, all without a token, while
  `/api/v1/health` → `200`. Whatever the flag's literal value, protected routes reject
  unauthenticated callers. Do not carry this item forward again without re-testing it.

These are recommended as the scope of a dedicated security-focused follow-up thread (see
`MEMORY.md` → `tech-debt-pre-gtm-2026-08-13`'s "Recommended Thread Sequence").

## What's left active/deferred after this triage

- `metrics-dashboard-phase9` — deferred, 0/108 tasks, see its `DEFERRED.md`.
- `taty-wompi-link-hitl-gate` — deferred, 0/16 tasks, see its `DEFERRED.md`.
- `hermes-multi-tenant-wrapper` — Phase 1A archived; remaining scope (JWT type mismatch,
  permissive RLS policies, Phase 2/3) tracked in its `archive/2026-08-13-hermes-multi-tenant-wrapper/DEFERRED.md`.

`feature_list.json`'s `active` pointer is `null` — nothing is currently claimed as in-progress.
