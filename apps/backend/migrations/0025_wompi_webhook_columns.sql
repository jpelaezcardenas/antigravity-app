-- Migration 0025: Prepare crm_wompi_transactions for real Wompi webhook handling
-- Wompi (Bancolombia) payment integration, Change C — see
-- openspec/changes/wompi-payment-integration and the original table from
-- openspec/changes/archive/2026-07-19-crm-b2c-sell-machine-cockpit
-- (0022_crm_b2c_sell_machine.sql), whose design doc explicitly reserved this
-- table for Change C to wire real webhook verification onto.
-- Date: 2026-07-19

-- 1. Allow idempotent upsert-by-Wompi-transaction-id: Wompi may redeliver the
--    same event, and wompi_transaction_id was not previously unique (rows
--    were only seeded, never written by a real webhook).
CREATE UNIQUE INDEX IF NOT EXISTS uq_crm_wompi_transactions_wompi_id
    ON crm_wompi_transactions (wompi_transaction_id)
    WHERE wompi_transaction_id IS NOT NULL;

-- 2. Widen the status CHECK to the full set of Wompi transaction statuses.
--    The original constraint only allowed PENDING/APPROVED/DECLINED because
--    only manual HITL approval wrote to this column before Change C.
ALTER TABLE crm_wompi_transactions DROP CONSTRAINT IF EXISTS chk_crm_wompi_transactions_status;
ALTER TABLE crm_wompi_transactions ADD CONSTRAINT chk_crm_wompi_transactions_status
    CHECK (status IN ('PENDING', 'APPROVED', 'DECLINED', 'VOIDED', 'ERROR'));

SELECT '✅ Migration 0025 complete: crm_wompi_transactions ready for real Wompi webhook writes' AS status;
