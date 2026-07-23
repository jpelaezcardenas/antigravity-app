# Implementation report — Section 9 (Update Technical Documentation)

Change: `openspec/changes/approval-queue-tenant-scoping/`
Tasks: 9.1, 9.2, 9.3 (all `[x]` in `tasks.md`)

## Scope discipline

Did NOT touch: migration application (8.3-8.5), Section 10 (deploy/push), Section 11 (archive),
any production Python code, or the migration SQL file itself. Confirmed via `git status --short`
before commit — only the 4 files below (plus this report) changed.

## Files touched

1. `ARCHITECTURE.md` (repo root) — added Decisión #14, extending Decisión #13
2. `openspec/specs/approval-queue/spec.md` — synced delta spec's `ADDED Requirements`
3. `openspec/changes/hermes-multi-tenant-wrapper/tasks.md` — added a follow-up note tracking
   the deferred RLS cleanup
4. `openspec/changes/approval-queue-tenant-scoping/tasks.md` — checked off 9.1-9.3

## 9.1 — ARCHITECTURE.md

Read Decisión #13 in full ("Decisiones asentadas") first — it documents per-tenant financials
scoping and is written in Spanish, so Decisión #14 matches that language and the terse style of
the surrounding numbered list. Added as a new numbered decision (14) rather than editing #13 in
place, since #13 is itself referenced elsewhere and should stay historically accurate to what it
originally described (financials); #14 explicitly says it extends the same pattern.

Exact text added (appended after Decisión #13, before the `## Enlaces canónicos` section):

> 14. **Approval Queue sigue el mismo patrón de tenant-scoping de Decisión #13** (2026-07-23) —
> los 4 endpoints `/api/v1/approval-queue/*` (list/enqueue/approve/reject) resuelven el tenant
> del caller vía el helper compartido `core/tenant_context.py::resolve_request_tenant_scope(user,
> client)`, no duplicado de `identity_resolver`. Un caller cuyo tenant resuelto es Cliente Cero se
> trata como **operador Contexia**: ve y actúa sobre la cola de todos los tenants (decisión HITL
> del fundador, registrada en `openspec/changes/approval-queue-tenant-scoping/design.md`), en vez
> de recibir el trato de "cliente sin tenant → vacío" de la Decisión #13. Un cliente B2B normal
> solo ve/opera su propia cola; un caller autenticado sin tenant resuelto nunca cae a Cliente
> Cero (lista vacía en lectura, 403 en escritura). `enqueue_draft`/`approve_draft`/`reject_draft`
> exigen `tenant_id` explícito — sin default silencioso. `approval_queue.tenant_id` pasa a `NOT
> NULL` sin default (migración `0033`, aplicación en vivo pendiente de confirmación explícita del
> fundador — ver `openspec/changes/approval-queue-tenant-scoping/tasks.md` §8.3). Pendiente
> documentado (no bloqueante): retirar la política RLS permisiva `approval_queue_anon_all`
> (propiedad de `hermes-multi-tenant-wrapper`) y refactorizar `financials_endpoints.py` para
> reusar `resolve_request_tenant_scope` en vez de su resolución propia — ver `design.md` §"Out of
> scope".

## 9.2 — Sync delta spec into main specs

Discovered `openspec/specs/approval-queue/spec.md` already exists (from an earlier archived
change, `add-pgvector-agent-critic-phase-3` — 3 requirements about Agent Critic validation and
vectorization). Read `ai-specs/skills/openspec-sync-specs/SKILL.md` directly (Skill tool
invocation not available to this subagent) and followed its documented rule for `## ADDED
Requirements`: "If requirement doesn't exist in main spec → add it." All 6 requirements in the
change's delta spec (`openspec/changes/approval-queue-tenant-scoping/specs/approval-queue/spec.md`)
are genuinely new (none overlap with the 3 existing Agent-Critic requirements), so I appended
them verbatim to the end of `openspec/specs/approval-queue/spec.md`'s `## Requirements` section,
preserving all 3 existing requirements unchanged. Added requirements:
- "Approval queue endpoints require authentication"
- "Drafts are stamped with the caller's resolved tenant, never a silent default"
- "Reads and decisions are scoped to the caller's tenant"
- "A Contexia operator sees and can act on every tenant's queue"
- "An authenticated caller with no resolved tenant never defaults to Cliente Cero"
- "The unauthenticated local/staging path preserves existing behavior"
- "`approval_queue.tenant_id` is enforced NOT NULL at the schema level"

Did not archive the change (out of scope — Section 11).

## 9.3 — Deferred follow-ups

**RLS policy cleanup** (owned by `hermes-multi-tenant-wrapper`): added a follow-up paragraph to
`openspec/changes/hermes-multi-tenant-wrapper/tasks.md`, placed directly after "Ground Truth
Correction #3" (the section that most recently touched `approval_queue_anon_all` and the
service-role-client migration), before the `## Grouping & Dependencies` header. Exact text added:

> **Follow-up noted by `approval-queue-tenant-scoping` (2026-07-23):** that change added
> application-layer tenant scoping to all `/api/v1/approval-queue/*` endpoints (explicit
> `tenant_id` on every write, `resolve_request_tenant_scope` on every read/write) and made
> `approval_queue.tenant_id` `NOT NULL` (migration `0033`) — but explicitly left the permissive
> RLS policy cleanup out of scope, deferring it here, to this section's still-open item: **drop
> `approval_queue_anon_all`** (line 117 above) now that (a) both services write via the
> service-role client (Layer 2, above) and (b) `tenant_id` is guaranteed non-null at write time.
> The application-layer defense (explicit `tenant_id` + endpoint auth) is live and sufficient on
> its own for now; dropping the permissive policy is defense-in-depth hygiene, not a correctness
> requirement, and remains this change's responsibility to schedule. See
> `openspec/changes/approval-queue-tenant-scoping/design.md` §"Out of scope".

**Financials refactor follow-up** (reuse `resolve_request_tenant_scope` in
`financials_endpoints.py`): already documented in this change's own `design.md` §"Out of scope"
("Refactoring `financials_endpoints.py` to reuse `resolve_request_tenant_scope`..."). Judged
sufficient per the task's own guidance — no additional location needed since `design.md` is a
durable, trackable artifact of this change and the note already explains why it wasn't bundled.

## Verification

`bash init.sh` — green:
```
[OK]    Harness ready. You can start working.
```

`git status --short` before commit confirmed only the 4 intended files changed (plus this new
report); no production code, migration SQL, or Section 8/10/11 artifacts touched.
