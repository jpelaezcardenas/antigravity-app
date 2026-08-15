## Why

Two independent implementations of "Taty answers a WhatsApp lead" exist in this repo, and only one
of them can be the live channel — Meta allows a single callback URL per app.

- **Route A** — `POST /api/v1/channels/whatsapp/webhook`
  (`presentation/whatsapp_endpoints.py`, gated by `WHATSAPP_CANONICAL`) → `services/taty_lead_router.py`.
  This is the actual sales machine: deterministic intent classification, `UMBRAL_RENTA_COP`
  thresholds, Wompi payment-link generation (`generate_wompi_link`, real and implemented),
  payment-status verification against `crm_wompi_transactions`, KB/RAG grounding via
  `retrieve_similar`, and document intake.
- **Route C** — Chatwoot (local) → `apps/chatwoot-bridge` → Hermes `taty-v1`. The bridge is by its
  own docstring a *"thin, stateless transport layer… no business logic is duplicated"*, and it
  keeps that promise: `main.py::process_incoming_message` sends conversation history to
  `hermes_client.invoke_chat_completion` and returns free text. **It never touches
  `taty_lead_router`.**

Route C was selected as the channel architecture (Chatwoot gives the human accountant a real inbox
with history, assignment, and the `bot_off` HITL pause — required by the Entidad A / Entidad B
separation). But adopting Route C as-is would ship a bot that **cannot quote a price, cannot issue
a Wompi payment link, cannot confirm a payment, and cannot ground an answer in the Estatuto
Tributario** — and would strand `wompi-production-go-live`'s now-live production credentials
against unreachable code.

The fix is not to pick a route. It is to stop having two brains: **`taty_lead_router` is the
logic, and Hermes becomes the LLM behind that router rather than a parallel one.** Which door the
message comes through (the Railway webhook, or Chatwoot via the bridge) then stops mattering —
both reach the same brain.

Separately, `presentation/meta_endpoints.py` (Instagram/Facebook events for Social Content Ops —
**not** a WhatsApp receiver; `channels/meta.py` discards anything that is not `facebook`/`instagram`)
stays mounted as a public, unauthenticated `POST` with a hardcoded default verify token
(`contexia-meta-webhook`) and no payload signature check. It is in scope here only for that
hardening, not for removal.

**Revised mid-implementation (2026-07-28)** — see design.md Decision 1: `contexia.online`'s
nameservers are Hostinger's, so a Cloudflare Tunnel hostname is unavailable without delegating the
zone (rejected — the NS TTL at the TLD is 24–48h and unrecoverable for mail). Meanwhile
`vercel.json` already rewrites `/api/v1/:path*` to Railway, so
`https://contexia.online/api/v1/channels/whatsapp/webhook` is already public, TLS-terminated, and
on the company's own domain at zero cost (verified live: `/api/v1/health` → 200). Route A's webhook
is therefore **kept and hardened**, not deleted — Chatwoot's inbox gap this creates (answered
messages don't yet appear there) is tracked as an explicit follow-up (`whatsapp-durable-inbox`),
not silently accepted.

## What Changes

- **Single Taty brain.** New authenticated internal endpoint exposes `route_lead_message` so the
  bridge produces replies through the sales router instead of a raw Hermes chat completion.
  `apps/chatwoot-bridge/main.py` calls it via the existing `backend_client` seam (which already
  calls `/crm/leads/whatsapp-intake`), keeping the bridge a transport layer.
- **Single WhatsApp ingress, hardened.** Route A's public webhook is KEPT. It now verifies
  `X-Hub-Signature-256` over the raw body and its verify token fails closed. The
  `WHATSAPP_CANONICAL` flag is retired — a flag on a live ingress can only drop real messages.
- **Hermes keeps its role, loses its parallel one.** Hermes remains the inference provider reached
  through the backend's existing LLM path; it stops being an independent reply generator that
  bypasses intent classification, Wompi, and RAG.
- **`meta_endpoints.py` hardened**: `X-Hub-Signature-256` verification over the raw body and a
  fail-closed verify token with no hardcoded default.
- **BREAKING**: `WHATSAPP_CANONICAL` is removed from config, and the WhatsApp webhook now
  REJECTS unsigned payloads (`403`). Any caller that was posting to it without a valid Meta
  signature stops working by design. Requires `WHATSAPP_APP_SECRET` to be set before the route can
  accept anything — see tasks section 4.

## Capabilities

### New Capabilities
- `taty-channel-consolidation`: the invariant that exactly one WhatsApp ingress and exactly one
  Taty reply-generation path exist, and the contract of the internal reply endpoint the bridge
  consumes.

### Modified Capabilities
- `taty-whatsapp-sales-router`: gains an authenticated internal endpoint alongside its public
  webhook, and the webhook gains signature verification. The routing logic itself
  (`taty_lead_router.py`) is unchanged — this change adds who can call it and proves who did,
  not what it does.

## Impact

- **Code**: `apps/backend/presentation/whatsapp_endpoints.py` (webhook signature-verified,
  internal reply endpoint added), `presentation/router.py` (unconditional mount), `config.py`
  (`WHATSAPP_CANONICAL` retired; `WHATSAPP_WEBHOOK_VERIFY_TOKEN`, `WHATSAPP_APP_SECRET`,
  `META_WEBHOOK_VERIFY_TOKEN`, `META_APP_SECRET` all fail-closed),
  `presentation/meta_endpoints.py` (signature verification),
  `apps/chatwoot-bridge/{main,backend_client}.py`.
- **Tests**: `tests/test_whatsapp_endpoints.py` rewritten against the new surface; bridge
  `tests/test_process_message.py` updated; new signature-verification tests for meta.
- **No migrations, no new tables** — `taty_lead_router` already reads/writes `crm_leads` and
  `crm_wompi_transactions` unchanged.
- **No frontend changes.**
- **Out of scope, and consequential** (see tasks section 8): with Meta pointed at the Railway
  webhook, answered messages do **not** appear in Chatwoot, so the human accountant has no inbox
  yet. Closing that needs the durable-receiver shape (persist + dedup on Meta's message id, local
  node pulls with a cursor and injects into Chatwoot via its API) — tracked and being built in
  `whatsapp-durable-inbox`. Also out of scope: moving document collection to a PWA magic link (Meta
  policy forbids collecting ID/bank-account numbers in-thread — so the bridge's existing
  attachment fallback stays as-is for now); Tier-1/Tier-2 approval-queue gating; voice notes.
