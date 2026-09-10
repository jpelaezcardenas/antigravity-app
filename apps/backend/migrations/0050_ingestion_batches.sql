-- Migration 0050: ingestion_batches table
-- Date: 2026-09-09
--
-- Migration 0019_shadow_gl_siigo_ingestion.sql intended to create this table but had
-- three real Postgres syntax errors that made the whole script fail on execution,
-- silently, before ever reaching CREATE TABLE ingestion_batches:
--   1. `ALTER TABLE ... ADD COLUMN IF NOT EXISTS (col1, col2, ...)` — invalid; Postgres
--      requires one ADD COLUMN clause per column.
--   2. `ADD CONSTRAINT ... UNIQUE (...) WHERE ...` — a partial unique constraint must be
--      a CREATE UNIQUE INDEX ... WHERE ..., not an ADD CONSTRAINT with a WHERE clause.
--   3. `CREATE POLICY IF NOT EXISTS ...` — Postgres has no IF NOT EXISTS for CREATE POLICY.
--
-- The other columns 0019 tried to add to erp_journal_entries (external_reference_id,
-- source, uploaded_at, is_verified_real) already exist in production, added by some
-- other corrective path — confirmed live via information_schema before writing this.
-- Only `ingestion_batches` itself, and the erp_journal_entries.upload_batch_id column,
-- were genuinely missing. upload_batch_id has no caller in the current codebase
-- (grepped), so it is deliberately NOT added here — no dead column.
--
-- Found while diagnosing "Failed to create batch record" on every real upload attempt
-- (CSV/XLSX/PDF alike) from CÓDIGO 520's Track 1 pilot test — the INSERT into this
-- nonexistent table failed before any file parsing ever started.

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
  uploaded_at timestamptz DEFAULT now(),
  processed_at timestamptz,
  completed_at timestamptz,
  created_at timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ingestion_batches_tenant
  ON ingestion_batches (tenant_id, uploaded_at DESC);

CREATE INDEX IF NOT EXISTS idx_ingestion_batches_status
  ON ingestion_batches (tenant_id, status);

-- RLS enabled but permissive, matching the existing precedent already live on its
-- sibling table erp_journal_entries (erp_journal_entries_anon_all: USING true / WITH
-- CHECK true for anon/authenticated/service_role) — tenant isolation for this pipeline
-- is enforced at the FastAPI layer (_resolve_tenant_from_scope), not at the RLS layer,
-- a known and already-documented simplification (ARCHITECTURE.md Decisión #14's open
-- item re: approval_queue_anon_all). The originally-intended stricter policy in 0019
-- referenced user_roles.role_name, a column that does not exist in production (the
-- real column is `role`) — reusing that would have reproduced the same silent-failure
-- class of bug this migration exists to fix.
ALTER TABLE ingestion_batches ENABLE ROW LEVEL SECURITY;

CREATE POLICY ingestion_batches_anon_all
  ON ingestion_batches
  FOR ALL
  TO anon, authenticated, service_role
  USING (true)
  WITH CHECK (true);

COMMENT ON TABLE ingestion_batches IS 'Tracks CSV/XLSX/XML/PDF uploads (Track 1 self-service + Track 2/3 pollers) for audit and error handling.';

SELECT '✅ 0050 ingestion_batches complete' AS status;
