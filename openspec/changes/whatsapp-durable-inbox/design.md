## Context

Meta's webhook is at-least-once with a hard ceiling: it retries a non-200, then drops the event
forever. No replay API, no DLQ. The consumer must therefore be durable and idempotent, because
the platform provides neither. Retries also fan out to every subscribed app, so duplicate
delivery is normal traffic, not an error condition.

The local node cannot be the thing Meta talks to without buying public reachability it does not
have (see proposal). Railway already has it, for free.

## Decisions

1. **Persist first, process later.** The webhook's only job is: verify signature → insert →
   `200`. Everything else is a background concern.
   *Alternative considered:* keep processing inline and simply add dedup. Rejected — inline
   processing means an LLM call sits inside Meta's request. A slow model turns into a retry, the
   retry turns into a duplicate, and a crash between "replied" and "returned 200" loses nothing
   but *also* re-replies. Persisting first makes the whole class of failure disappear.

2. **Deduplication is the unique index, not application logic.** `INSERT … ON CONFLICT
   (meta_message_id) DO NOTHING` — the database is the only place where "have I seen this?" can
   be answered without a race between two concurrent retries.
   *Alternative considered:* an in-memory or Redis seen-set. Rejected — it does not survive a
   restart, which is exactly when Meta is retrying.

3. **The local node pulls; Railway never pushes.** This is what removes the tunnel requirement
   entirely. The node makes an outbound HTTPS call, the same direction Chatwoot's containers
   already talk to the internet.
   *Alternative considered:* Railway pushing to the node through a tunnel. Rejected — reintroduces
   the domain/delegation problem this change exists to avoid, and makes Railway depend on the
   node being up.

4. **Claim-then-acknowledge, not delete-on-read.** A pull marks rows with a claim timestamp; a
   separate acknowledge marks them processed. If the node crashes between pulling and injecting,
   the claim expires and the event is redelivered.
   *Alternative considered:* delete on read. Rejected — a crash after the read loses the message
   permanently, which is the failure this change exists to prevent.

5. **Side effects are exactly-once by acknowledging only after Chatwoot accepts the injection.**
   At-least-once delivery plus an idempotent consumer is the only honest guarantee available; the
   `meta_message_id` unique index also protects the injection path if a redelivery slips through.

6. **Taty's reply path is untouched.** The poller injects the customer's message into Chatwoot;
   Chatwoot then fires its existing webhook to the bridge, which calls
   `backend_client.taty_reply`. The single-brain invariant from `taty-channel-consolidation` is
   preserved rather than re-implemented.
   *Alternative considered:* have the poller call `taty_reply` directly and post both sides into
   Chatwoot. Rejected — it would duplicate the bridge's filtering and `bot_off` HITL check, which
   is precisely the second-brain mistake this line of work just finished removing.

## Risks / Trade-offs

- **[Risk] Reply latency grows** — the customer's message now waits for a poll interval before
  Taty sees it. → **Mitigation**: short interval (default 5s). WhatsApp is not a synchronous
  medium; a few seconds is invisible to a user typing on a phone. Accepted.
- **[Risk] The node being offline is now silent** rather than visibly broken — events pile up
  correctly, but nobody notices. → **Mitigation**: expose the backlog depth and oldest-unclaimed
  age so it can be alerted on. A durable queue nobody watches is a queue that quietly grows.
- **[Risk] `bot_off` cannot pause a message that has not reached Chatwoot yet.** A message
  injected while the label is set will still be injected — correctly, since Tatiana needs to see
  it — and the bridge's existing check stops the bot from replying. Behaviour is right; worth
  stating because it looks like a gap.
- **[Trade-off] Two hops before the customer gets an answer** (Railway → node → Chatwoot →
  bridge → Railway). More moving parts than a direct webhook, bought in exchange for never losing
  a message and never needing a public local node. Accepted deliberately.

## Migration Plan

1. Land migration `0036` (additive table, safe on its own).
2. Land the receiver + pull/ack endpoints (nothing consumes them yet).
3. Land the bridge poller.
4. Rollback: stop the poller. Events keep accumulating durably; nothing is lost, and the previous
   inline-processing behaviour can be restored by reverting the webhook handler alone.

## Open Questions

- Retention for processed events — a tax-season volume of rows is trivial for Postgres, but
  inbound messages contain customer text and fall under the Ley 1581 retention policy the
  architecture plan calls for. Deferred to that work, not invented here.
