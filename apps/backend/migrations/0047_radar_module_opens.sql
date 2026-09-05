-- Migration: 0047_radar_module_opens
-- Records one row per tenant + user + day when the Radar de Caja 13-week projection
-- is opened, feeding the adoption KPI ">=40% of active users open Radar de Caja at
-- least once a week" (radar-adoption-tracking).
--
-- Day-grain by design: the KPI is weekly, and a unique row per day keeps the table's
-- size proportional to real usage rather than to renders.
--
-- RLS follows 0045_metrics_snapshots' tenant-scoped pattern. It deliberately does NOT
-- use the permissive `USING (true)` shape carried by erp_journal_entries /
-- erp_journal_lines / dian_xml_documents, which the 2026-09-05 masterprompt audit
-- flags as providing no database-level isolation at all.

CREATE TABLE IF NOT EXISTS public.radar_module_opens (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id   UUID NOT NULL,
    -- Nullable: the staging identity (AUTH_ENFORCED=False, no token) resolves to a
    -- tenant but has no auth.uid(). Recording the open with a NULL user is more honest
    -- than dropping it or inventing an id.
    user_id     UUID,
    opened_on   DATE NOT NULL DEFAULT CURRENT_DATE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT chk_radar_module_opens_not_future CHECK (opened_on <= CURRENT_DATE)
);

-- Two partial unique indexes rather than one constraint: in Postgres, NULLs are
-- distinct, so a plain UNIQUE (tenant_id, user_id, opened_on) would let the staging
-- identity insert unlimited rows per day.
--
-- Consequence for the caller: these are PARTIAL indexes, and Postgres cannot infer a
-- partial index for ON CONFLICT. record_module_open therefore issues a plain INSERT and
-- treats 23505 as "already recorded today" rather than using upsert.
CREATE UNIQUE INDEX IF NOT EXISTS uq_radar_module_opens_tenant_user_day
    ON public.radar_module_opens (tenant_id, user_id, opened_on)
    WHERE user_id IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS uq_radar_module_opens_tenant_anon_day
    ON public.radar_module_opens (tenant_id, opened_on)
    WHERE user_id IS NULL;

-- Supports the weekly rollup query in design.md.
CREATE INDEX IF NOT EXISTS idx_radar_module_opens_tenant_day
    ON public.radar_module_opens (tenant_id, opened_on DESC);

ALTER TABLE public.radar_module_opens ENABLE ROW LEVEL SECURITY;

-- Tenant isolation: an authenticated user sees only their own tenants' opens.
CREATE POLICY radar_module_opens_tenant_isolation
    ON public.radar_module_opens
    FOR ALL
    USING (
        tenant_id IN (
            SELECT tenant_id FROM public.user_tenants
            WHERE user_id = auth.uid()
        )
    );

-- Service role bypass: the backend writes these rows on behalf of every tenant.
CREATE POLICY radar_module_opens_service_role
    ON public.radar_module_opens
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);
