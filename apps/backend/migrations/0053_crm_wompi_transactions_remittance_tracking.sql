-- Migration: Entidad A remittance tracking on crm_wompi_transactions.
-- Date: 2026-09-10
-- Purpose: Wompi collects Renta Natural payments under Entidad B's merchant credentials (existing
-- wompi-payment-integration capability), but Renta Natural is an Entidad A service. This migration
-- adds the columns needed to track whether the collected amount has actually been remitted to
-- Entidad A, so that step is never a manual, unaudited bank transfer.
-- Change: taty-wompi-entidad-a-remittance (absorbed into renta-natural-first-sale).
-- Idempotent: Can be run multiple times safely.
-- Prerequisites: none — additive, touches only crm_wompi_transactions.
--
-- NOT APPLIED. Per this repo's standing rule (CLAUDE.md, ARCHITECTURE.md Decision #23/#15),
-- migrations are written but never auto-applied to Supabase production — applying this requires
-- explicit founder confirmation. See renta-natural-first-sale/tasks.md task 3.7/2.8 for the
-- founder-approval gate.
--
-- Deliberately NOT included here: the actual payout API contract (endpoint, request/response
-- shape) is unknown until the founder confirms with Wompi support whether "Pagos a Terceros"
-- applies (tasks.md task 3.1-3.6) — adding speculative columns for a specific unconfirmed API
-- shape would risk a second migration to undo them. `remittance_status` and `remittance_error`
-- are the minimum generic tracking shape that works regardless of which payout mechanism is
-- ultimately confirmed (Pagos a Terceros API, a batch payout, or a manual reconciled transfer).

ALTER TABLE public.crm_wompi_transactions
    ADD COLUMN IF NOT EXISTS remittance_status TEXT NOT NULL DEFAULT 'pending'
        CHECK (remittance_status IN ('pending', 'sent', 'failed')),
    ADD COLUMN IF NOT EXISTS remittance_error TEXT,
    ADD COLUMN IF NOT EXISTS remitted_at TIMESTAMPTZ;

COMMENT ON COLUMN public.crm_wompi_transactions.remittance_status IS
    'Tracks whether the collected amount has been remitted to Entidad A. pending = not yet '
    'attempted (default, so historical rows are never misreported as sent); sent = payout '
    'confirmed; failed = payout attempt failed, see remittance_error. Never defaults to sent.';

COMMENT ON COLUMN public.crm_wompi_transactions.remittance_error IS
    'Failure reason from the most recent remittance attempt. NULL unless remittance_status is '
    'failed. A remittance failure never rolls back the underlying payment approval — see '
    'taty-wompi-entidad-a-remittance design.md Decision 2.';

COMMENT ON COLUMN public.crm_wompi_transactions.remitted_at IS
    'Timestamp of the confirmed successful remittance to Entidad A. NULL until remittance_status '
    'transitions to sent.';
