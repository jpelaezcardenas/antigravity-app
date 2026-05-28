-- Social Content Ops Coworker-style acquisition schema.
-- Apply after validating service rollout; runtime falls back to memory until SOCIAL_OPS_PERSIST_SUPABASE=true.

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS social_channel_accounts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    channel text NOT NULL CHECK (channel IN ('telegram', 'facebook', 'instagram', 'tiktok', 'linkedin')),
    account_id text NOT NULL,
    display_name text NOT NULL,
    auth_status text NOT NULL DEFAULT 'pending',
    capability_status jsonb NOT NULL DEFAULT '{}'::jsonb,
    scopes text[] NOT NULL DEFAULT '{}',
    token_ref text,
    last_sync_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (channel, account_id)
);

CREATE TABLE IF NOT EXISTS social_leads (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    primary_channel text NOT NULL CHECK (primary_channel IN ('telegram', 'facebook', 'instagram', 'tiktok', 'linkedin')),
    actor_handle text NOT NULL,
    display_name text,
    maturity_stage text NOT NULL DEFAULT 'Informal',
    pipeline_stage text NOT NULL DEFAULT 'nuevo',
    urgency text NOT NULL DEFAULT 'low',
    pain_tags text[] NOT NULL DEFAULT '{}',
    score integer NOT NULL DEFAULT 0,
    last_message text,
    last_event_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (primary_channel, actor_handle)
);

CREATE TABLE IF NOT EXISTS social_inbound_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    channel text NOT NULL CHECK (channel IN ('telegram', 'facebook', 'instagram', 'tiktok', 'linkedin')),
    account_id text,
    source_event_id text NOT NULL,
    event_type text NOT NULL,
    actor_handle text,
    actor_name text,
    text text NOT NULL,
    normalized_text text,
    pain_tags text[] NOT NULL DEFAULT '{}',
    urgency text NOT NULL DEFAULT 'low',
    status text NOT NULL DEFAULT 'new',
    lead_id uuid REFERENCES social_leads(id) ON DELETE SET NULL,
    raw_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    received_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (channel, source_event_id)
);

CREATE TABLE IF NOT EXISTS social_conversations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id uuid NOT NULL REFERENCES social_leads(id) ON DELETE CASCADE,
    channel text NOT NULL CHECK (channel IN ('telegram', 'facebook', 'instagram', 'tiktok', 'linkedin')),
    external_thread_id text,
    status text NOT NULL DEFAULT 'open',
    last_message_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS social_pipeline_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    lead_id uuid NOT NULL REFERENCES social_leads(id) ON DELETE CASCADE,
    stage text NOT NULL,
    reason text,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS social_agent_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    agent_name text NOT NULL,
    lead_id uuid REFERENCES social_leads(id) ON DELETE SET NULL,
    event_id uuid REFERENCES social_inbound_events(id) ON DELETE SET NULL,
    status text NOT NULL DEFAULT 'completed',
    output jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS social_command_drafts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    channel text NOT NULL CHECK (channel IN ('telegram', 'facebook', 'instagram', 'tiktok', 'linkedin')),
    actor_handle text,
    lead_id uuid REFERENCES social_leads(id) ON DELETE SET NULL,
    command_text text NOT NULL,
    action text NOT NULL,
    status text NOT NULL DEFAULT 'pending_approval',
    requires_approval boolean NOT NULL DEFAULT true,
    risk_level text NOT NULL DEFAULT 'controlled',
    approval_reason text,
    parsed_payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    approved_at timestamptz,
    approved_by text
);

CREATE TABLE IF NOT EXISTS social_reply_drafts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    type text NOT NULL DEFAULT 'lead_reply',
    lead_id uuid REFERENCES social_leads(id) ON DELETE SET NULL,
    channel text NOT NULL CHECK (channel IN ('telegram', 'facebook', 'instagram', 'tiktok', 'linkedin')),
    intent text,
    status text NOT NULL DEFAULT 'pending_approval',
    requires_approval boolean NOT NULL DEFAULT true,
    approval_reason text,
    actor_handle text,
    message_text text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    approved_at timestamptz,
    approved_by text,
    rejected_at timestamptz,
    rejected_by text,
    rejection_reason text
);

CREATE TABLE IF NOT EXISTS social_sales_drafts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    type text NOT NULL DEFAULT 'sales_closure',
    lead_id uuid REFERENCES social_leads(id) ON DELETE SET NULL,
    channel text NOT NULL CHECK (channel IN ('telegram', 'facebook', 'instagram', 'tiktok', 'linkedin')),
    status text NOT NULL DEFAULT 'pending_approval',
    requires_approval boolean NOT NULL DEFAULT true,
    approval_reason text,
    actor_handle text,
    message_text text NOT NULL,
    sales_script jsonb NOT NULL DEFAULT '{}'::jsonb,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    approved_at timestamptz,
    approved_by text,
    rejected_at timestamptz,
    rejected_by text,
    rejection_reason text
);

CREATE TABLE IF NOT EXISTS service_desk_tickets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id text NOT NULL,
    channel text NOT NULL,
    actor_handle text,
    subject text,
    body text NOT NULL,
    category text NOT NULL DEFAULT 'general',
    priority text NOT NULL DEFAULT 'normal',
    level text NOT NULL DEFAULT 'L1',
    status text NOT NULL DEFAULT 'open',
    assigned_to text,
    requires_human_review boolean NOT NULL DEFAULT false,
    duplicate_count integer NOT NULL DEFAULT 0,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS service_desk_reply_drafts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ticket_id uuid REFERENCES service_desk_tickets(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'pending_approval',
    requires_approval boolean NOT NULL DEFAULT true,
    approval_reason text,
    actor_handle text,
    reply_text text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    approved_at timestamptz,
    approved_by text,
    rejected_at timestamptz,
    rejected_by text,
    rejection_reason text
);

CREATE TABLE IF NOT EXISTS social_onboarding_workspaces (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name text NOT NULL,
    customer_email text NOT NULL,
    payment_reference text NOT NULL,
    plan_name text NOT NULL DEFAULT 'Starter',
    owner_handle text,
    status text NOT NULL DEFAULT 'active',
    current_step text NOT NULL DEFAULT 'payment_verified',
    requested_channels text[] NOT NULL DEFAULT '{}',
    steps jsonb NOT NULL DEFAULT '[]'::jsonb,
    training_profile jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (payment_reference)
);

CREATE TABLE IF NOT EXISTS social_onboarding_seed_drafts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL REFERENCES social_onboarding_workspaces(id) ON DELETE CASCADE,
    status text NOT NULL DEFAULT 'pending_approval',
    requires_approval boolean NOT NULL DEFAULT true,
    approval_reason text,
    business_summary text,
    datasets jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    approved_at timestamptz,
    approved_by text
);

CREATE TABLE IF NOT EXISTS social_onboarding_intake_items (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id uuid NOT NULL REFERENCES social_onboarding_workspaces(id) ON DELETE CASCADE,
    source text NOT NULL DEFAULT 'dashboard',
    actor_handle text,
    text text NOT NULL,
    extracted jsonb NOT NULL DEFAULT '{}'::jsonb,
    present text[] NOT NULL DEFAULT '{}',
    missing text[] NOT NULL DEFAULT '{}',
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_social_inbound_channel_received
    ON social_inbound_events(channel, received_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_inbound_lead
    ON social_inbound_events(lead_id);

CREATE INDEX IF NOT EXISTS idx_social_leads_pipeline
    ON social_leads(pipeline_stage, urgency, last_event_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_command_drafts_status
    ON social_command_drafts(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_reply_drafts_status
    ON social_reply_drafts(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_sales_drafts_status
    ON social_sales_drafts(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_service_desk_tickets_status
    ON service_desk_tickets(status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_service_desk_reply_drafts_status
    ON service_desk_reply_drafts(status, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_onboarding_status
    ON social_onboarding_workspaces(status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_onboarding_seed_workspace
    ON social_onboarding_seed_drafts(workspace_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_social_onboarding_intake_workspace
    ON social_onboarding_intake_items(workspace_id, created_at DESC);

ALTER TABLE social_channel_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_inbound_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_pipeline_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_command_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_reply_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_sales_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_desk_tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE service_desk_reply_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_onboarding_workspaces ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_onboarding_seed_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE social_onboarding_intake_items ENABLE ROW LEVEL SECURITY;
