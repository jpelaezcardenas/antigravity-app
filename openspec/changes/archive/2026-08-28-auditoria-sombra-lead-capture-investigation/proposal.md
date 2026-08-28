## Why

The freemium-onboarding master plan (Subdomain 5, `freemium-tenant-minimum-seed`) assumed Auditoria
Sombra was a stateless dead end: a prospect completes the shadow audit, and if they don't book a
discovery call immediately, the sales team has no record to follow up on. That assumption was never
verified against the actual code — it was inferred from `wizard_service.py::run_auditoria_sombra`
looking read-only at a glance, in contrast to `CrmService.whatsapp_intake` (used by the sibling
`run_renta_diagnostico` function), which is known to write to `crm_leads`. Before designing Subdomain
5's persistence work, we need to know whether that gap is real or already closed elsewhere.

## What Changes

- No code changes. This change produces a findings note answering: does completing Auditoria Sombra
  leave any queryable trace before the discovery call, and if so, where?
- The investigation traced the full call chain of `run_auditoria_sombra` (backend, Python) AND its
  only known real-world caller, the `contexia-wizard` Next.js app, since the backend function alone
  does not represent how the flow is actually exercised in production.
- Finding (see `design.md` for full evidence): the backend service function and its FastAPI endpoint
  are genuinely stateless — no DB/queue/file write anywhere in that call chain. But the production
  flow as a whole is **not** stateless: `contexia-wizard`'s `Step8Diagnostico.tsx` unconditionally
  calls its own Next.js route (`app/api/audit/execute/route.ts`) immediately after every audit,
  which writes the result to Supabase's `leads` table and fires an internal notification email. So
  today, in production, a completed Shadow Audit already leaves a trace — just not inside
  `apps/backend`, and not via the pattern (`crm_leads`) this investigation was originally pointed at.

## Capabilities

### New Capabilities
(none — investigation only, no new capability introduced)

### Modified Capabilities
(none — no spec-level behavior is changing; this note informs future design work in Subdomains 3
and 5, which will carry their own capability changes if/when they proceed)

## Impact

- No affected code, APIs, or systems — read-only investigation.
- Informs `openspec/changes/plan-tier-feature-gating` (Subdomain 3) and
  `openspec/changes/freemium-tenant-minimum-seed` (Subdomain 5) design work, not yet started.
- Files read (no changes): `apps/backend/services/wizard_service.py`,
  `apps/backend/services/centinela_service.py`, `apps/backend/agents/agent_6_analyst.py`,
  `apps/backend/services/crm_service.py`, `apps/backend/presentation/wizard_endpoints.py`,
  `apps/backend/presentation/auditoria_sombra_endpoints.py`,
  `apps/backend/services/auditoria_sombra_service.py`, `apps/backend/migrations/0001`, `0002`,
  `0022`, `0040`, `specs/phase2-llm-integration.md`,
  `contexia-wizard/components/wizard/steps/Step8Diagnostico.tsx`, `contexia-wizard/lib/store.ts`,
  `contexia-wizard/app/api/audit/execute/route.ts`, `contexia-wizard/app/api/audit/pdf/route.ts`.
