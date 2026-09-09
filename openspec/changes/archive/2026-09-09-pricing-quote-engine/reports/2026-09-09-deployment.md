# Stage 11 — Deployment report (2026-09-09)

**Status: DEPLOYED AND VERIFIED IN PRODUCTION.**

Authorised explicitly by the founder ("Merge to main + deploy"). The migration had been
authorised and applied separately the day before — see `2026-09-08-migration.md`.

| | |
|---|---|
| Merged | `f96d487..dfdcb8a` → `main`, **fast-forward** (no merge commit, conflicts impossible) |
| Pushed | `origin/main` |
| Railway | deployment `c5133932-65d5-4651-ad70-c2e50b18451e`, status **SUCCESS** |
| Vercel | `contexia.online/app/bunker` → 200 |
| Migration | `0048` applied 2026-09-08, verified again post-deploy |

## How the merge was done

`git fetch . feat/pricing-quote-engine:main` — updates `main` **without checking it out**.
Chosen deliberately: a concurrent session was working in this same working directory on
`feat/voicebox-local-voice-adoption`, and a `git checkout main` would have yanked its tracked
files out from under it mid-task. `fetch .` also refuses anything that is not a fast-forward,
so it doubles as a guard.

## Verified live, not assumed

**Backend (Railway):**

| Route | Result |
|---|---|
| `GET /api/v1/health` | 200 |
| `GET /api/v1/pricing/pre-cotizacion` | **401** — new route mounted, auth enforced |
| `GET /api/v1/pricing/pre-cotizacion?tenant_id=whatever` | 401 — auth runs first; the param does not exist (Decisión #17) |
| `GET /api/v1/financials` | 401 — unchanged |
| `GET /api/v1/centinela/alerts` | 401 — unchanged |
| `GET /api/v1/radar/proyeccion-caja` | 401 — unchanged |

**Frontend (Vercel) — traced all the way to what a user actually loads:**

| Check | Result |
|---|---|
| `contexia.online/app/bunker` | 200 |
| Live `sw.js` `CACHE_VERSION` | `v19-2026-09-08` — the bump is serving, so no stale-cache trap |
| Live Búnker page references the new chunk | yes (`0x__o-vi52nbo.js`) |
| That chunk, fetched from production, contains `Honorario / Banda` | yes |

The last two matter more than a 200 on the page: they are what distinguishes "deployed" from
"deployed and reachable". This change was one commit away from shipping a backend with an
invisible UI (see `2026-09-08-implementation.md`, "Build artifact"), so the served HTML → served
chunk → string chain was walked end to end rather than trusted.

**Database:** `uvt_values` still returns `2025 → 49799`, `2026 → 52374`.

## Deploy ordering — why it was safe

`CrmService.list_b2b_clients` now projects `service_band`, and its `except` branch falls back to
**demo data** on any Supabase error. Had the code shipped before the migration, the Búnker's B2B
roster would have silently displayed demo clients. Migration first (2026-09-08), deploy second
(2026-09-09) — the hazard never opened.

## Concurrent-session hazard, resolved by this merge

`feat/voicebox-local-voice-adoption` was branched off this branch's tip mid-work and sits on
`ce3709b`, so it carried this change's first three commits — the backend endpoint and the
`service_band` write path — **without** the build artifact (`28f9918`). Had it reached `main`
first, it would have shipped this feature to production incomplete, with no one deciding to.

Merging this branch first put that base into `main`, so the exposure is closed. The other
session's work was never touched: its branch holds its own commit, and its uncommitted files are
intact.

## What is deliberately NOT done

- **No `service_band` backfill.** All 11 clients remain `NULL`. Nobody recorded which band those
  fees were quoted under, and inferring it from the amount is the guess this change removes.
- **No UI for the pre-quote result.** The endpoint is live and callable; rendering it in the CRM
  is a separate change (proposal.md, Non-goals).

## Founder action (not blocking, same deferred pattern as prior tenant-scoped changes)

Log into the Búnker and confirm the "Honorario / Banda" column and the alta band selector render,
and that setting a band persists. This agent does not handle plaintext credentials, so the
authenticated round trip was not exercised — only the unauthenticated contract (401) and the
served-asset chain.
