# Chatwoot <-> Hermes (Taty) Bridge

Thin, stateless FastAPI service that bridges a self-hosted Chatwoot WhatsApp
inbox to the local Hermes Gateway (Taty). See
`openspec/changes/chatwoot-hermes-taty-bridge/design.md` for the full
architecture and decisions this implementation follows.

Runs **locally only** (this laptop, alongside Hermes Gateway) — it is never
deployed to Railway/Vercel (ARCHITECTURE.md decision #1 applies transitively:
Taty's brain is local Hermes, so the inbox/bridge must be local too).

## What it does

```
Chatwoot (WhatsApp) --webhook--> bridge --HTTP--> Hermes Gateway (taty-v1)
                                    |
                                    +--HTTP--> Contexia backend (CRM lead intake)
```

1. `POST /webhook` receives every Chatwoot event.
2. Filters for genuine incoming customer messages (not private notes, not
   outgoing/echoed bot replies — loop prevention) and checks the `bot_off`
   label for human-in-the-loop pause.
3. Background pipeline: CRM lead intake (find-or-create; new leads get their
   Chatwoot contact tagged `tipo_lead`/`estado: "nuevo"` — no company
   onboarding is triggered here, see design.md decision 5) -> fetch recent
   conversation history -> call Hermes's OpenAI-compatible
   `/v1/chat/completions` -> post the reply back to Chatwoot.
4. Audio attachments get a fixed Spanish "please send text" fallback instead
   of a transcription attempt (no GPU on this laptop — phase 2 non-goal).
5. Any dependency failure (CRM, Hermes) degrades gracefully — the customer
   always gets some reply, never silence (design.md decision 7).

## Environment variables

See `.env.example` for the full list with defaults. All secrets default to
empty strings and fail closed (no hardcoded fallback secret is ever used).

| Var | Purpose |
|---|---|
| `CHATWOOT_URL` | Base URL of the local Chatwoot instance (default port `:3020`) |
| `CHATWOOT_API_TOKEN` | Agent bot API access token (Chatwoot Profile Settings -> Access Token) |
| `CHATWOOT_ACCOUNT_ID` | Chatwoot account id (default `1`) |
| `HERMES_GATEWAY_URL` | Local Hermes Gateway base URL (default `http://localhost:8642`) |
| `HERMES_MODEL` | Hermes profile/model name to request (default `taty-v1`) — configurable, never hardcoded elsewhere |
| `HERMES_API_KEY` | Bearer token Hermes Gateway expects (`API_SERVER_KEY` in Hermes's own config) |
| `CONTEXIA_API_URL` | Contexia backend base URL, including `/api/v1` (e.g. `http://127.0.0.1:8080/api/v1`) |
| `CONTEXIA_JWT_SECRET` | Shared secret matching the backend's `JWT_SECRET` — used to sign the bridge's tenant JWT |
| `PAUSE_LABEL` | Chatwoot conversation label that pauses the AI (default `bot_off`) |
| `MAX_HISTORY` | Max prior messages sent to Hermes as context (default `10`) |
| `WEBHOOK_TOKEN` | Shared token Chatwoot's webhook URL must present (query param `token` or `X-Webhook-Token` header) |
| `PORT` | Port the bridge listens on (default `8090`) |
| `LOCAL_WHISPER_URL` | Reserved, unused today (phase 2 — voice transcription) |

## Local startup sequence

```bash
# 1. Chatwoot stack (docker-compose.chatwoot.yml, repo root)
docker compose -f docker-compose.chatwoot.yml up -d

# 2. Hermes Gateway, with the taty-v1 profile explicitly active
wsl -d hermes-ws -- hermes -p taty-v1 gateway run

# 3. The bridge itself
cd apps/chatwoot-bridge
pip install -r requirements.txt
cp .env.example .env   # then fill in the secrets
uvicorn main:app --port 8090
```

## Port map

| Service | Port |
|---|---|
| Next.js dev / Hermes Workspace UI | `:3000` |
| Chatwoot web | `:3020` |
| Local backend dev | `:8080` |
| This bridge | `:8090` |
| Hermes Gateway | `:8642` |

## Troubleshooting

- **Wrong Hermes profile active**: `GET /` (health check) logs the result of
  `GET {HERMES_GATEWAY_URL}/v1/models` — if the returned model list doesn't
  include `taty-v1` (or whatever `HERMES_MODEL` is set to), a different
  profile is currently serving `:8642`. Restart Hermes with
  `hermes -p taty-v1 gateway run`.
- **`401` on every webhook call**: `WEBHOOK_TOKEN` mismatch between this
  service's `.env` and the token configured on the Chatwoot webhook URL
  (`?token=...` or `X-Webhook-Token` header).
- **Customer gets a generic apology instead of a real reply**: Hermes timed
  out (60s) or errored — check the bridge's logs for the traceback logged by
  `hermes_client.invoke_chat_completion`.
- **New WhatsApp contacts aren't appearing as CRM leads**: check
  `CONTEXIA_API_URL` and `CONTEXIA_JWT_SECRET` — a failed intake call is
  logged but swallowed by design (the conversation still gets an AI reply),
  so look at the bridge's logs, not the webhook response.
- **New leads aren't getting a company/workspace onboarded automatically**:
  this is expected, not a bug — the bridge deliberately does not call company
  onboarding on first WhatsApp contact (design.md decision 5). That flow
  belongs to a later funnel stage (a closed B2B sale), not a lead's first
  message.

## Tests

```bash
cd apps/chatwoot-bridge
pytest tests -v
```

All external calls (Chatwoot, Hermes, backend) are mocked with `respx` — no
real network calls are made by the test suite.
