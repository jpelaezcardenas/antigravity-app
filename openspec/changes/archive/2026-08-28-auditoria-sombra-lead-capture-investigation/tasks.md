## 1. Trace the backend call chain

- [x] 1.1 Read `run_auditoria_sombra` (`apps/backend/services/wizard_service.py:132-209`) in full;
      confirm whether it calls any repository/Supabase/queue/file write, directly or transitively.
- [x] 1.2 Read `CentinelaService.evaluate()` and `save_alerts()`
      (`apps/backend/services/centinela_service.py`) to confirm which method actually persists, and
      confirm `run_auditoria_sombra` only calls the non-persisting one.
- [x] 1.3 Read `AnalystAgent.execute()` (`apps/backend/agents/agent_6_analyst.py`) and its
      `call_llm` dependency (`apps/backend/agents/base_agent.py`) to confirm the LLM call is
      outbound-only, not a persistence call.
- [x] 1.4 Read the sibling function `run_renta_diagnostico` (same file) as the contrast case, and
      confirm `CrmService.whatsapp_intake` (`apps/backend/services/crm_service.py`) performs a real
      find-then-insert into `crm_leads`.

## 2. Search for any other persistence path

- [x] 2.1 Grep the full repo (backend services/presentation/migrations/tests, `openspec/`, `specs/`)
      for any table, migration, background job, or design-doc reference tying Auditoria Sombra
      results to a persisted lead record.
- [x] 2.2 Confirm no migration ever created a table for wizard/audit results (checked migrations
      0001, 0002 — an `auditoria_reports` table was planned and explicitly removed before it ever
      existed).
- [x] 2.3 Identify and document the unrelated second "Auditoria Sombra" feature
      (`apps/backend/presentation/auditoria_sombra_endpoints.py` +
      `apps/backend/services/auditoria_sombra_service.py`) so it isn't conflated with the GTM
      wizard flow in future work.

## 3. Trace the real-world caller (frontend)

- [x] 3.1 Find the FastAPI endpoint that calls `run_auditoria_sombra`
      (`apps/backend/presentation/wizard_endpoints.py`) and confirm it does nothing with the result
      beyond logging and returning it.
- [x] 3.2 Find where `contexia-wizard` calls this endpoint
      (`contexia-wizard/components/wizard/steps/Step8Diagnostico.tsx`) and trace what happens to
      the response client-side.
- [x] 3.3 Confirm whether the frontend persists the result anywhere durable, not just
      `localStorage` (`contexia-wizard/lib/store.ts`) — found: it does, via a second Next.js route.
- [x] 3.4 Read `contexia-wizard/app/api/audit/execute/route.ts` in full and confirm the exact
      Supabase write (table, columns, conditional vs. unconditional) and the internal notification
      email side effect.

## 4. Verify the central claim adversarially

- [x] 4.1 Run 3 independent verification passes against the compiled evidence, each instructed to
      try to refute "Auditoria Sombra persists nothing anywhere in the codebase," defaulting to
      refuted=true on any credible evidence of persistence.
- [x] 4.2 Reconcile the verification results: 2 of 3 refuted the broad framing (correctly, per the
      frontend write found in Section 3); the 1 non-refuting result had explicitly scoped its check
      to the backend only, so it is not in tension with the other two.

## 5. Independent spot-check (trust but verify)

- [x] 5.1 Re-read `apps/backend/services/wizard_service.py:130-209` directly (not via subagent
      summary) and confirm it matches the quoted evidence verbatim.
- [x] 5.2 Re-read `contexia-wizard/app/api/audit/execute/route.ts` directly and confirm the
      Supabase write and email notification match the quoted evidence verbatim.

## 6. Write the deliverable

- [x] 6.1 Write the full findings, evidence, and design decisions into `design.md`.
- [x] 6.2 Write a founder/engineering-readable findings note to
      `reports/2026-08-28-findings.md`, distinct from `design.md`, as the standalone deliverable
      this investigation subdomain calls for.
- [x] 6.3 Confirm no code, spec, or living-doc changes are needed as part of *this* change — open
      items are recorded as follow-up questions in `design.md`, not silently fixed here.

Note: no Stage 11 (Deploy to Production) section — this change makes no code or infrastructure
change; see `design.md`'s Migration Plan for why that section is deliberately omitted rather than
left as an unchecked box.
