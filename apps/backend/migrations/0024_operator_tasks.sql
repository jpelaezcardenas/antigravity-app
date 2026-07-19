-- Migration 0024: operator_tasks (hermes-manus-execution-bridge, Change F)
-- Date: 2026-07-19
-- Generic operator-task queue bridging approved Sell Machine output (and other operational
-- asks) to external execution via Hermes/Manus. Tenant-scoped to Cliente Cero, admin-only RLS
-- using the live role_type enum (values verified live: admin | finance | marketing | growth |
-- operator | viewer), matching the pattern established in 0020_crm_b2b_retainers.sql.

CREATE TABLE IF NOT EXISTS operator_tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  task_type text NOT NULL,
  status text NOT NULL DEFAULT 'pending',
  payload jsonb NOT NULL DEFAULT '{}',
  result jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT chk_operator_tasks_task_type CHECK (
    task_type IN (
      'post_content',
      'run_ads_ab',
      'research',
      'metrics_pull',
      'external_integration',
      'generate_doc'
    )
  ),
  CONSTRAINT chk_operator_tasks_status CHECK (
    status IN ('pending', 'dispatched', 'completed', 'failed')
  )
);

CREATE INDEX IF NOT EXISTS idx_operator_tasks_tenant ON operator_tasks (tenant_id);
CREATE INDEX IF NOT EXISTS idx_operator_tasks_status ON operator_tasks (status);

-- Reuses the generic updated_at trigger function from 0020_crm_b2b_retainers.sql (despite the
-- name, it is a plain `NEW.updated_at = now()` function with no table-specific logic).
DROP TRIGGER IF EXISTS trg_operator_tasks_updated_at ON operator_tasks;
CREATE TRIGGER trg_operator_tasks_updated_at
  BEFORE UPDATE ON operator_tasks
  FOR EACH ROW
  EXECUTE FUNCTION update_crm_b2b_updated_at();

-- Row Level Security: admin-only, using the live role_type enum.
ALTER TABLE operator_tasks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS operator_tasks_admin_only ON operator_tasks;
CREATE POLICY operator_tasks_admin_only ON operator_tasks
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = operator_tasks.tenant_id
      AND role = 'admin'
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = operator_tasks.tenant_id
      AND role = 'admin'
    )
  );

COMMENT ON TABLE operator_tasks IS 'Generic operator-task queue for the Hermes/Manus execution bridge. Hermes polls status=pending, marks dispatched, and writes results back. No FK to approval_queue by design — side-effecting task payloads carry source_decision_id for traceability instead (see design.md).';
COMMENT ON COLUMN operator_tasks.task_type IS 'post_content/run_ads_ab are side-effecting and may only be created via the campaign-package dispatch endpoint; research/metrics_pull/external_integration/generate_doc are read-only and may be created directly.';
COMMENT ON COLUMN operator_tasks.result IS 'Shape varies by task_type: a post URL + basic metrics for post_content/run_ads_ab, a report payload for research/metrics_pull/generate_doc.';

SELECT '✅ 0024 operator_tasks complete' AS status;
