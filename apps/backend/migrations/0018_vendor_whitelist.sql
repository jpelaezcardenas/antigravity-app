-- Phase 7 Stage 3: Vendor Whitelist Table
-- Stores approved vendors for auto-approval rule

CREATE TABLE vendor_whitelist (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  vendor_code varchar(100) NOT NULL,
  vendor_name varchar(255),
  avg_amount_cents bigint NOT NULL,
  tolerance_percent numeric(3, 2) DEFAULT 0.10,
  enabled boolean DEFAULT true,
  created_at timestamp DEFAULT now(),
  updated_at timestamp DEFAULT now(),

  -- Ensure unique vendor per tenant
  UNIQUE (tenant_id, vendor_code)
);

-- Index for fast lookup
CREATE INDEX idx_vendor_whitelist_tenant_code
  ON vendor_whitelist (tenant_id, vendor_code)
  WHERE enabled = true;

-- Index for admin queries
CREATE INDEX idx_vendor_whitelist_tenant
  ON vendor_whitelist (tenant_id);

-- Enable RLS
ALTER TABLE vendor_whitelist ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Only tenant admins can view/manage vendors
CREATE POLICY vendor_whitelist_admin_only ON vendor_whitelist
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = vendor_whitelist.tenant_id
      AND role_name IN ('admin', 'accountant')
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = vendor_whitelist.tenant_id
      AND role_name = 'admin'
    )
  );

-- Sample data (optional - for testing)
-- INSERT INTO vendor_whitelist (tenant_id, vendor_code, vendor_name, avg_amount_cents, tolerance_percent, enabled)
-- VALUES
--   ('tenant-001', 'V001', 'SAP Consulting', 50000000, 0.10, true),
--   ('tenant-001', 'V002', 'AWS', 10000000, 0.10, true),
--   ('tenant-001', 'V003', 'Google Cloud', 8000000, 0.10, true);
