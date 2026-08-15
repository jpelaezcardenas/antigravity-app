## Why

`taty-channel-consolidation` left one thing open, and it is the thing the human accountant needs:
with Meta's callback pointed at the Railway webhook, inbound messages are answered by
`taty_lead_router` but **never appear in Chatwoot**. Tatiana has no inbox, which was the entire
reason Chatwoot was chosen (history, assignment, and the `bot_off` HITL pause required by the
Entidad A / Entidad B separation).

The obvious fix — point Meta at Chatwoot instead — is blocked on infrastructure:
`contexia.online`'s nameservers are Hostinger's, a Cloudflare Tunnel hostname requires delegating
the zone (rejected: NS TTL at the TLD is 24–48h and unrecoverable for mail), and Cloudflare's
partial-zone mode is a Business-plan feature. Exposing the local node publicly costs a domain, a
paid front, or both.

There is a second problem the same design solves. Meta retries a failed webhook and then **drops
the event permanently** — there is no replay API, no dead-letter queue, no event log. A mini-PC on
office fibre will lose customer messages silently every time the power or the ISP blinks. Today
nothing persists an inbound message before it is processed, so a crash mid-handler loses it too.
And because Meta retries fan out to every subscribed app, duplicates are guaranteed by design:
without deduplication a retry produces a **second reply to the same customer**.

Inverting the flow fixes both at once. Railway — already public, already TLS, already on the
company's own domain at zero cost — becomes a durable buffer that acknowledges Meta immediately
and stores the event. The local node **pulls**, so it never needs to be publicly reachable.

## What Changes

- **New table `whatsapp_inbound_events`** (migration `0036`) with a unique constraint on Meta's
  message id. Persisting is the deduplication: a retried event collides and is ignored.
- **The webhook becomes a receiver, not a processor.** After signature verification it persists
  each event and returns `200` immediately. Classification, LLM inference and outbound sending
  move off the request path, so a slow model can no longer turn into a Meta retry, and a crash
  mid-processing no longer loses the message.
- **New authenticated pull endpoint** returning unclaimed events after a cursor, plus an
  acknowledgement endpoint that marks them processed.
- **New poller in the bridge** that pulls on an interval and injects each event into Chatwoot via
  its API (contact + conversation + incoming message), which is what puts the conversation in
  front of Tatiana. Taty's reply continues to flow through the existing
  `backend_client.taty_reply` path, so the single-brain invariant holds.
- **BREAKING**: the webhook's response no longer reflects processing outcome — it reports what was
  accepted for processing. Nothing external depends on that body today.

## Capabilities

### New Capabilities
- `whatsapp-durable-inbox`: at-least-once delivery of inbound WhatsApp events with
  exactly-once side effects, and the pull/acknowledge contract the local node consumes.

### Modified Capabilities
- `taty-channel-consolidation`: its "exactly one ingress" requirement stands; this change makes
  that ingress durable and moves processing off the hot path.

## Impact

- **Migration**: `apps/backend/migrations/0036_whatsapp_inbound_events.sql` — new table only, no
  changes to existing tables.
- **Code**: `apps/backend/presentation/whatsapp_endpoints.py`, new
  `apps/backend/services/whatsapp_inbox_service.py`, `apps/chatwoot-bridge/` (poller +
  Chatwoot injection).
- **No frontend changes.**
- **Out of scope**: voice notes; the PWA magic link for document collection; Tier-1/Tier-2
  approval-queue gating. Those remain in the approved architecture plan.
