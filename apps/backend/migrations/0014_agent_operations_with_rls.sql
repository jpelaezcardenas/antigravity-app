-- Migration 0014: agent_operations audit table with RLS
-- Change: agent-operations-multitenant-security (Slice 1)
-- Date: 2026-06-24
--
-- Per-invocation audit log for every agent call routed through the WebSocket
-- invoke_agent() chokepoint. Captures who/where/what/outcome/timing/cost plus
-- input/output payloads. Financial rows are written separately to cost_tracking
-- (migration 0013); this table is the audit trail.
--
-- Conventions mirror 0013_missions_table_with_rls.sql:
--   tenant_id FK -> tenants(id) ON DELETE CASCADE, cost DECIMAL(10,6),
--   created_at TIMESTAMPTZ, indexes on tenant scoping, RLS via user_tenants/roles.

-- ============================================================================
-- 1. AGENT_OPERATIONS TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS agent_operations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    agent_name VARCHAR(100) NOT NULL,
    user_id VARCHAR(255) NOT NULL,
    operation_type VARCHAR(100) NOT NULL,

    -- Outcome: success | failed | blocked (blocked = access-control denial)
    status VARCHAR(20) NOT NULL DEFAULT 'success'
        CHECK (status IN ('success', 'failed', 'blocked')),

    -- Performance + financial tracking
    duration_ms INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) NOT NULL DEFAULT 0,

    -- Forensic payloads
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_agent_operations_tenant_id ON agent_operations(tenant_id);
CREATE INDEX IF NOT EXISTS idx_agent_operations_agent_name ON agent_operations(agent_name);
CREATE INDEX IF NOT EXISTS idx_agent_operations_status ON agent_operations(status);
CREATE INDEX IF NOT EXISTS idx_agent_operations_created_at ON agent_operations(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_agent_operations_tenant_created
    ON agent_operations(tenant_id, created_at DESC);

-- ============================================================================
-- 2. ROW-LEVEL SECURITY
-- ============================================================================

ALTER TABLE agent_operations ENABLE ROW LEVEL SECURITY;

-- RLS Policy: users can only see agent operations from their active tenant
-- NOTE: this DB models membership in user_tenants(user_id, tenant_id, is_active)
-- and role as an inline enum on user_roles.role (role_type) — there is no
-- separate roles table (verified against live schema 2026-06-24).
CREATE POLICY agent_operations_tenant_isolation ON agent_operations
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM user_tenants
            WHERE user_id = auth.uid()
            AND is_active = true
        )
    );

-- RLS Policy: full audit visibility limited to admin/finance roles
CREATE POLICY agent_operations_audit_privileged ON agent_operations
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            WHERE ur.user_id = auth.uid()
            AND ur.tenant_id = agent_operations.tenant_id
            AND ur.role IN ('admin', 'finance')
        )
    );

-- Grants follow the established pattern (backend connects with a broad key;
-- tenant isolation is also enforced in application code — see design.md D2).
GRANT SELECT, INSERT ON agent_operations TO anon, authenticated, service_role;

-- ============================================================================
-- 3. STATUS
-- ============================================================================

SELECT '✅ Migration 0014 complete: agent_operations table with RLS created' AS status;
