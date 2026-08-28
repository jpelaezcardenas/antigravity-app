## 1. Poller: switch to bearer-token auth, remove dead JWT path

- [x] 1.1 Write a failing test for `apps/hermes-manus-poller` confirming `_headers()` sends
      `Authorization: Bearer <token>` when `HERMES_BRIDGE_TOKEN` is set, and no `Authorization`
      header when it is unset.
- [x] 1.2 In `apps/hermes-manus-poller/backend_client.py`, replace `_headers()`'s call to
      `sign_tenant_jwt()` with a direct read of `settings.HERMES_BRIDGE_TOKEN`; remove the
      `sign_tenant_jwt` function.
- [x] 1.3 In `apps/hermes-manus-poller/config.py`, remove the `CONTEXIA_JWT_SECRET` setting and add
      `HERMES_BRIDGE_TOKEN` (default empty string), matching the backend's setting name.
- [x] 1.4 Remove the now-unused `python-jose` import/usage in `backend_client.py` if nothing else in
      that file depends on it. (Confirmed `jose`/`jwt` had zero remaining references anywhere in
      the poller — also removed the now-dead `python-jose[cryptography]` line from
      `requirements.txt`.)
- [x] 1.5 Run the poller's test suite; confirm the new test from 1.1 passes and nothing else broke.
      (47/47 passed.)

## 2. Backend: confirm guard behavior unchanged (no code change expected)

- [x] 2.1 Read `apps/backend/presentation/sell_machine_endpoints.py::require_hermes_bridge_token`
      and confirm it already matches the MODIFIED spec exactly (it does per this session's
      investigation) — no code change here, just a documented confirmation in the task, so a future
      reviewer doesn't assume this task group was skipped. (Re-verified at apply time,
      lines 44-56, unchanged.)

## 3. Deploy poller change inert (token still unset)

- [x] 3.1 Deploy the updated `apps/hermes-manus-poller` locally with `HERMES_BRIDGE_TOKEN` left
      unset in its `.env`. (Code already saved to disk; no separate deploy step — the scheduled
      task invokes a fresh `python main.py` each tick, per `run_poller.ps1`, so it's live
      immediately.)
- [x] 3.2 Restart the `ContexiaHermesManusPoller` scheduled task; confirm its next tick completes
      successfully with no `Authorization` header sent (inert — matches today's behavior). (No
      restart needed — one-shot task, `MultipleInstances=IgnoreNew`. Confirmed via
      `logs/poller-20260828.log`: tick at 08:15:16 ran with the new code, `HTTP/1.1 200 OK`,
      `Tick complete: {'resolved': 0, 'dispatched': 0, 'pending_seen': 0, 'skipped': 0}` — no
      regression.)

## 4. Generate and configure the production secret

- [x] 4.1 Generate a new random token value; store it in Bitwarden under a clearly named entry (do
      not write the value into any repo file, doc, or report — name only, per ARCHITECTURE.md
      Decision #12). (Generated via `secrets.token_urlsafe(32)`. `bw` CLI hung/unreachable from
      this shell — known environment limitation, not this change's fault. Value was NOT written to
      any repo file; reported directly to the founder in chat so they can add it to Bitwarden
      themselves. Entry name to use: `Hermes Bridge Token (production)`.)
- [x] 4.2 Set `HERMES_BRIDGE_TOKEN` on the canonical Railway backend service (`-175a`) to that
      value; redeploy/restart the service. (Set via Railway MCP `railway_set_variable`
      with `skip_deploys=false`; new deployment `d7eeeed3` — status SUCCESS, `/api/v1/health`
      confirmed healthy post-deploy.)
- [x] 4.3 Set the identical value in the poller's local `.env` (`HERMES_BRIDGE_TOKEN`); restart the
      `ContexiaHermesManusPoller` scheduled task. (Appended surgically to `.env` — verified
      `DRY_RUN=true`, owned by the parallel Envigado GTM thread, was left untouched. No restart
      needed, one-shot task per tick.)

## 5. Live verification (Stage 11 prerequisite)

- [x] 5.1 `curl` `GET https://antigravity-app-production-175a.up.railway.app/api/v1/sell-machine/tasks/pending`
      with no `Authorization` header — confirm 401. (Confirmed: `{"detail":"missing or malformed
      Authorization header"}`, HTTP 401. Also confirmed a wrong-token case returns 401
      `{"detail":"invalid bridge token"}` — not required by this task but a good extra check.)
- [x] 5.2 `curl` the same endpoint with `Authorization: Bearer <the configured token>` — confirm 200.
      (Confirmed: HTTP 200, `[]`.)
- [x] 5.3 Confirm the poller's next scheduled tick after step 4.3 completes successfully (check
      Windows Scheduled Task last-run result, and/or a new `agent_operations` row with
      `agent_name="hermes-bridge"`). (Confirmed via `logs/poller-20260828.log`: tick at 08:23:12
      sent the real bearer token and got `HTTP/1.1 200 OK`, `Tick complete` with no errors.)
- [x] 5.4 Confirm no other caller of the 5 operator-task endpoints exists beyond the poller (grep
      the repo for `sell-machine/tasks` and `sell-machine/campaigns` call sites) — if any other
      caller is found, it must also be updated before this task is considered done. (Grep found
      `contexia-app/lib/sell-machine-api.ts` calls `/sell-machine/campaigns` (POST, create) and
      `/sell-machine/campaigns` (GET, list) — different routes from the 5 protected ones, admin-
      session-authenticated, unaffected by this change. No other caller found.)

## 6. Update living docs (same change, per CLAUDE.md §7)

- [x] 6.1 If `ARCHITECTURE.md` or any other canon doc still describes the bridge's authentication as
      unconfigured/no-op in production, correct it in this same change. (`ARCHITECTURE.md` had no
      stale claim. `AGENTES.md` line ~345-352 said "fail-open until the env var is set" — corrected
      to state the token is live/enforced in production as of 2026-08-28, referencing this change.)
- [x] 6.2 Add a one-paragraph manual rotation runbook note (generate in Bitwarden → update Railway
      → update poller `.env` → restart poller) to `docs/runbooks/` (or the nearest existing runbook
      location) for future rotation. (`docs/runbooks/hermes-bridge-token-rotation.md` created.)

## 7. Cleanup

- [x] 7.1 Confirm no remaining references to `CONTEXIA_JWT_SECRET` or `sign_tenant_jwt` exist
      anywhere in `apps/hermes-manus-poller/` (grep to verify). **CORRECTED (reviewer caught this):**
      first pass wrongly scoped the grep to `*.py` only and missed `apps/hermes-manus-poller/.env.example:17`,
      which still had `CONTEXIA_JWT_SECRET=` with a stale "open today" comment — fixed to
      `HERMES_BRIDGE_TOKEN=` with an accurate comment. Re-ran grep with no file-type filter across
      the whole directory: zero matches now, genuinely confirmed clean.

## 8. Testing

- [x] 8.1 Backend: confirm existing tests for `sell_machine_endpoints.py` (if any) still pass
      unchanged — no backend code changed, but re-run to be sure nothing else regressed.
      (32/32 passed, including `TestHermesBridgeToken`'s 4 pre-existing scenarios.)
- [x] 8.2 Poller: full local test suite green after Section 1's changes. (47/47 passed.)

## 9. Stage 9 — Reviewer gate

- [x] 9.1 Reviewer validates against `ARCHITECTURE.md`, `hermes-manus-execution-bridge/spec.md`
      (post-merge), and `DEPLOYMENT_STAGE/CHECKPOINTS.md` per `HARNESS.md`'s leader→implementer→
      reviewer loop — writes `progress/review_hermes-bridge-token-production-hardening.md`.
      (First pass: CHANGES_REQUESTED — `.env.example` stale JWT reference + missing impl paper
      trail, both fixed. Second pass: **APPROVED**.)

## 10. Commit + push

- [ ] 10.1 Commit the poller code changes and doc updates (Sections 1, 6) to `main`.

## 11. Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Backend URL: https://antigravity-app-production-175a.up.railway.app
- This change's only frontend-visible surface is none (backend + local poller only) — no Vercel
  deploy required.

Tasks:
- [ ] 11.1 git commit + push to main (poller code + doc corrections).
- [ ] 11.2 Railway env var (`HERMES_BRIDGE_TOKEN`) set and service redeployed/restarted (Section 4).
- [ ] 11.3 Production URL: live verification from Section 5 passed (401 unauthenticated, 200
      authenticated, poller tick succeeds).
- [ ] 11.4 Create report: `openspec/changes/hermes-bridge-token-production-hardening/reports/YYYY-MM-DD-deployment.md`.
