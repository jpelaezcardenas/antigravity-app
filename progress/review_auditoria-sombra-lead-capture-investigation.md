# Review — task auditoria-sombra-lead-capture-investigation

**Verdict:** CHANGES_REQUESTED

## Scope of review

This is an investigation-only OpenSpec change (no code changes). I independently re-read every
file cited in `design.md`'s "Decisions" section and `reports/2026-08-28-findings.md` — not the
documents' summaries — and checked every quoted line range against the real file contents.

## Checkpoints

- C1: [x] `apps/backend/services/wizard_service.py::run_auditoria_sombra` — confirmed at exact
  lines 132-209 as claimed. Calls only `CentinelaService.evaluate()` (in-memory, no
  `save_alerts()` call) and `AnalystAgent.execute()` (LLM call only via `call_llm` ->
  `llm_engine.get_ai_response`, no persistence in `base_agent.py`). Zero DB/queue/file writes in
  this call chain. Verified against the real file, matches claim.
- C2: [x] Contrast claim — `run_renta_diagnostico` (same file, lines 212-261) does call
  `CrmService().whatsapp_intake(...)` (line 251), which performs a real find (`crm_service.py:
  411-419`) then insert (`crm_service.py:423-434`) into `crm_leads`. Both line ranges verified
  exact against the real file.
- C3: [x] `apps/backend/presentation/wizard_endpoints.py` — the `/auditoria-sombra` handler is at
  exact lines 69-91 as claimed. It calls `run_auditoria_sombra`, logs one line, returns the Pydantic
  response, or raises `HTTPException` on error. No DB/queue write anywhere in the handler.
- C4: [x] `contexia-wizard/components/wizard/steps/Step8Diagnostico.tsx` — `executeAudit` calls the
  backend `/wizard/auditoria-sombra` endpoint (lines ~189-214), merges the response into local
  state and `AuditResult` (through line 249), then unconditionally (regardless of whether the
  backend call succeeded) calls `/wizard/api/audit/execute` in its own try/catch at lines 267-285.
  Confirmed this second call is not gated on any condition — it always fires once `executeAudit`
  runs.
- C5: [x] `contexia-wizard/app/api/audit/execute/route.ts` — confirmed real, unconditional
  Supabase writes via `supabaseAdmin` to the `leads` table at exact lines 26-86 (`.update()` when
  `leadId` is known, `.update()` on matched `email`, or `.insert()` for a new lead), setting
  `audit_result`, `audit_executed_at`, `status: "audited"`, `lead_score` exactly as claimed — not
  wrapped in a dedicated try/catch (only the outer function-level try/catch at line 18 guards it,
  returning a generic 500). The internal Resend notification email is a separate, self-contained
  try/catch at exact lines 88-181, confirmed not dead code — `app/api/audit/pdf/route.ts:20`
  contains the exact quoted comment about columns that actually exist in the leads table, and
  reads `audit_result` back from the same `leads` table, corroborating this is live persistence.
  `lib/store.ts` confirms the Zustand store (`auditResult`) is `localStorage`-only
  (`createJSONStorage(() => ... localStorage ...)`, lines 213-220) — device-local, as claimed.
- C6: [x] No migration creates a table for wizard/audit results. `apps/backend/migrations/0001_
  add_tenant_id_columns.sql:8-11` and `0002_backfill_tenant_id.sql:12-13` contain, verbatim, the
  quoted phrase "those agents compute their data on the fly" and confirm `pulso_results`,
  `radar_insights`, and `auditoria_reports` were planned but never created as tables. A repo-wide
  grep of `apps/backend/migrations/` for `auditoria_reports` only turns up an RBAC permission enum
  value (`0006_role_permissions_table.sql`, `0009_seed_role_permissions.sql`), never a table
  definition — consistent with the claim. `specs/phase2-llm-integration.md:297` and `:314` also
  verified verbatim, corroborating this was a known, deliberately deferred gap.
- C7: [x] `apps/backend/presentation/auditoria_sombra_endpoints.py` +
  `apps/backend/services/auditoria_sombra_service.py` confirmed genuinely separate: tenant-scoped
  (`tenant_id` required), HITL-gated via `approval_queue`/`audit_report_signoff` for external
  audience — no reference to `wizard_service` or `run_auditoria_sombra` anywhere in
  `auditoria_sombra_service.py` (grepped, zero matches). Confirmed unrelated to the GTM wizard flow.
- C8: [~] Naming-collision claim is incomplete, not wrong. design.md frames this as exactly
  "two distinct Auditoria Sombra features." A third, independent usage exists:
  `apps/backend/services/social_ops_service.py` uses "auditoria_sombra" as a B2B onboarding
  Kanban pipeline-stage id (line 26) and a Cal.com booking-link slug
  (`CALCOM_SHADOW_AUDIT_URL`, line 66, default ".../auditoria-sombra") for Taty's manual
  Nodos-Contexia sales conversations — unrelated to both the GTM wizard and the tenant PDF/HITL
  generator, and it performs no persistence relevant to this investigation's question. This does
  not change the investigation's conclusion (it is not a trace-leaving code path for the GTM
  wizard), so it is not a blocking error — but design.md's "two distinct features" framing
  undercounts by one and should be corrected or the omission should at least be acknowledged, since
  the investigation's own methodology section claims a "repo-wide search for any other
  Auditoria-Sombra-adjacent persistence/path" was performed (Task 2.1).
- C9: [x] `openspec/changes/.../specs/NO_CAPABILITY_CHANGES.md` — justified; no code changed, `git
  status` confirms only OpenSpec artifacts + harness pointers (`feature_list.json`,
  `progress/current.md`) were touched by this session, no files under `apps/backend`,
  `contexia-wizard`, or `app/` were modified.
- C10: [x] `tasks.md`'s omission of the mandatory Stage 11 section is justified and consistent with
  `CLAUDE.md` section 8, which is scoped to deploying code changes (git push -> Vercel/Railway ->
  verify in production). This change has zero deployable artifact, and the omission is explicitly
  documented in `design.md`'s Migration Plan rather than silently skipped, matching the
  self-improving-loop / documentation-first culture the repo requires. No docs-sync failure:
  `ARCHITECTURE.md` describes no container/dependency this investigation touched.
- C11: [x] `init.sh` green; `feature_list.json.active` correctly points at this change id.

## Required changes (must fix before archiving)

1. `design.md` line 47-48 — wrong line range for `CentinelaService.save_alerts()`. The text
   reads "the write-capable sibling `save_alerts()` at lines 403-424 is never invoked here." The
   actual function (`apps/backend/services/centinela_service.py`) spans lines 403-430
   (`def save_alerts` at 403 through the closing `return []` of the `except` block at 430); line
   424 is mid-loop (`saved_ids.append(result.data[0]["id"])`), not the function's end. The
   substantive claim (never invoked by `run_auditoria_sombra`) is correct — only the cited line
   range is wrong. Fix the range to 403-430 (or drop the specific end-line and just cite 403).

## Recommended, non-blocking

2. Consider a one-line addendum to design.md's "Naming collision" paragraph and/or the corresponding
   Open Question, noting the third `social_ops_service.py` pipeline-stage/Cal.com-slug usage of
   "Auditoria Sombra" (found during this review, see C8), so Subdomain 3's future tier-gating work
   does not independently rediscover it. Not required to fix before archiving since it does not
   affect the investigation's conclusion or any cited evidence.

## Summary

Every substantive factual claim in `design.md`'s Decisions section and the findings note was
independently re-verified against the real code and holds up: the backend `run_auditoria_sombra`
path is genuinely stateless; `contexia-wizard`'s `Step8Diagnostico.tsx` does unconditionally call
`/wizard/api/audit/execute`, which does perform a real, unconditional Supabase write to `leads`
(exact columns as claimed) plus a Resend notification email; the migrations evidence and the
`specs/phase2-llm-integration.md` corroboration are both verbatim-accurate; and the two-features
distinction for `auditoria_sombra_endpoints.py`/`auditoria_sombra_service.py` vs. the GTM wizard is
correct as far as it goes. The one concrete inaccuracy found (Required change #1) is a wrong line
range, not a wrong conclusion — trivial to fix, but per this review's mandate to catch exactly this
class of error before archiving, it blocks approval until corrected.
