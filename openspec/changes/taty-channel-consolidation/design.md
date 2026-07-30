## Context

Meta permits one callback URL per app. This repo has two live-capable WhatsApp reply paths built
by different changes (`taty-whatsapp-sales-router` → Route A; `chatwoot-hermes-taty-bridge` →
Route C) that were never reconciled, because Route C's design deliberately scoped the public
tunnel out ("documented as a manual deployment step, not built/automated here") and therefore
never had to confront which route Meta would actually point at.

## Decisions

1. **`taty_lead_router` is the sole reply brain. The Railway webhook is the sole Meta ingress.**

   **Revised mid-implementation (2026-07-28)** — the original decision deleted Route A's webhook
   on the assumption Chatwoot would terminate Meta. Checking DNS invalidated that assumption:
   `contexia.online`'s nameservers are Hostinger's (`ns1/ns2.dns-parking.com`, apex → Vercel at
   216.198.79.1). A Cloudflare Named Tunnel publishes hostnames as CNAMEs to
   `<TUNNEL_ID>.cfargotunnel.com`, which only resolves inside Cloudflare's edge — a CNAME from
   Hostinger to it does not resolve, and Cloudflare's partial/CNAME-setup zone mode is a
   Business-plan feature. So exposing Chatwoot publicly requires either delegating the zone
   (rejected: NS TTL at the TLD is 24–48h and unrecoverable for mail) or a paid front.

   Meanwhile `vercel.json` already rewrites `/api/v1/:path*` to Railway, so
   `https://contexia.online/api/v1/channels/whatsapp/webhook` is **already public, already TLS,
   already on the company's own domain, at zero cost** (verified: `/api/v1/health` → 200).

   The webhook is therefore **kept and hardened**, not deleted: `X-Hub-Signature-256` over the raw
   body, fail-closed verify token, and the feature flag retired (a flag on a live ingress can only
   drop real customer messages).
   *Alternative considered:* keep deleting it and buy a domain/VPS for a Chatwoot tunnel.
   Rejected for now — it spends money and time to reach a public URL the company already owns.

   **Known consequence, not left silent:** with Meta pointed at Railway, messages reach
   `taty_lead_router` and get answered, but they do **not** appear in Chatwoot — so the human
   accountant has no inbox, which was the reason Chatwoot was chosen. Closing that needs the
   durable-receiver shape: the webhook persists the event and the local node pulls and injects it
   into Chatwoot via its API. That is `whatsapp-durable-inbox`, an explicit follow-up change, not
   implemented here (see Migration Plan step 6).

2. **The bridge stays a transport layer.** It gains one call, not logic. `process_incoming_message`
   replaces `hermes_client.invoke_chat_completion(history, content)` with
   `backend_client.taty_reply(lead_id, content)`. This preserves the bridge's stated design
   contract (decision 5 of `chatwoot-hermes-taty-bridge`: no business logic duplicated from the
   backend) — today the bridge violates that contract in spirit, because generating a sales reply
   from raw history *is* business logic living outside the backend.

3. **The internal endpoint is authenticated with the mechanism the bridge already uses.**
   `backend_client.sign_tenant_jwt()` + `_headers()` already mint a JWT for
   `/crm/leads/whatsapp-intake`. The new endpoint reuses `Depends(get_current_user)` on the same
   contract rather than inventing a second scheme.
   *Alternative considered:* a shared static token. Rejected — the repo already standardized on
   the JWT path for bridge→backend, and ARCHITECTURE.md decision #17 mandates a single tenant
   resolution contract across the agent HTTP surface.

4. **`lead_id`, not `phone`, is the endpoint's key.** The bridge already holds `lead_id` from the
   intake call it makes immediately before. Passing the phone again would duplicate the
   find-or-create and risk a second lead row on a race.

5. **Hermes is not removed from the bridge.** `hermes_client.check_models()` stays as the
   startup/health liveness probe (it is what makes a wrong-profile gateway visible in logs, per
   the bridge's decision 8). Only `invoke_chat_completion` stops being the reply source.
   `taty_lead_router` reaches the LLM through `get_anonymized_ai_response`, which keeps the
   pre-LLM anonymization guarantee the bridge path currently bypasses entirely.

6. **`meta_endpoints.py` is hardened, not consolidated.** It serves a different product surface
   (Social Content Ops) whose events are Instagram/Facebook only. It shares the `hub.challenge`
   idiom with WhatsApp, which is what made it look like a third competing receiver; it is not one.
   It gets the same two controls the WhatsApp route should have had: HMAC over the raw body and a
   verify token with no hardcoded default.

7. **Signature verification requires the raw body.** FastAPI's `Dict[str, Any]` body parameter
   re-serializes and cannot reproduce the exact bytes Meta signed. The handler takes `Request` and
   reads `await request.body()` before parsing — a real bug class, since a JSON round-trip changes
   key order and whitespace and would make every signature fail.

## Risks / Trade-offs

- **[Risk] The bridge's reply latency now includes a backend round-trip.** Chatwoot → bridge →
  Railway → LLM → back. → **Mitigation**: the bridge already calls the backend synchronously for
  intake in the same pipeline, and the whole pipeline runs in a FastAPI `BackgroundTask`, so no
  webhook response is blocked. Accepted.
- **[Risk] `taty_lead_router`'s replies are tuned for a deterministic keyword flow, not
  conversational history.** Its `route_lead_message(lead_id, text)` signature takes no history, so
  multi-turn context Chatwoot has is not passed. → **Mitigation**: out of scope here; this change
  preserves existing router behavior exactly. Adding history is a follow-up against
  `taty-whatsapp-sales-router`, not a silent redesign inside a consolidation change.
- **[Trade-off] Keeping Route A means two more moving parts before Chatwoot sees a message**
  (webhook → durable store → local poller → Chatwoot, built in `whatsapp-durable-inbox`) instead
  of Meta talking to Chatwoot directly. Accepted — it buys zero-cost, zero-delegation-risk public
  reachability and never losing a message when the local node is offline.
- **[Risk] `META_APP_SECRET` is not yet set in Railway**, so enabling fail-closed verification
  could break Social Ops ingestion on deploy. → **Mitigation**: set the env var before merge and
  verify the value is present in Railway as an explicit task, ordered before the code lands.

## Migration Plan

1. Land the internal reply endpoint (additive, nothing consumes it yet).
2. Point the bridge at it; run bridge tests against a running backend.
3. Harden Route A's webhook (signature verification) and retire `WHATSAPP_CANONICAL`.
4. Harden `meta_endpoints.py` **after** confirming `META_APP_SECRET` is set in Railway.
5. Rollback: revert the bridge to `hermes_client.invoke_chat_completion` (one function call) —
   Chatwoot keeps queuing messages for human takeover regardless, so no data loss.
6. Follow-up (separate change, `whatsapp-durable-inbox`): give Chatwoot the messages Route A now
   answers, via a durable persist-then-pull design.

## Open Questions

- Should `route_lead_message` eventually accept conversation history from Chatwoot? Deferred; see
  Risks above.
