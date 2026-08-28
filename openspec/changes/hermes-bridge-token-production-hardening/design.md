## Context

`apps/backend/presentation/sell_machine_endpoints.py` exposes 5 operator-task bridge routes that
the local Hermes/Manus poller (`apps/hermes-manus-poller/`) polls and reports back to
(`GET /tasks/pending`, `POST /tasks`, `POST /campaigns/{id}/dispatch`, `POST /tasks/{id}/status`,
`POST /tasks/{id}/result`). They are guarded by `require_hermes_bridge_token`
(`sell_machine_endpoints.py:44-56`), which reads `settings.HERMES_BRIDGE_TOKEN`
(`apps/backend/config.py:81`, default `None`) and no-ops when unset — the spec at
`openspec/specs/hermes-manus-execution-bridge/spec.md` documents this as intentional, optional
behavior.

Live verification (this session, against the canonical Railway service `-175a`) confirmed
`HERMES_BRIDGE_TOKEN` is not set in production today, so all 5 routes are open. Separately, reading
`apps/hermes-manus-poller/backend_client.py` shows the poller does not send a bearer token at all —
it signs a JWT (`sign_tenant_jwt`, HS256, 15-minute expiry) keyed by `CONTEXIA_JWT_SECRET`, a
different, also-unset setting, and only attaches an `Authorization` header when that signing
succeeds. No code anywhere in `sell_machine_endpoints.py` verifies a JWT — the two mechanisms were
built independently and were never reconciled. Turning on `HERMES_BRIDGE_TOKEN` today, without
touching the poller, would make every poller request fail with 401 and silently stall the
`operator_tasks` queue Sell Machine's content pipeline depends on.

## Goals / Non-Goals

**Goals:**
- Close the live unauthenticated write surface on the 5 operator-task bridge routes.
- Do it without breaking the currently-healthy `ContexiaHermesManusPoller` scheduled task.
- Leave exactly one authentication mechanism for this bridge, matching what the spec already
  documents, so a future reader isn't left guessing which of two codepaths is real.

**Non-Goals:**
- Not introducing per-caller identity, token expiry, or rotation tooling — this bridge has exactly
  one trusted caller (the local poller), so a static shared secret is proportionate.
- Not touching `agents_endpoints.py`'s tenant-scoping gap or any other pre-existing tech debt —
  out of scope per the parent plan's explicit deferral.
- Not changing the 5 endpoints' tenant-resolution logic — it is already correct per the existing
  spec; only the layer in front of it changes.

## Decisions

**Decision 1 — Canonicalize on the bearer-token mechanism (`HERMES_BRIDGE_TOKEN`), not the JWT one.**
The backend-side guard (`require_hermes_bridge_token`) is already fully implemented, uses
`hmac.compare_digest` (timing-safe), and matches exactly what `hermes-manus-execution-bridge/spec.md`
already describes as the intended contract. The JWT path (`sign_tenant_jwt` /
`CONTEXIA_JWT_SECRET`) has no corresponding backend verification code anywhere in the repo — building
one now would mean writing new JWT-verification logic for a bridge with a single trusted caller,
pure added surface for no benefit. Alternative considered: verify the poller's JWT via a new
dependency mirroring `core/deps.py::_verify_supabase_token`. Rejected — that helper verifies
Supabase-issued tokens against Supabase's own JWKS; the poller's self-signed JWT is a different,
unrelated credential, and building parallel verification logic for a single-caller bridge is
disproportionate.

**Decision 2 — Remove the poller's JWT-signing path instead of leaving it dormant.**
`sign_tenant_jwt`/`CONTEXIA_JWT_SECRET` in `apps/hermes-manus-poller` produces a credential nothing
ever checks. Per this repo's own precedent (Phase 3B's `core/rbac.py` bundle — dead code left in
place became a source of confusion for later sessions), delete this path rather than leave two
authentication mechanisms sitting side by side. `apps/hermes-manus-poller/backend_client.py::_headers()`
is updated to send `Authorization: Bearer {settings.HERMES_BRIDGE_TOKEN}` when that setting is
non-empty, and no header when it's empty — mirroring the backend's own "no-op when unset" contract
so local development without the token still works unauthenticated, exactly as today.

**Decision 3 — Sequence the rollout so the poller never has a code gap.**
Ship and verify the poller's new header-sending code first, while `HERMES_BRIDGE_TOKEN` is still
unset in Railway (inert change — the guard still no-ops, so behavior is unchanged). Only after
confirming the poller still ticks cleanly with the new code, generate the real secret and set it in
both Railway and the poller's local `.env` in the same maintenance window. This avoids the failure
mode identified in the proposal (guard turned on server-side before the poller can satisfy it).

## Risks / Trade-offs

- **[Risk] Railway env var change requires a restart to take effect, and the poller's local `.env`
  must be updated in the same window** → **Mitigation**: Decision 3's sequencing (poller code ships
  inert first); tasks.md includes an explicit live-verification step (unauthenticated call → 401,
  next poller tick → still succeeds) before the change is considered done, not just "env var is set."
- **[Risk] Static shared secret has no expiry — a leak is valid until manually rotated** →
  **Mitigation**: proportionate given single trusted local caller; document a one-paragraph manual
  rotation runbook (generate in Bitwarden → update Railway → update poller `.env` → restart poller)
  as part of this change's tasks, not built as tooling.
- **[Risk] Rollback if something breaks mid-rollout** → unsetting `HERMES_BRIDGE_TOKEN` in Railway
  and redeploying/restarting the service immediately restores today's open behavior (the guard's
  own documented no-op path) — no code revert needed for an emergency rollback.
- **[Trade-off] Deleting the JWT-signing code is a small, unrelated-looking diff inside a security
  change** — accepted deliberately (Decision 2) rather than leaving a second, unused, confusing
  auth mechanism in a bridge that a later session (like this one) would otherwise have to
  re-investigate from scratch, as happened this session.

## Migration Plan

1. Update `apps/hermes-manus-poller/backend_client.py` to send `Authorization: Bearer <token>` from
   `settings.HERMES_BRIDGE_TOKEN` when configured; remove `sign_tenant_jwt` and the
   `CONTEXIA_JWT_SECRET` setting from `apps/hermes-manus-poller/config.py`.
2. Deploy/restart the poller locally with `HERMES_BRIDGE_TOKEN` still unset — confirm the next
   scheduled tick still succeeds unauthenticated (no regression).
3. Generate a new secret value, store it in Bitwarden (name only documented here; value never
   committed).
4. Set `HERMES_BRIDGE_TOKEN` in Railway (`-175a`) and redeploy/restart.
5. Set the identical value in the poller's local `.env` and restart the `ContexiaHermesManusPoller`
   scheduled task.
6. Live-verify: `curl` to `GET /api/v1/sell-machine/tasks/pending` with no header → 401; the
   poller's next tick claims/completes a task successfully (confirmed via `agent_operations` rows
   or task-status transitions).

**Rollback**: unset `HERMES_BRIDGE_TOKEN` in Railway and restart the service — restores the
documented no-op/open behavior immediately, no code changes needed.

## Open Questions

None — both technical decisions (mechanism choice, rollout sequencing) are resolved above.
