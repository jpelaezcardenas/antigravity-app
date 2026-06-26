-- Phase 8 Stage 1: Shadow GL Siigo CSV Ingestion
-- Adds columns for tracking CSV uploads and deduplication

-- Extend erp_journal_entries with source tracking
ALTER TABLE erp_journal_entries ADD COLUMN IF NOT EXISTS (
  external_reference_id varchar(255),
  source varchar(50) DEFAULT 'manual',
  uploaded_at timestamp DEFAULT now(),
  upload_batch_id uuid
);

-- Add unique constraint for idempotency
-- Upsert key: (tenant_id, external_reference_id, entry_date)
ALTER TABLE erp_journal_entries
ADD CONSTRAINT uq_erp_entries_dedup UNIQUE (
  tenant_id,
  external_reference_id,
  entry_date
) WHERE external_reference_id IS NOT NULL;

-- Add indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_erp_entries_external_ref
  ON erp_journal_entries (tenant_id, external_reference_id)
  WHERE external_reference_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_erp_entries_upload_batch
  ON erp_journal_entries (upload_batch_id)
  WHERE upload_batch_id IS NOT NULL;

-- Add constraint to erp_journal_lines: amounts must be non-negative
ALTER TABLE erp_journal_lines
ADD CONSTRAINT check_amounts_non_negative
CHECK (debit_amount_cents >= 0 AND credit_amount_cents >= 0);

-- Create ingestion_batches table for tracking uploads
CREATE TABLE IF NOT EXISTS ingestion_batches (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id uuid NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  data_source varchar(50) NOT NULL,
  file_name varchar(255),
  file_size_bytes bigint,
  row_count int,
  status varchar(50) DEFAULT 'pending',
  error_count int DEFAULT 0,
  error_summary jsonb,
  uploaded_by uuid REFERENCES auth.users(id),
  uploaded_at timestamp DEFAULT now(),
  processed_at timestamp,
  completed_at timestamp,
  created_at timestamp DEFAULT now()
);

-- Index for admin queries
CREATE INDEX IF NOT EXISTS idx_ingestion_batches_tenant
  ON ingestion_batches (tenant_id, uploaded_at DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_batches_status
  ON ingestion_batches (tenant_id, status);

-- Enable RLS on ingestion_batches
ALTER TABLE ingestion_batches ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Only admins can view/manage batches
CREATE POLICY IF NOT EXISTS ingestion_batches_admin_only ON ingestion_batches
  FOR ALL
  USING (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = ingestion_batches.tenant_id
      AND role_name IN ('admin', 'accountant')
    )
  )
  WITH CHECK (
    auth.uid() IN (
      SELECT user_id FROM user_roles
      WHERE tenant_id = ingestion_batches.tenant_id
      AND role_name = 'admin'
    )
  );

-- Comments for documentation
COMMENT ON COLUMN erp_journal_entries.external_reference_id IS 'Reference from source system (e.g., Siigo transaction ID)';
COMMENT ON COLUMN erp_journal_entries.source IS 'Data source: manual, siigo_csv, dian_xml, api';
COMMENT ON COLUMN erp_journal_entries.upload_batch_id IS 'Groups entries from same batch upload';
COMMENT ON TABLE ingestion_batches IS 'Tracks CSV/XML uploads for audit and error handling';
