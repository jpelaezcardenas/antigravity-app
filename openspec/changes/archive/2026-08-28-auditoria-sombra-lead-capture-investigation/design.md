## Context

Subdomain 5 of the freemium-onboarding master plan (`freemium-tenant-minimum-seed`) was designed
around an unverified assumption: that Auditoria Sombra is purely synchronous compute-and-return,
so a prospect who completes it without booking a discovery call leaves zero trace for the sales
team. This assumption came from a glance at `wizard_service.py::run_auditoria_sombra` next to its
sibling `run_renta_diagnostico` (which is known to write to `crm_leads` via
`CrmService.whatsapp_intake`). This investigation traces the full call chain of both functions —
including the real-world caller, not just the backend function in isolation — to confirm or refute
that assumption before any code is designed against it.

Method: a multi-agent workflow ran 5 independent explorers in parallel (backend function trace,
sibling-function contrast, the known-good `crm_leads` persistence pattern, a repo-wide search for
any other Auditoria-Sombra-adjacent persistence path, and the frontend/endpoint wiring), followed
by 3 independent adversarial verifiers instructed to try to refute the central "no persistence
anywhere" claim, followed by a synthesis pass. The two highest-stakes claims (the backend function
being side-effect-free, and the frontend route performing a real Supabase write) were independently
re-verified by directly reading `apps/backend/services/wizard_service.py:132-209` and
`contexia-wizard/app/api/audit/execute/route.ts` in full before writing this document — both match
the workflow's evidence verbatim.

## Goals / Non-Goals

**Goals:**
- Determine definitively whether completing Auditoria Sombra leaves any durable, queryable record
  before a discovery call is booked.
- If it does, identify exactly where (which system, which table, which code path) so Subdomains 3
  and 5 design against reality instead of an assumption.
- Surface any adjacent gaps found along the way (e.g. Centinela alerts never being persisted) as
  explicitly scoped follow-up items, not silently absorbed into this investigation's conclusion.

**Non-Goals:**
- No code changes. This is a read-only investigation; any fix belongs to a future change.
- Not re-litigating the two distinct "Auditoria Sombra" features found in the repo (the GTM wizard
  vs. the tenant-facing PDF/HITL report generator) beyond flagging the naming collision — that
  reconciliation is out of scope here.

## Decisions

**Finding — the trace exists, but not where the plan assumed it would.**

Whether Auditoria Sombra leaves a queryable trace depends on which layer of the system is asked:

- **Backend (`apps/backend`) — genuinely stateless.** `run_auditoria_sombra`
  (`apps/backend/services/wizard_service.py:132-209`) takes no DB/repository dependency. It builds
  a synthetic profile in memory, calls `CentinelaService.evaluate()`
  (`apps/backend/services/centinela_service.py:384-401`, a pure in-memory rule loop — the
  write-capable sibling `save_alerts()` at lines 403-430 is never invoked here), calls
  `AnalystAgent.execute()` (`apps/backend/agents/agent_6_analyst.py:53-72`, an outbound LLM call
  only), and returns a plain dict. Its only caller,
  `apps/backend/presentation/wizard_endpoints.py:69-91`, logs one line and returns the dict — no
  DB/queue/audit_log write. No migration ever created a table for wizard/audit results; migrations
  `0001` and `0002` explicitly document that a planned `auditoria_reports` table was removed
  because "those agents compute their data on the fly." `specs/phase2-llm-integration.md:297,314`
  independently corroborates this was a known, deliberately deferred gap, not an overlooked one.
  Contrast: the sibling `run_renta_diagnostico` (wizard_service.py:250-254) calls
  `CrmService().whatsapp_intake(...)`, which does a real find-then-insert into Supabase `crm_leads`
  (`crm_service.py:411-419` / `423-434`) — confirming the codebase has a working persistence
  pattern available that `run_auditoria_sombra` simply doesn't use.

- **Frontend (`contexia-wizard`) — persistence DOES occur here, on the happy path.**
  `contexia-wizard` is the only known real-world caller of the backend's `/wizard/auditoria-sombra`
  endpoint, and per `ARCHITECTURE.md`'s container table it is a first-class part of this same
  product (Vercel, `contexia-wizard.vercel.app`), not a separate unrelated project.
  `Step8Diagnostico.tsx:189-249` calls that backend endpoint and merges the response into local
  `AuditResult` state (itself only `localStorage`-persisted via Zustand — device-local). Immediately
  after (`Step8Diagnostico.tsx:266-285`), it unconditionally calls the wizard app's own Next.js
  route, `/wizard/api/audit/execute`. That route
  (`contexia-wizard/app/api/audit/execute/route.ts:26-86`, read in full) performs a real,
  unconditional Supabase write via `supabaseAdmin` — `.update()` (existing lead, keyed by `leadId`
  or matched `email`) or `.insert()` (new lead, capturing `nombre`/`cedula`/`email`/`whatsapp`/
  `ciudad`/`rol` plus `ip_address`/`user_agent`/`referrer`) — setting `audit_result`,
  `audit_executed_at`, `status: "audited"`, `lead_score`. This write is a first-class statement,
  not wrapped in the try/catch that guards only the subsequent step. That same route
  (lines 88-181) also sends an internal team notification email via Resend, summarizing risks,
  potential savings, and readiness score, with quick WhatsApp/Cal.com action links. A separate
  route, `contexia-wizard/app/api/audit/pdf/route.ts`, reads `audit_result` back from `leads`
  ("Columns that actually exist in the leads table"), confirming this is live, functioning
  persistence — not dead code.

- **Net:** any consumer that calls the backend endpoint directly (bypassing `contexia-wizard`), or
  any future flow that doesn't replicate that second call, would leave zero trace. But as actually
  shipped today, a completed Shadow Audit through the real product already lands in Supabase
  `leads` and triggers an internal email — the sales team is not currently losing these leads.

**Adversarial verification result:** 2 of 3 independent verifiers refuted the "no persistence
anywhere in the codebase" framing on exactly this basis — the narrow backend-function claim held up
under independent re-reading, but the broader "the Auditoria Sombra flow leaves zero trace" framing
did not once the frontend's second API call was included. The one verifier who did not refute had
explicitly scoped their check to "the backend function and everything it calls" and did not
re-examine the frontend route — narrower in scope, not in tension with the other two. This
investigation's own spot-check (reading both files in full directly, independent of any subagent)
confirms the frontend write is real and matches the quoted evidence verbatim.

**Naming collision flagged, not resolved here:** two distinct "Auditoria Sombra" features exist in
this repo — the public GTM wizard (`run_auditoria_sombra`, pre-signup, no tenant, the one
investigated here) and an unrelated tenant-facing PDF/HITL report generator
(`apps/backend/presentation/auditoria_sombra_endpoints.py` +
`apps/backend/services/auditoria_sombra_service.py`, gated via `approval_queue` for existing
tenants). Subdomain 3's plan-tier gating must not conflate the two. (A third, unrelated usage of
the same words also exists in `apps/backend/services/social_ops_service.py` — a Kanban
pipeline-stage id and a Cal.com booking-link slug, neither of which touches persistence or plan
tiers — noted here only so a future reader doesn't mistake it for a third real feature.)

## Risks / Trade-offs

- [Risk] Subdomain 5 could be designed to add persistence that already exists, wasting effort and
  potentially creating two competing write paths (backend + frontend) for the same lead record. →
  Mitigation: Subdomain 5's design must first confirm whether its entry point is `contexia-wizard`
  (already captures leads via `leads` table) or a new/different surface that talks to the backend
  directly (would need an equivalent write path built or reused) — see Open Questions.
- [Risk] The existing persistence in `contexia-wizard/app/api/audit/execute/route.ts` has no
  retry/alerting if the Supabase write or the Resend email silently fails (the write is
  unconditional but not itself wrapped in a surfaced-error path beyond a generic 500; the email is
  in its own swallow-and-log try/catch). If freemium onboarding depends on this path, a silent
  failure would look identical to "everything worked" from the prospect's side. → Mitigation:
  flagged as a founder decision below; not fixed in this investigation.
- [Risk] `run_auditoria_sombra` never calls `CentinelaService.save_alerts()`, so even when a lead is
  captured via `contexia-wizard`, the underlying Centinela alerts are not persisted with tenant
  scoping — only the LLM-merged `AuditResult` summary lands in `leads.audit_result`. If Subdomain 3
  needs the raw, structured alerts (not just the narrative summary) for plan-tier gating, this gap
  would need to be closed first. → Mitigation: flagged as an open question below.

## Migration Plan

Not applicable — this change makes no code or infrastructure changes. Nothing to deploy, nothing to
roll back. Stage 11 (deploy to production) does not apply to this change for that reason; the
`tasks.md` for this change will not include the mandatory Stage 11 section that code-bearing
changes require, since there is no deployable artifact — recorded here explicitly per
`CLAUDE.md` §8's "close the loop" intent, so a future reader doesn't read an empty Stage 11 as a
missed step.

## Open Questions

- [ENGINEERING] Confirm whether the freemium-tenant-minimum-seed flow (Subdomain 5) will route
  through the existing `contexia-wizard` `/wizard/api/audit/execute` path, or through a new/direct
  backend integration — this determines whether any new persistence work is needed at all.
- [ENGINEERING] Confirm whether Subdomain 3's plan-tier gating needs the raw, tenant-scoped
  Centinela alerts (not just the merged `AuditResult` summary) and, if so, whether
  `CentinelaService.save_alerts()` needs to be wired into `run_auditoria_sombra` or a follow-up
  flow.
- [ENGINEERING] Reconcile the two distinct "Auditoria Sombra" features (GTM wizard vs.
  tenant-facing PDF/HITL report) before writing any plan-tier feature-gating rule keyed on
  "has this tenant used Auditoria Sombra."
- [ENGINEERING] Verify whether the `.claude/worktrees/*` copies of `contexia-wizard` (one was
  observed to contain an extra `app/api/leads/save/route.ts` not present in the main checkout)
  represent stale/divergent persistence logic that could ship inconsistently if merged carelessly.
- [FOUNDER ACTION] Decide whether the current best-effort persistence (Supabase `leads` write +
  internal Resend email, no explicit retry/alerting on failure) meets the reliability bar needed
  for the freemium sales-follow-up motion, or whether Subdomain 5 should harden this path (e.g.
  queue-based retry, dedicated audit-log table).
- [FOUNDER ACTION] Confirm the swallowed exception in `run_renta_diagnostico`
  (`wizard_service.py:253-254`, log-only on CRM write failure) and the equivalent try/catch around
  the notification email in `route.ts:88-181` are acceptable failure modes for a paid/gated
  freemium funnel, or whether failures there should be surfaced/alerted rather than silently
  logged.
