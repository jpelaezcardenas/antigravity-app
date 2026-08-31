-- Migration: 0045_metrics_snapshots
-- Creates metrics_snapshots table for Phase 9 operational dashboard.
-- Stores pre-computed daily metrics per tenant (nightly job writes, API reads).

CREATE TABLE IF NOT EXISTS public.metrics_snapshots (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id                   UUID NOT NULL,
    snapshot_date               DATE NOT NULL,

    -- Auto-approval metrics
    auto_approved_total         INTEGER NOT NULL DEFAULT 0,
    auto_approved_recurring     INTEGER NOT NULL DEFAULT 0,
    auto_approved_vendor        INTEGER NOT NULL DEFAULT 0,
    auto_approved_micro         INTEGER NOT NULL DEFAULT 0,
    false_positive_count        INTEGER NOT NULL DEFAULT 0,

    -- CSV ingestion metrics
    csv_batches_total           INTEGER NOT NULL DEFAULT 0,
    csv_rows_processed          INTEGER NOT NULL DEFAULT 0,
    csv_rows_error              INTEGER NOT NULL DEFAULT 0,

    -- Queue health
    queue_pending_count         INTEGER NOT NULL DEFAULT 0,
    queue_avg_review_seconds    NUMERIC(10, 2),

    -- Top vendors (JSON array of {vendor: str, count: int})
    top_vendors                 JSONB NOT NULL DEFAULT '[]',

    computed_at                 TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT uq_metrics_snapshots_tenant_date UNIQUE (tenant_id, snapshot_date),
    CONSTRAINT chk_metrics_snapshots_date CHECK (snapshot_date <= CURRENT_DATE)
);

CREATE INDEX IF NOT EXISTS idx_metrics_snapshots_tenant_date
    ON public.metrics_snapshots (tenant_id, snapshot_date DESC);

ALTER TABLE public.metrics_snapshots ENABLE ROW LEVEL SECURITY;

-- Tenant isolation: authenticated users see only their own tenant's metrics
CREATE POLICY metrics_snapshots_tenant_isolation
    ON public.metrics_snapshots
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.user_tenants
            WHERE user_id = auth.uid()
        )
    );

-- Service role bypass (for nightly computation job)
CREATE POLICY metrics_snapshots_service_role
    ON public.metrics_snapshots
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
