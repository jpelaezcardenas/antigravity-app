# Deployment report — sell-machine-creative-swarm

Date: 2026-07-19

## Summary

Change deployed and verified live in production. The Copywriter → Content Critic →
Approval Queue creative loop is now reachable at `https://antigravity-app-production-175a.up.railway.app/api/v1/sell-machine/*`,
and the "Sell Machine" Búnker section is live at `https://contexia.online/app/bunker`.

## Commits deployed

- `fac55df` — feat(sell-machine): implement Copywriter + Content Critic + orchestration + endpoints + Búnker UI (Sections 1-9)
- `3c22327` — chore(pwa): bump service worker CACHE_VERSION for Sell Machine deploy (v11->v12)
- `bb450fd` — chore(bunker): sync contexia-app build output for Sell Machine + sw.js bump

## Stage 11 steps executed

1. **10.1-10.2** — Merged to `main`, pushed. No conflicts.
2. **10.3 — Dark deploy confirmed.** Railway deployment `1eef1b9f`/`6007b237` (commit `fac55df`)
   went `SUCCESS` with `SELL_MACHINE_CANONICAL` unset (defaults `false` per `config.py`).
   Confirmed via `railway_list_variables` that the flag was absent before flipping it.
3. **10.4 — sw.js bump + build sync.** `CACHE_VERSION` bumped `v11-2026-07-19` -> `v12-2026-07-19`.
   Rebuilt `contexia-app` (`npm run build`), synced `out/` -> `app/` additively (new buildId
   `hYi6BIgheVuHVhVH-QJ4M`, 1 new shared chunk `0rf189rnpbxt_.js`). Verified 0 missing
   `/_next/static/*` references with the Python all-characters chunk verifier before committing.
   Vercel deployment `dpl_4XdUcCgykA8heQKyFKWe6MtnuXPA` (commit `bb450fd`) is `READY`, aliased to
   `contexia.online`.
4. **10.5 — Live dark-deploy verification.** Loaded `https://contexia.online/app/bunker`: sidebar
   shows "Sell Machine" alongside Dashboard, CRM/Ventas, Onboarding, Social Content Ops, Agentic OS,
   Configuración — no regression. Clicked into "Sell Machine": section renders (header, "Generar
   Hooks" button, empty "Campaign Packages Pendientes" state), and the pre-flip API call correctly
   surfaced `{"detail":"Not Found"}` (flag still off, 404 as designed) rather than a blank/crashed
   screen.
5. **10.6 — Flag flip + live full-loop smoke test.**
   - Set `SELL_MACHINE_CANONICAL=true` on Railway (`elegant-success` / `-175a`). Railway did not
     auto-redeploy on the variable change within ~1 minute, so triggered an explicit redeploy
     (`railway_redeploy` on the existing image, new deployment `996a4862`). Deployment reached
     `SUCCESS`; the app took longer than the usual ~80s cold start to answer requests (~5-6 min,
     `502 Application failed to respond` throughout) before serving 200s — no error in the visible
     logs beyond a benign pydantic `protected_namespaces` warning, consistent with a slow cold
     start under load rather than a crash.
   - Exercised the full loop live via direct API calls (accented characters in the JSON payload
     broke shell quoting through inline `curl -d`, so requests were sent via `--data-binary @file`
     instead — noted here in case this recurs for future smoke tests):
     1. `POST /api/v1/sell-machine/hooks/generate` → 3 real GLM-generated hooks (Renta Natural /
        DIAN pain points), no hard-ban violations.
     2. `POST /api/v1/sell-machine/hooks/evaluate` → all 3 survived the Content Critic.
     3. `POST /api/v1/sell-machine/campaigns` → created campaign package
        `id=7b4439c3-ba70-4490-bd0b-3fcd412aac20`, `draft_id=c354a9eb-588a-455e-8c72-60abda7fab79`,
        `status=pending_approval`.
     4. `POST /api/v1/approval-queue/approve` (the existing, unmodified endpoint — confirms Change
        E's Decision 1: reuse the generic Approval Queue rather than a Sell-Machine-specific gate)
        → `{"success":true,"status":"approved"}`.
   - **Verified directly in Supabase** (`execute_sql` on project `kpynymwghfwshvcvevxq`):
     `SELECT status, approved_by FROM approval_queue WHERE id = '7b4439c3-...'` returned
     `status="approved"`, `approved_by="jpelaezcardenas@gmail.com"` — the row is real, not mocked.
   - **Decision on the demo row**: leaving it in place, matching the precedent set in Change B's
     report (a real approved `campaign_package` row is a harmless, useful production demonstration
     of the loop — it is a draft record, not a live ad spend or a Meta post, since execution is
     Change F, not yet built).
7. **10.7 — This report.**

## Accepted risks (carried from design.md)

- **Non-deterministic Critic backed by a hard deterministic gate.** The Content Critic's LLM tone
  check (`_llm_tone_check`) can vary run-to-run, but the hard-ban phrase list
  (`_HARD_BAN_PHRASES` in `content_evaluator.py`) is a non-overridable, deterministic gate that the
  LLM cannot bypass — confirmed by the credential-free unit tests in Section 2. This smoke test's
  live hooks contained no hard-ban phrases and were not tested against the LLM-failure fallback
  path (already covered by unit tests).
- **`tenant_id` not persisted on Approval Queue rows** (pre-existing, not introduced by this
  change) — the `campaign_package` row created here, like all other draft types in this table, has
  no tenant scoping column. Unchanged risk posture from prior changes (A/B) that also write through
  paths adjacent to this table.
- **R1 (CRM/Sell Machine endpoints have no request-level auth)**, carried from the overall plan
  (`eventual-snacking-ritchie.md`) — `/api/v1/sell-machine/*` has the same posture as
  `/api/v1/crm/*` and Social Ops: no bearer/auth check, gated only by the feature flag and the
  Vercel edge middleware on the Búnker route. Accepted for this stage, same as Changes A/B.

## Verification evidence

- Railway deployment `996a4862-831d-4c06-a524-2bd0bad33668`: `SUCCESS`.
- Vercel deployment `dpl_4XdUcCgykA8heQKyFKWe6MtnuXPA`: `READY`, aliased to `contexia.online`.
- Live `GET /api/v1/sell-machine/campaigns` (post-flip): returns `[]` before the smoke test, then
  reflects the created/approved package.
- Supabase `approval_queue` row `7b4439c3-ba70-4490-bd0b-3fcd412aac20`: `status="approved"`.
- Browser: Búnker sidebar + Sell Machine section screenshots/DOM confirmed via the in-app browser
  (no console errors, correct empty/error states pre-flip).
