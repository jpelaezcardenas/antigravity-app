# Implementer report — hermes-bridge-token-production-hardening

- Date: 2026-08-28
- Scope: full change (Sections 1-8 of tasks.md); Section 9 (reviewer gate) delegated to a
  separate `reviewer` subagent per HARNESS.md — this report is written to close that loop
  properly instead of skipping the paper trail, which the first review pass correctly flagged
  as missing.

## Section 1 — Poller: bearer-token auth, remove dead JWT path

TDD: wrote `TestBackendClientHeaders` (2 tests) in `tests/test_poller.py` against the OLD code —
confirmed red (`AttributeError: ... has no attribute 'HERMES_BRIDGE_TOKEN'`). Then:
- `apps/hermes-manus-poller/backend_client.py`: removed `sign_tenant_jwt()`, the unused `_TENANT_ID`
  constant, and the `datetime`/`timedelta`/`timezone`/`Optional` imports it needed. `_headers()` now
  reads `settings.HERMES_BRIDGE_TOKEN` directly.
- `apps/hermes-manus-poller/config.py`: replaced `CONTEXIA_JWT_SECRET` with `HERMES_BRIDGE_TOKEN`.
- `apps/hermes-manus-poller/requirements.txt`: removed `python-jose[cryptography]` — confirmed via
  grep it was the only remaining reference to `jose`/`jwt` in the poller.
- Full suite green: 47/47 (`python -m pytest tests/test_poller.py`).

## Section 2 — Backend guard: confirmed unchanged

Read `apps/backend/presentation/sell_machine_endpoints.py:44-56` — matches the MODIFIED spec
exactly. No code change (design explicitly says none is needed).

## Section 3 — Inert deploy verification

The poller has no persistent process to restart — `run_poller.ps1` invokes a fresh `python main.py`
every tick (Windows Scheduled Task `ContexiaHermesManusPoller`, 1-minute trigger,
`MultipleInstances=IgnoreNew`). Confirmed via `logs/poller-20260828.log`: the tick at 08:15:16
already ran the new code (saved to disk moments earlier) with `HERMES_BRIDGE_TOKEN` still unset —
`HTTP/1.1 200 OK`, no regression.

## Section 4 — Secret generation + configuration

- Generated via `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
- **`bw` CLI hung/unreachable from this shell** (`bw status` timed out at 30s) — a pre-existing
  environment limitation, not caused by this change. Value was reported directly to the founder in
  chat (private channel) instead, with the suggested Bitwarden entry name
  `Hermes Bridge Token (production)`, so they can store it themselves. **The value was never
  written to any repo file, doc, or report** — confirmed by the reviewer's own grep pass.
- Set on Railway via `mcp__contexia-railway__railway_set_variable` (project `elegant-success`,
  service `antigravity-app`, environment `production`, `skip_deploys=false`). New deployment
  `d7eeeed3` reached `SUCCESS`.
- Appended to `apps/hermes-manus-poller/.env` (gitignored — confirmed via
  `git check-ignore -v` before writing) with a surgical `printf >>` append, deliberately not a
  full-file rewrite, to avoid clobbering `DRY_RUN=true`, which a parallel session (GTM Envigado
  go-live) is actively managing in that same file.

## Section 5 — Live verification

Initial curls (~13:20 UTC) returned 502 on every path, including `/api/v1/health` — this was the
Railway container's own ~76s cold-start window after the redeploy (matches ARCHITECTURE.md's
documented "~80s antes de servir"), confirmed by reading `railway_deployment_logs` for deployment
`d7eeeed3`: `Application startup complete` at 13:21:50, and a real `/tasks/pending` request already
succeeding at 13:22:12. Re-ran verification after startup completed:
- No header → `401 {"detail":"missing or malformed Authorization header"}`
- Correct token → `200 []`
- Wrong token → `401 {"detail":"invalid bridge token"}`
- Poller's own tick at 08:23:12 (local log time) sent the real token and got `200 OK`.
- Grepped the repo for other callers of the 5 routes: only `contexia-app/lib/sell-machine-api.ts`
  matched `sell-machine/`, but it calls `/sell-machine/campaigns` (POST create, GET list) — a
  different, admin-session-authenticated route, not one of the 5 this change touches. No other
  caller found.

## Section 6 — Living docs

- `AGENTES.md` (~line 345-352): corrected "fail-open until the env var is set" to state the token
  is live/enforced in production as of this change, referencing it by name.
- `ARCHITECTURE.md`: checked, no stale claim at that level of granularity (same conclusion the
  original `hermes-task-queue-tenant-scoping` implementer reached for the same reason).
- New `docs/runbooks/hermes-bridge-token-rotation.md` — manual rotation steps + rollback.

## Section 7 — Cleanup verification (CORRECTED after reviewer feedback)

First pass: `grep -rn "CONTEXIA_JWT_SECRET|sign_tenant_jwt" apps/hermes-manus-poller/ --include="*.py"`
— zero matches, checked off as clean. **This was wrong** — the reviewer caught that
`apps/hermes-manus-poller/.env.example:17` still had `CONTEXIA_JWT_SECRET=` with a stale "open
today" comment, because the grep was scoped to `*.py` only. Fixed: `.env.example` now documents
`HERMES_BRIDGE_TOKEN=` with an accurate comment pointing at the rotation runbook. Re-ran the grep
with no file-type filter across the whole directory — genuinely zero matches now.

## Section 8 — Testing

- Poller: 47/47 (`tests/test_poller.py`).
- Backend: 32/32 across `test_sell_machine_endpoints.py` (9) and `test_operator_task_endpoints.py`
  (23, including the pre-existing `TestHermesBridgeToken` class's 4 scenarios) — no backend code
  was changed, this just confirms no regression.
- `./init.sh`: green (harness structure + one-change-at-a-time invariant).

## Files touched

- `apps/hermes-manus-poller/backend_client.py`, `config.py`, `requirements.txt`,
  `tests/test_poller.py`, `.env.example`, `.env` (gitignored, not committed)
- `AGENTES.md` (correction)
- `docs/runbooks/hermes-bridge-token-rotation.md` (new)
- `feature_list.json` (`active` pointer)
- `openspec/changes/hermes-bridge-token-production-hardening/` (proposal, design, specs, tasks)
- `progress/impl_hermes-bridge-token-production-hardening.md` (this file)
- Railway production env var `HERMES_BRIDGE_TOKEN` (infrastructure, not a repo file)

## Next step

First reviewer pass returned CHANGES_REQUESTED (missing `.env.example` fix + this missing paper
trail — both addressed above). Awaiting re-review before Section 10 (commit/push) and Section 11
(Stage 11 deployment report + archive).
