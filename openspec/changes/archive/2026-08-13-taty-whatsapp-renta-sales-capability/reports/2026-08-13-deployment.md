# Deployment Report — taty-whatsapp-renta-sales-capability

**Date:** 2026-08-13
**Status:** In production, serving real customer traffic. 57/74 tasks done; remaining 17 are
founder actions or genuinely deferred, non-blocking items.

## Summary

This change fixed Taty's WhatsApp channel (previously stuck on two static replies) and added a
declaración-de-renta-persona-natural sales capability. The interim report
(`reports/2026-08-11-step-10-unit-test-and-db-verification.md`) documents an extensive live-incident
history found and fixed during rollout — pgvector schema/RLS bugs, a scheduled-task stale-process
restart gotcha, Chatwoot's `incoming`-message 422 on real (non-Api) inboxes, and image-caption text
loss. This report closes the change out for archival purposes.

## Verified today (2026-08-13, tech-debt triage)

- `main` is at `2cd52a9`, in sync with `origin/main`, working tree clean — all of this change's
  commits are pushed (task 14.1).
- `GET /api/v1/health` on the canonical `175a` backend: healthy (task 14.3).
- `https://contexia.online/privacy` and `/terms` (the Stage 6.1 Vercel rewrites): both `200`
  (task 14.4).
- No `DEEPSEEK_API_KEY`-consuming code exists — Stage 3.4's DeepSeek client was deferred and never
  implemented, so 14.2's env var requirement doesn't apply to what actually shipped.
- All 4 delta specs synced into `openspec/specs/`: `chatwoot-whatsapp-delivery` and
  `taty-knowledge-base` (new capabilities), `taty-fiscal-assistant` (2 `ADDED` requirements
  appended), `taty-whatsapp-sales-router` (2 `MODIFIED` requirements surgically replaced, 4
  untouched requirements preserved).
- `feature_list.json` updated: this feature marked `done`, `active` set to `null`.

## Explicitly NOT done — founder actions, not silently closed

- **2.1c** — pricing tiers (asalariado/independiente) not yet provided by the founder; Taty must
  not state a specific price until they are.
- **5.7/5.8, 14.5** — physical-phone verification of the real WhatsApp number. Backend-level
  round-tripping is proven (multiple real and synthetic messages processed end-to-end per the
  Stage 5 incident log), but nobody has confirmed it from an actual phone screen since the last
  fix. Never simulated by an agent, per this change's own explicit constraint.
- **6.2-6.4** — Meta Business Verification, display-name re-verification, `es_CO` message
  templates. All founder-owned Meta Business Manager actions, not blocking the inbound-first
  motion already live.
- **3.4** — DeepSeek client, deferred pending `DEEPSEEK_API_KEY` (doesn't exist anywhere yet). The
  `taty-v1` fallback chain works today without it (Groq primary, Gemini/OpenRouter fallback).

All of the above are captured in `openspec/FOUNDER_ACTIONS_2026-08-13.md`.

## Known structural gap flagged, not fixed (real scope of its own)

Per task 3.6/3.7's finding: a transient pgvector retrieval failure (rate limit, Supabase hiccup)
silently degrades ALL of Taty's fiscal answers — not just WhatsApp — to a smaller, staler,
out-of-sync in-memory KB fallback (`ensure_dian_loaded()` only ever loads the original 48-chunk
file, never the 84 chunks now live in pgvector). This deserves its own design decision on whether
that fallback should exist at all vs. fail loudly. Not addressed here.

## Disposition

Archiving now as part of the broader 11-change tech-debt triage restoring the "one change at a
time" invariant (HARNESS.md). See `MEMORY.md` → `tech-debt-pre-gtm-2026-08-13`.
