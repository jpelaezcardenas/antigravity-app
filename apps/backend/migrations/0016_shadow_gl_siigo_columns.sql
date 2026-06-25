-- Migration 0016: Add Siigo CSV ingestion columns to erp_journal_entries
-- Purpose: Support CSV import from Siigo with idempotency + constraint validation
-- Date: 2026-06-25
-- Phase: Phase 5 (Shadow GL Real Data Ingestion)

BEGIN;

-- Add columns to erp_journal_entries for Siigo CSV import
ALTER TABLE erp_journal_entries
  ADD COLUMN IF NOT EXISTS external_reference_id TEXT,
  ADD COLUMN IF NOT EXISTS source TEXT DEFAULT 'manual',
  ADD COLUMN IF NOT EXISTS uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- Add unique constraint: (tenant_id, external_reference_id, entry_date)
-- This prevents duplicate imports of the same Siigo document on the same day
ALTER TABLE erp_journal_entries
  ADD CONSTRAINT unique_siigo_document_per_day UNIQUE (tenant_id, external_reference_id, entry_date)
  WHERE external_reference_id IS NOT NULL;

-- Add CHECK constraint to erp_journal_lines: amounts must be non-negative
-- (Negative amounts are allowed via offset/reversal entries, but individual lines cannot be negative)
ALTER TABLE erp_journal_lines
  ADD CONSTRAINT check_debit_not_negative CHECK (debit_minor >= 0),
  ADD CONSTRAINT check_credit_not_negative CHECK (credit_minor >= 0);

COMMIT;

-- Verification queries (run separately, not in transaction):
-- SELECT * FROM information_schema.columns WHERE table_name = 'erp_journal_entries' AND column_name = 'external_reference_id';
-- SELECT * FROM information_schema.table_constraints WHERE table_name = 'erp_journal_entries' AND constraint_name = 'unique_siigo_document_per_day';
-- SELECT * FROM information_schema.check_constraints WHERE table_name = 'erp_journal_lines' AND constraint_name LIKE 'check_%not_negative';
