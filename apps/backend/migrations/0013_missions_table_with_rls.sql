-- Migration 0013: Create missions, tasks, checkpoints tables with RLS policies
-- T12.1: Row-Level Security for missions
-- Date: 2026-06-23

-- ============================================================================
-- 1. MISSIONS TABLE (Work units for customer onboarding)
-- ============================================================================

CREATE TABLE IF NOT EXISTS missions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    objective TEXT NOT NULL,

    -- Cost tracking
    cost DECIMAL(10, 6) NOT NULL DEFAULT 0,
    cost_breakdown JSONB DEFAULT '{}',

    -- Progress tracking
    progress FLOAT DEFAULT 0.0,

    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metadata
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_missions_tenant_id ON missions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_missions_status ON missions(status);
CREATE INDEX IF NOT EXISTS idx_missions_created_at ON missions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_missions_tenant_status ON missions(tenant_id, status);

-- Enable RLS on missions
ALTER TABLE missions ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see missions from their tenant
CREATE POLICY missions_tenant_isolation ON missions
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM user_tenants
            WHERE user_id = auth.uid()
        )
    );

-- RLS Policy: Only admins can create missions
CREATE POLICY missions_insert_admin_only ON missions
    FOR INSERT
    WITH CHECK (
        tenant_id IN (
            SELECT ut.tenant_id FROM user_tenants ut
            WHERE ut.user_id = auth.uid()
            AND EXISTS (
                SELECT 1 FROM user_roles ur
                WHERE ur.user_id = auth.uid()
                AND ur.tenant_id = tenant_id
                AND ur.role_id IN (
                    SELECT id FROM roles WHERE name = 'admin'
                )
            )
        )
    );

-- RLS Policy: Only admins can update missions
CREATE POLICY missions_update_admin_only ON missions
    FOR UPDATE
    USING (
        tenant_id IN (
            SELECT ut.tenant_id FROM user_tenants ut
            WHERE ut.user_id = auth.uid()
            AND EXISTS (
                SELECT 1 FROM user_roles ur
                WHERE ur.user_id = auth.uid()
                AND ur.tenant_id = tenant_id
                AND ur.role_id IN (
                    SELECT id FROM roles WHERE name = 'admin'
                )
            )
        )
    );

-- ============================================================================
-- 2. TASKS TABLE (Individual operations within a mission)
-- ============================================================================

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    type VARCHAR(50) NOT NULL,
    operator VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'assigned',
    payload JSONB DEFAULT '{}',

    -- Timing
    created_at TIMESTAMPTZ DEFAULT NOW(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,

    -- Metadata
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_mission_id ON tasks(mission_id);
CREATE INDEX IF NOT EXISTS idx_tasks_tenant_id ON tasks(tenant_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at DESC);

-- Enable RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Same tenant isolation as missions
CREATE POLICY tasks_tenant_isolation ON tasks
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM user_tenants
            WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- 3. CHECKPOINTS TABLE (Proof of task completion)
-- ============================================================================

CREATE TABLE IF NOT EXISTS checkpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL REFERENCES missions(id) ON DELETE CASCADE,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,

    task_type VARCHAR(100) NOT NULL,
    status VARCHAR(5) NOT NULL,  -- ✅, ⏳, ❌
    proof JSONB DEFAULT '{}',
    operator_id VARCHAR(100) NOT NULL,

    -- Performance metrics
    duration_ms INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0,

    -- Timing
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_checkpoints_mission_id ON checkpoints(mission_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_tenant_id ON checkpoints(tenant_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_status ON checkpoints(status);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at DESC);

-- Enable RLS
ALTER TABLE checkpoints ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Checkpoints inherit mission's tenant isolation
CREATE POLICY checkpoints_tenant_isolation ON checkpoints
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM user_tenants
            WHERE user_id = auth.uid()
        )
    );

-- ============================================================================
-- 4. COST_TRACKING TABLE (Financial tracking per operation)
-- ============================================================================

CREATE TABLE IF NOT EXISTS cost_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    mission_id UUID REFERENCES missions(id) ON DELETE SET NULL,

    operation_type VARCHAR(100) NOT NULL,
    cost DECIMAL(10, 6) NOT NULL,
    cost_currency VARCHAR(3) DEFAULT 'USD',

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_cost_tracking_tenant_id ON cost_tracking(tenant_id);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_mission_id ON cost_tracking(mission_id);
CREATE INDEX IF NOT EXISTS idx_cost_tracking_created_at ON cost_tracking(created_at DESC);

-- Enable RLS
ALTER TABLE cost_tracking ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can only see costs from their tenant
CREATE POLICY cost_tracking_tenant_isolation ON cost_tracking
    FOR SELECT
    USING (
        tenant_id IN (
            SELECT tenant_id FROM user_tenants
            WHERE user_id = auth.uid()
        )
    );

-- RLS Policy: Only finance/admin can view costs
CREATE POLICY cost_tracking_finance_only ON cost_tracking
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM user_roles ur
            INNER JOIN roles r ON r.id = ur.role_id
            WHERE ur.user_id = auth.uid()
            AND ur.tenant_id = cost_tracking.tenant_id
            AND r.name IN ('admin', 'finance')
        )
    );

-- ============================================================================
-- 5. TRIGGER: Auto-update missions.updated_at on missions table change
-- ============================================================================

CREATE OR REPLACE FUNCTION update_missions_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_missions_updated_at ON missions;
CREATE TRIGGER trigger_missions_updated_at
    BEFORE UPDATE ON missions
    FOR EACH ROW
    EXECUTE FUNCTION update_missions_updated_at();

-- ============================================================================
-- 6. TRIGGER: Auto-update tasks.updated_at on tasks table change
-- ============================================================================

CREATE OR REPLACE FUNCTION update_tasks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trigger_tasks_updated_at ON tasks;
CREATE TRIGGER trigger_tasks_updated_at
    BEFORE UPDATE ON tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_tasks_updated_at();

-- ============================================================================
-- 7. AUDIT LOG: Log all mission changes for compliance
-- ============================================================================

CREATE TABLE IF NOT EXISTS mission_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mission_id UUID NOT NULL,
    tenant_id UUID NOT NULL REFERENCES tenants(id),

    action VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    before_state JSONB,
    after_state JSONB,

    changed_by UUID REFERENCES auth.users(id),
    changed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_mission_audit_log_mission_id ON mission_audit_log(mission_id);
CREATE INDEX IF NOT EXISTS idx_mission_audit_log_tenant_id ON mission_audit_log(tenant_id);
CREATE INDEX IF NOT EXISTS idx_mission_audit_log_changed_at ON mission_audit_log(changed_at DESC);

-- ============================================================================
-- 8. STATUS: Print completion message
-- ============================================================================

SELECT '✅ Migration 0013 complete: missions table with RLS policies created' AS status;
