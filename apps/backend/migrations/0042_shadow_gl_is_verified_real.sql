-- Migration 0042: Add is_verified_real data-integrity flag to Shadow GL tables
-- Date: 2026-08-18
-- Change: shadow-gl-data-integrity-flag
--
-- Context: audit on 2026-08-18 found erp_journal_entries (73 rows) and dian_xml_documents
-- (4 rows) are 100% synthetic/fixture data despite prior "Phase 5 COMPLETE" reports claiming
-- real production data. Real data will come from Siigo (Contexia's paid subscription) via
-- manual accountant export through the existing ingestion endpoints. This flag lets a future
-- upload declare itself as a genuine Siigo/DIAN export vs. a fixture/test, defaulting to false
-- everywhere so nothing is silently treated as real. See design.md for full rationale.
--
-- NOT NULL DEFAULT false on ADD COLUMN backfills every existing row to false automatically --
-- no separate UPDATE statement is needed.

ALTER TABLE erp_journal_entries
  ADD COLUMN IF NOT EXISTS is_verified_real BOOLEAN NOT NULL DEFAULT false;

ALTER TABLE dian_xml_documents
  ADD COLUMN IF NOT EXISTS is_verified_real BOOLEAN NOT NULL DEFAULT false;

SELECT '✅ 0042 shadow_gl_is_verified_real complete' AS status;
