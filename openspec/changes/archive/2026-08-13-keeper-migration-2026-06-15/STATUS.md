# Keeper → Bitwarden Migration — STATUS & RUNBOOK

**Last updated:** 2026-06-15
**Owner:** Juan David / Contexia Infra
**Overall status:** ✅ Deployed & verified (GATE 2). Keeper deletion (T14) on HOLD until 2026-07-04.

This is the single source of truth for the current state of the migration.
For task-by-task detail see `tasks.md`; for audit/deployment evidence see `reports/`.

---

## 1. TL;DR

- Secrets were migrated from **Keeper** (legacy password manager) to **Bitwarden Cloud** (US region).
- A backend **secrets provider** + **health endpoint** were added to prove Bitwarden connectivity.
- The endpoint is **live and healthy** on the **dc78** Railway backend.
- **Keeper has NOT been deleted yet** — held as read-only backup until 2026-07-04 (Phase 2 stability gate). A scheduled reminder exists for that date.

---

## 2. What is live, and where

| Item | Value |
|------|-------|
| Health endpoint | `https://antigravity-app-production-dc78.up.railway.app/api/v1/secrets/health` |
| Backend service | `antigravity-app-production-dc78` (Railway) |
| Deploy branch | `deploy-prod` (Railway dc78 auto-deploys from it) |
| Active commit | `3432976` (and later doc commits) |
| Provider | `bitwarden-cloud` |
| Bitwarden region | **US** — `https://vault.bitwarden.com` |
| Expected response | `{"status":"healthy","provider":"bitwarden-cloud","latency_ms":~7000,"vault_url":"https://vault.bitwarden.com"}` |

### ⚠️ Important routing fact
`contexia.online/api/v1/*` is rewritten by **Vercel** to the **175a** backend
(`antigravity-app-production-175a`), per `vercel.json` line ~77. The secrets
endpoint was deployed to **dc78**, so it is **NOT reachable on contexia.online** —
only on the dc78 Railway domain above. This is expected and does not block the
migration. Exposing it on the canonical domain is an optional follow-up (see §7).

---

## 3. How to verify (quick check)

```cmd
curl https://antigravity-app-production-dc78.up.railway.app/api/v1/secrets/health
```

- `{"status":"healthy",...}` → all good.
- `{"status":"unhealthy",...,"error":"..."}` → read the error; see §6 troubleshooting.
- `{"detail":"Not Found"}` → you're hitting the wrong host (e.g. contexia.online) or a deploy is mid-rollout.

> Tip: paste the command on a single line. Pasting it twice concatenates into a
> bad URL and returns `{"detail":"Not Found"}` for the first (malformed) half.

---

## 4. Configuration

### Railway env vars (service `dc78` → Variables)
| Variable | Value |
|----------|-------|
| `SECRETS_BACKEND` | `bitwarden` |
| `BW_VAULT_URL` | `https://vault.bitwarden.com` |
| `BW_CLIENT_ID` | personal API key client id (`user.<guid>`) |
| `BW_CLIENT_SECRET` | personal API key client secret (**rotated 2026-06-15**) |
| `BW_MASTER_PASSWORD` | Bitwarden account master password |

Secret values live in local `.env.local` (git-ignored) and in the Bitwarden vault
itself. **Never commit them.** The Bitwarden API key is at:
Bitwarden web → Account Settings → Security → Keys → **API Key**.

> The `client_secret` originally in `.env.local` was **stale** and rejected by
> Bitwarden. It was replaced with the current value from the web vault. Make sure
> `.env.local` holds the working value.

### Code
| File | Role |
|------|------|
| `apps/backend/core/secrets_provider.py` | Abstract `SecretsProvider` + `BitwardenCloudProvider` + `VaultwardenProvider` (Phase 2) + `get_provider()` factory |
| `apps/backend/api/endpoints/secrets_endpoints.py` | `GET /secrets/health` route |
| `apps/backend/api/__init__.py`, `api/endpoints/__init__.py` | package markers |
| `apps/backend/main.py` | registers secrets router (inside try/except) |
| `apps/backend/Dockerfile` | single-stage build + installs native Bitwarden CLI |

---

## 5. How the health check works (flow)

Each request to `/secrets/health` runs, via the `bw` CLI in the container:
1. `bw login --apikey` — reads `BW_CLIENTID`/`BW_CLIENTSECRET` from env (API-key auth).
2. `bw unlock --passwordenv BW_PASSWORD --raw` — unlocks vault with master password → session token.
3. `bw sync` — confirms connectivity. Session cached ~1h in-process.

Returns `healthy` on success, `unhealthy` + error string on any failure.

---

## 6. Defects fixed during bring-up (history)

The endpoint failed on first deploy. Six real defects were fixed:

| # | Commit | Defect | Fix |
|---|--------|--------|-----|
| 1 | `a433f3a` | secrets router not registered in `main.py` | include the router |
| 2 | `bdba87e` | missing `__init__.py` in `api/`, `api/endpoints/` | add package markers |
| 3 | `bbc2e53` | import `apps.backend.core` crashed startup (Railway runs from `apps/backend`) | use `from core.secrets_provider` |
| 4 | `bdddd2e` | Dockerfile had no `bw` CLI; `build-essential` hung builds ~33 min | single-stage + native bw binary (deps ship as wheels, no compiler needed) |
| 5 | `287f1ac` | `_auth` piped creds to stdin & never unlocked the vault | login via env vars + `bw unlock` |
| 6 | `3432976` | `bw sync` prints plain text; `json.loads` crashed | tolerant parse → `{"raw": <text>}` |

Plus: the persistent `contexia.online` 404 was the Vercel→175a routing (§2), and
the credential rejection was a **stale `client_secret`** (§4).

### Troubleshooting map
| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `{"detail":"Not Found"}` | hitting contexia.online, or rollout in progress | use dc78 host; wait for deploy |
| `error: "... client_id or client_secret is incorrect"` | stale/wrong API key, or wrong region | re-copy API key from web vault; confirm US region |
| `error: "... bw unlock failed ..."` | wrong master password | verify `BW_MASTER_PASSWORD` |
| `error: "Expecting value: line 1 ..."` | non-JSON bw output | already fixed (commit `3432976`) |
| `error: "... not logged in"` | auth didn't complete | check env vars are set on dc78 |

---

## 7. Known debt / follow-ups (non-blocking)

1. **Canonical-domain exposure:** to serve the endpoint on `contexia.online`, either
   repoint `vercel.json` `/api/v1` to dc78, or deploy the secrets code to the 175a
   backend (its branch). Verify env-var parity before repointing.
2. **Latency ~7–10 s/call:** every call does a full `bw login`+`unlock`+`sync`.
   Optimize by caching the session token across requests, or rewrite
   `BitwardenCloudProvider` to use the Bitwarden REST API (no CLI subprocess).
3. **Architecture note:** the live app reads its runtime keys (LLM, Supabase, etc.)
   from **Railway env vars**, not from Bitwarden. The secrets provider is
   validation/management infrastructure. Deleting Keeper does not affect production.
4. **`.env.local`:** keep it updated with the working (rotated) `client_secret`.

---

## 8. Remaining work — T14 (Keeper deletion, GATE 3)

**Status: HOLD until 2026-07-04.** A scheduled reminder will walk through this.

Before deleting Keeper:
- [ ] Health still `healthy` (§3)
- [ ] Bitwarden backup taken: `bw export --format encrypted_json --output bitwarden-backup-<date>.json`
- [ ] `bw list items` shows ~330 items
- [ ] Keeper kept read-only since migration (no new secrets added to it)

Then:
- [ ] **2026-07-04** — delete the Keeper vault **manually in Keeper's web/app** (NOT a `bw` command; Keeper is the legacy manager being retired). Irreversible.
- [ ] Update `reports/T14-KEEPER-DELETION-APPROVAL-2026-06-15.md` and the migration memory.
- [ ] **2026-07-15** — delete the 30-day backup export.

---

## 9. Phase 2 (optional, deferred to 2026-07-04)

Self-hosted **Vaultwarden** config already exists in the repo
(`docker-compose.vaultwarden.yml`, `railway.vaultwarden.toml`, `Dockerfile.vaultwarden`,
`.env.vaultwarden.example`). The provider abstraction (`VaultwardenProvider`) means
switching backends is a config change (`SECRETS_BACKEND=vaultwarden`). Decide at the
2026-07-04 gate whether to stay on Bitwarden Cloud or move to Vaultwarden.

---

## 10. Key references

- OpenSpec change: `openspec/changes/keeper-migration-2026-06-15/`
- Audit report: `reports/T13-HEALTH-AUDITS-2026-06-15.md`
- Deployment report: `reports/2026-06-15-deployment.md`
- T14 decision: `reports/T14-KEEPER-DELETION-APPROVAL-2026-06-15.md`
- Routing: `vercel.json`
