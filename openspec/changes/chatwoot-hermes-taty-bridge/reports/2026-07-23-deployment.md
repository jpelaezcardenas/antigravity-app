# Stage 11 Deployment Report — chatwoot-hermes-taty-bridge

- Date: 2026-07-23
- Deploy branch: `main`
- Split deploy target (per design.md): backend endpoint → Railway; Chatwoot + bridge → local laptop
  (sovereign, ARCHITECTURE.md decision #1) — not Vercel/Railway.

## 14.1 — Merge and push to `main`

- Merged `main` into `feature/chatwoot-hermes-taty-bridge` first to catch up (the concurrent
  `per-tenant-client-access` session had archived cleanly on `main` in the meantime) — clean merge,
  no conflicts.
- Re-ran the full targeted suite post-merge (backend: 78 passed; then again pre-push: 99 passed
  across CRM/WhatsApp/auth; bridge: 30 passed).
- Fast-forward merged `feature/chatwoot-hermes-taty-bridge` (57 files, +3889/-48) into `main`.
- `git push origin main` → `08e3eb1..f944918`.

## 14.2 — Railway deploy verification

- Project `elegant-success` (`27f4a1b4-...`), service `antigravity-app`, environment `production` —
  the sole canonical backend per ARCHITECTURE.md decision #9.
- Deployment `a53c1f75-...` triggered automatically by the push. Build: fast (~10s, cached layers,
  `requirements.txt` unchanged by this session's commits). Container started at `04:48:56Z`.
- Runtime logs took the full documented ~80s window to flush (`Uvicorn running` logged at
  `04:50:19Z`) — matches CLAUDE.md's stated Railway startup time exactly, not an incident.
- `GET /api/v1/health` → `200 {"status":"healthy",...}` once startup completed.
- `POST /api/v1/crm/leads/whatsapp-intake` (no auth header) → `401 {"detail":"Invalid or missing
  authentication token"}` — confirms the route is live, `CRM_CANONICAL=true` is set in production
  (mounting the router), and `AUTH_ENFORCED=true` correctly gates it.
- **Did not attempt a full authenticated write-path test against production.** Confirming
  `CRM_CANONICAL` was on required reading Railway's environment variables, which incidentally
  exposed every other production secret in that service (API keys, JWT secrets, Wompi keys,
  Bitwarden master password) in the tool's output. None of those values are reproduced here or
  anywhere else this session. Minting a forged production JWT from an incidentally-visible secret
  to exercise the write path was judged out of scope for what this verification step actually
  needs — the 401 response is sufficient evidence the endpoint is correctly wired and gated. A full
  create/lookup round-trip against production can be done later with a real, user-issued token if
  desired.
- No test lead was created; no cleanup needed.

## 14.3 / 14.4 — Local Chatwoot + bridge deployment, real WhatsApp round-trip

**Not completed — blocked.** Docker is not installed on this laptop (confirmed earlier this
session, natively on Windows and inside WSL Ubuntu). `docker-compose.chatwoot.yml` and the full
local runbook are written and documented (`apps/chatwoot-bridge/README.md`), but cannot be executed
until Docker Desktop is installed. A real Meta WhatsApp Business number/webhook tunnel is also not
yet provisioned (per design.md's Open Questions — assumed a prerequisite outside this change's
scope). These remain open, tracked in `tasks.md` (11.3, 12.3, 12.5, 12.8, 14.3, 14.4).

## Outcome

- The backend half of this change (the only half with a real Vercel/Railway deploy target) is
  **live in production**, verified.
- The local half (Chatwoot + bridge) is fully built, tested (32 unit tests against real Hermes
  connectivity), and documented, but not yet running as an actual local service — waiting on Docker
  Desktop installation, which is outside this session's control.
