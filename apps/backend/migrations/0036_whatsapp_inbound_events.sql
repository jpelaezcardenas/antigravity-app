-- Migration: Durable inbox for inbound WhatsApp Cloud API events.
-- Date: 2026-07-30
-- Purpose: Meta's webhook is at-least-once with a hard ceiling — it retries a non-200 and then
-- drops the event permanently. There is no replay API, no dead-letter queue and no event log. A
-- mini-PC on office fibre would therefore lose customer messages silently on every power or ISP
-- blink, and today nothing persists an inbound message before it is processed, so a crash
-- mid-handler loses it too. This table makes the Railway backend a durable buffer that
-- acknowledges Meta immediately; the local node pulls from it, so the node never needs to be
-- publicly reachable (which is what removes the Cloudflare-Tunnel/domain-delegation requirement).
-- Change: whatsapp-durable-inbox.
-- Idempotent: Can be run multiple times safely.
-- Prerequisites: none — additive, creates one new table and touches nothing existing.

-- 1. The table. `meta_message_id` UNIQUE is the deduplication mechanism itself, not a hint:
-- Meta's retries fan out to every subscribed app, so duplicate delivery is normal traffic. Doing
-- this in the database rather than in application code is deliberate — two concurrent retries
-- would race any read-then-write check.
CREATE TABLE IF NOT EXISTS public.whatsapp_inbound_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Meta's own message id (normalize_whatsapp_webhook exposes it as `source_event_id`).
    -- NOT NULL + UNIQUE: the service layer must never insert a blank one, because a blank would
    -- collide every un-idded message into a single row and silently discard real messages.
    meta_message_id TEXT NOT NULL UNIQUE,

    -- Normalized fields (see channels/whatsapp.py::normalize_whatsapp_webhook).
    account_id      TEXT NOT NULL,          -- customer phone / wa_id
    actor_name      TEXT,
    body            TEXT,
    media_id        TEXT,
    mime_type       TEXT,
    raw_payload     JSONB NOT NULL,

    -- Claim-then-acknowledge, not delete-on-read: if the consumer crashes between pulling and
    -- injecting into Chatwoot, the claim expires and the event is redelivered rather than lost.
    claimed_at      TIMESTAMPTZ,
    processed_at    TIMESTAMPTZ,

    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 2. Pull-query index: unprocessed events, oldest first. Partial so it stays small — processed
-- rows accumulate over a tax season but are never scanned by the hot path.
CREATE INDEX IF NOT EXISTS idx_whatsapp_inbound_events_pending
    ON public.whatsapp_inbound_events (created_at)
    WHERE processed_at IS NULL;

-- 3. Backlog-health index: supports counting unprocessed events and finding the oldest, which is
-- how an offline local node becomes detectable instead of silent.
CREATE INDEX IF NOT EXISTS idx_whatsapp_inbound_events_claimed
    ON public.whatsapp_inbound_events (claimed_at)
    WHERE processed_at IS NULL;

-- 4. RLS on with no permissive policy: this table holds raw customer message text (personal data
-- under Ley 1581) and is written and read exclusively by the backend using the service-role key.
-- Enabling RLS without granting anon/authenticated anything means a leaked anon key cannot read
-- customer conversations. Deliberately NOT following the permissive `*_anon_all` pattern that
-- hermes-multi-tenant-wrapper left on approval_queue and which is already flagged for removal.
ALTER TABLE public.whatsapp_inbound_events ENABLE ROW LEVEL SECURITY;

COMMENT ON TABLE public.whatsapp_inbound_events IS
    'Durable buffer for inbound WhatsApp Cloud API events (change: whatsapp-durable-inbox). '
    'Written by the Railway webhook, pulled by the local Chatwoot bridge. Dedup on meta_message_id.';
