# Deployment Report: hermes-jarvis-contexia — 2026-09-13

**Change:** hermes-jarvis-contexia (re-scoped this session per `HANDOFF.md` D1-D6)
**Stage:** 11 (Deploy to Production) — partially closed, see §5 for what's still open

---

## 1. Scope deployed today

Five feature commits + two deploy-hygiene commits, all pushed to `main` with explicit
founder confirmation before each push (per this repo's "never `git push` without confirmation"
rule):

| Commit | Fase | Summary |
|---|---|---|
| `666495b` | Fase C | Adopted uncommitted `plan_features.py` (`jarvis_chat`/`jarvis_voice`) + fixed two real copy bugs (`TenantInfoCard`/`UpgradePlanBanner` tier labels didn't match `pricing_catalog.py`). Switched `feature_list.json.active` to `hermes-jarvis-contexia`. |
| `f0da981` | Fase 1 (D1) | Merged the founder's personal Jarvis assistant into Taty's existing single Telegram bot/webhook. Removed the dead second-bot webhook (`jarvis_endpoints.py::jarvis_telegram_webhook`, never wired up in BotFather/Railway). |
| `4bd8940` | Fase B fix | Found and fixed a real bug in already-shipped code (`4933f0a`, 2026-09-02): `HermesStatusCard`/`jarvis-client.ts` expected `{online, url, uptime_seconds}` but the backend always returns `{status, gateway_url, hermes}` — the card showed "Sin conexión" even when Hermes was healthy. |
| `884acb4` | Fase E | New floating Jarvis bubble across the PWA shell (`components/jarvis/JarvisBubble.tsx`). Found and fixed a real UI collision live in the browser: the bubble's initial position landed exactly on the "Salir" logout pill already rendered by `overview`/`config`. |
| `18d5ba4` | Fase D (D2) | Growth/Enterprise B2B WhatsApp clients proxy to Hermes instead of the B2C Renta Natural lead flow. New `resolve_b2b_tenant_for_whatsapp_phone()` lookup (phone-normalized both sides) since no "tenant of a WhatsApp lead" concept existed before. |
| `8db9152` | Deploy hygiene | First (incomplete) attempt at the `CACHE_VERSION` bump — edited the wrong file (see §4). |
| `320dbb5` | Deploy hygiene | Real fix: ran `contexia-app`'s `npm run build` and synced `out/` → `app/` + repo root per the documented mapping, landing `CACHE_VERSION` v22 on the artifact Vercel actually serves. |

Full task-level detail and TDD evidence for each Fase lives in
`openspec/changes/hermes-jarvis-contexia/tasks.md` (updated in lockstep with each commit) and
`design.md` (D1-D6 decision ledger).

---

## 2. Backend (Railway, `elegant-success` / `antigravity-app-production-175a`)

- Deployment `d2a6c47b` — **SUCCESS**, picked up automatically on push.
- Verified live via `openapi.json` + direct calls:
  - `GET /api/v1/health` → `{"status": "healthy", ...}`.
  - `POST /api/v1/channels/jarvis/webhook` (the removed second-bot webhook) → **404** — confirmed gone.
  - `GET /api/v1/jarvis/status` → **401** (mounted, auth-enforced, correct).
  - `/api/v1/jarvis/{chat,status,brief}` all present in `openapi.json`; `/channels/jarvis/*` absent.

## 3. Frontend (Vercel, `contexia-web-app` project)

- Three deploys, all **READY**: `dpl_GbxCVCfRACkvtsRrw1PB4o6RDjzj` (18d5ba4), `dpl_DVGbX4vCkEprezAgehqvmE9HbcAL`
  (8db9152), `dpl_8TFZZJDpcWy4WVqirzp22edsgHBZ` (320dbb5, final).
- `contexia.online/sw.js` → confirmed `CACHE_VERSION = "v22-2026-09-13"` live (only after the
  second, real fix — see §4).
- Confirmed the new chunk carrying `JarvisBubble`'s compiled code
  (`_next/static/chunks/03chtzq6m-11k.js`, string `"Abrir Jarvis"`) loads with **200** on
  `contexia.online/app/overview`.
- `contexia.online/app/bunker` → Agentic OS section reachable, `HermesStatusCard` renders
  (shows "Sin conexión" — Hermes itself is not tunneled/reachable from this machine right now;
  this is the correct honest state given Hermes runs local-only, not a regression of the fix,
  which only corrected the response-shape mapping).

## 4. Real finding: three diverging copies of `sw.js` (self-improving-loop candidate)

`contexia-app/CLAUDE.md`'s hard rule requires bumping `CACHE_VERSION` on every build that
changes cached assets — a rule that exists because of a prior real production incident
(`antigravity-app/CLAUDE.md` §9). This session found and hit the *next* version of that same
class of failure:

1. Commit `8db9152` bumped `CACHE_VERSION` in `contexia-app/public/sw.js` — the correct
   **source** file — and Vercel built and deployed it successfully. But `contexia.online/sw.js`
   still served `v21-2026-09-10` afterward.
2. Root cause: `vercel.json` has `"outputDirectory": "."` — Vercel serves this repo **statically
   from its root**, not from a Next.js build of `contexia-app/`. The actually-live `/sw.js` is a
   **manually-synced build artifact** at the repo root (`./sw.js`), produced by
   `cd contexia-app && npm run build` then copying `out/app/*` → `app/` and everything else in
   `out/` → the repo root (documented only in commit `1ec9d2b`'s message, not in a checklist).
3. A third, apparently-orphaned copy was also found: `app/sw.js` at `v18-2026-09-04` — stale
   because Next's static export never emits an app-scoped `sw.js` (it's a top-level asset), so
   this file was never part of any correct sync and is effectively dead weight, left untouched.
4. Real fix (`320dbb5`): ran the build, synced `out/` per the documented mapping, verified the
   new chunks actually contain `JarvisBubble`'s code before staging, and — critically — diffed
   the full `git status` against the intended build-artifact scope before `git add`, to avoid
   sweeping in unrelated untracked files from other in-progress sessions
   (`taty-channel-consolidation/`, `whatsapp-durable-inbox/`, GTM handoff docs, etc.).

**Recommendation for `DEPLOYMENT_STAGE/checklist-vercel.md` / `CHECKPOINTS.md`:** after any
`contexia-app` frontend change, verify the *live* `contexia.online/sw.js` version — not just
that Vercel's build succeeded — since a successful build of the wrong artifact still deploys
successfully. A build+sync script (`scripts/sync_contexia_app_build.*`) that encodes the
`out/app/* -> app/, everything else -> repo root` mapping would remove the manual-copy step
that caused this drift in the first place; that script does not exist today, only the
comment-documented mapping in one historical commit message.

## 5. What's still open (Stage 11 not fully closed for this change)

- **Fase 1 tasks 1.5-1.7**: Telegram webhook signature verification left explicitly untouched
  (risk of silently breaking the live bot if `TELEGRAM_WEBHOOK_SECRET` doesn't match what's
  actually configured in Telegram's `setWebhook` — never verified this session); obtaining and
  setting `TELEGRAM_JUAN_DAVID_CHAT_ID` in Railway is a founder action.
- **Fase D7-D13** (memory persistence, sales voice agent, Gemini scope, etc.) are design-only,
  referenced in `HANDOFF.md` §2, not part of this session's build scope.
- **Two pre-existing, non-regression observations surfaced during verification** (neither
  introduced by this session's changes — flagged for a founder decision, not fixed blind):
  - A real admin session (logged in as Admin in the Búnker) showed "Jarvis no disponible en tu
    plan" in `AgenticOsSection` and no floating bubble in the PWA — `readRoleFromJwt()` (shared
    by both, pre-existing since commit `4933f0a`) isn't resolving `isAdmin=true` for this
    session's actual JWT shape. Worth checking directly rather than assumed fixed by this
    session's `HermesStatusCard` fix, which only touched the status-shape mapping.
  - One uncaught minified React error (`#418`, hydration mismatch) observed in the console on
    `contexia.online/app/overview` with this same session. Not isolated to a pre- vs. post-
    deploy comparison this session (would have required a temporary rollback to confirm); noted
    here rather than silently ignored or blindly "fixed."
- **Stage 11 report checklist items not applicable to this change**: no migration was applied
  (none needed), no founder-only manual step beyond the ones above.

## 6. Test evidence (backend)

- 8 new tests (Fase 1, D1 single-bot routing) — green, TDD red confirmed first.
- 13 new tests (Fase D, D2 B2B WhatsApp routing + phone lookup) — green, TDD red confirmed
  first. 5 pre-existing tests corrected (were silently hitting real Supabase because they didn't
  mock the new lookup function).
- Full backend suite: 33 pre-existing failures (`shadow_gl`/`wizard`, unrelated to any file this
  session touched — confirmed by path), 1267 passed, 120 skipped — zero regressions.
- Frontend: `tsc --noEmit` clean after every Fase C/E change.

---

**Bottom line:** the code for Fases 1 (D1), B (fix), C, D (D2), and E is live in production and
verified against real HTTP responses, not just "build succeeded." The change is **not** archived
— §5's open items (especially the webhook signature gap and the two observations) should be
resolved or explicitly deferred by the founder before this change is considered closed.
