-- Migration: 0046_gmail_sender_map.sql
-- Maps Gmail sender addresses to tenant UUIDs for the hermes-gmail-poller.
-- When Taty receives a document attachment via email, the poller looks up
-- the sender's address here to determine which tenant to ingest under.
-- Populated manually (Taty adds a row when onboarding a client who sends attachments).

CREATE TABLE IF NOT EXISTS gmail_sender_map (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    sender_email text NOT NULL UNIQUE,
    tenant_id   uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    notes       text,
    created_at  timestamptz NOT NULL DEFAULT now(),
    updated_at  timestamptz NOT NULL DEFAULT now()
);

-- Index for the poller's lookup (by sender email on every processed email)
CREATE INDEX IF NOT EXISTS idx_gmail_sender_map_email
    ON gmail_sender_map (sender_email);

-- RLS: service_role writes; authenticated reads own tenant's rows only
ALTER TABLE gmail_sender_map ENABLE ROW LEVEL SECURITY;

CREATE POLICY gmail_sender_map_service_all
    ON gmail_sender_map
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

CREATE POLICY gmail_sender_map_tenant_read
    ON gmail_sender_map
    FOR SELECT
    TO authenticated
    USING (
        tenant_id = (
            SELECT resolved_tenant_id
            FROM user_tenants
            WHERE user_id = auth.uid()
              AND is_active = true
            LIMIT 1
        )
    );

COMMENT ON TABLE gmail_sender_map IS
    'Maps Gmail sender addresses to tenant UUIDs for hermes-gmail-poller attachment ingestion.';
