# Step 12 Report - Manual Endpoint Testing with curl

- Date: 2026-07-23
- Change: chatwoot-hermes-taty-bridge

## Environment / blocker

**Docker is not installed on this laptop** (confirmed: `docker --version` fails both natively on
Windows and inside WSL Ubuntu). This blocks Task 11.3 (bringing up the Chatwoot stack) entirely, and
transitively blocks the parts of this step that require a real, running Chatwoot instance: 12.3
(reply actually lands in a Chatwoot conversation), 12.5 (`bot_off` label toggled via the real
Chatwoot API), and 12.8 (cleaning up test data in Chatwoot).

What follows is everything that genuinely IS testable without a live Chatwoot — the bridge itself,
started against the real, running local Hermes Gateway.

## Commands and Results

### 12.1 — Bridge started against the real Hermes Gateway
```
HERMES_GATEWAY_URL=http://localhost:8642 HERMES_API_KEY=<local dev key> HERMES_MODEL=contexia \
WEBHOOK_TOKEN=test-webhook-token-local CHATWOOT_URL=http://localhost:3020 PORT=8090 \
uvicorn main:app --host 127.0.0.1 --port 8090
```
`HERMES_MODEL=contexia` was used (not `taty-v1`) because that is the profile the local Hermes
Gateway is actually serving right now (`GET /v1/models` confirms this — see below); the model name
is a plain config value, not hardcoded anywhere in the bridge, per design.md decision 8.

### 12.2 — `GET /` health check
```
curl http://127.0.0.1:8090/
```
→ `200 {"status":"ok","service":"chatwoot-hermes-bridge","hermes_models":{"data":[{"id":"contexia",...}]}}`
— confirms the bridge genuinely reached the real Hermes Gateway and logged its liveness, not a mock.

### 12.4 — Outgoing message is skipped (no reply loop)
```
curl -X POST "http://127.0.0.1:8090/webhook?token=test-webhook-token-local" -d '{"event":"message_created","message_type":"outgoing","conversation":{"id":1}}'
```
→ `200 {"status":"skipped"}`.

### 12.6 — Missing/wrong `WEBHOOK_TOKEN`
```
curl -X POST "http://127.0.0.1:8090/webhook?token=wrong-token" -d '...'
curl -X POST "http://127.0.0.1:8090/webhook" -d '...'   # no token at all
```
→ both `401 {"detail":"Invalid webhook token"}`.

### Bonus (beyond the original 12.x list, tested since it was free to check): private note is skipped
```
curl -X POST "...?token=test-webhook-token-local" -d '{"event":"message_created","message_type":"incoming","private":true,...}'
```
→ `200 {"status":"skipped"}`.

### Bonus: genuine incoming message returns instantly, background pipeline runs after
```
curl -X POST "...?token=test-webhook-token-local" -d '{"event":"message_created","message_type":"incoming","private":false,"content":"Hola Taty",...}'
```
→ `200 {"status":"processing_started"}` (returned before any downstream call — confirms
`BackgroundTasks` scheduling, not an inline `await`, per the webhook handler's design).
Background task then correctly attempted to reach Chatwoot at `localhost:3020` (which doesn't exist
without Docker), got `httpx.ConnectError: All connection attempts failed`, logged it, and the
**server process survived** (confirmed with a follow-up `GET /` returning `200` normally) — FastAPI
isolates `BackgroundTasks` failures per-request, this is not a crash.

## Not testable this session (blocked by 11.3 — Docker not installed)

- 12.3: reply actually landing in a real Chatwoot conversation.
- 12.5: `bot_off` label toggled via the real Chatwoot API and re-verified.
- 12.8: cleanup of test data in Chatwoot (N/A — no real Chatwoot conversation/lead was created;
  the one `crm_leads` write attempt inside the background task never reached the backend either,
  since it failed earlier at the Chatwoot history-fetch step in this particular test run).

## Cleanup

- Bridge test server stopped; port 8090 confirmed free afterward.
- No real Chatwoot, CRM, or Hermes state was mutated (Hermes was only queried via `GET /v1/models`,
  a read).

## Outcome

- Step 12 status: **PARTIAL PASS, blocked on Docker not being installed for the rest.** Everything
  testable without a live Chatwoot (routing, webhook auth, loop-prevention filters, real Hermes
  connectivity, background-task isolation) is verified live. Task 11.3/12.3/12.5/12.8 remain open
  until Docker Desktop is installed on this laptop.
