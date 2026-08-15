# hermes-multi-tenant-wrapper — Deferred Scope

**As of:** 2026-08-13 tech-debt triage. This supplements, not replaces, the three "Ground Truth
Correction" sections already in `tasks.md` — read those first for the full root-cause history.

## What's genuinely done (Phase 1A)

- `TenantContextMiddleware` (T1-T4) — live, extracts `tenant_id` from JWT into
  `request.state.tenant_id`.
- **Write-time tenant stamping** (Ground Truth Correction #3, Layer 1): `ApprovalDecision` and
  `CentinelaService.save_alerts` now stamp a real Cliente Cero tenant UUID at write time via the
  shared `core/tenant_context.py::resolve_cliente_cero_tenant_id`, closing the root cause behind
  the NULL/placeholder-UUID data drift found in Correction #2.
- **Service-role client migration** (Layer 2): `approval_queue_service.py` and
  `centinela_service.py` both switched from the anon-key client to `get_service_supabase()`.
- Historical data backfilled onto the real Cliente Cero UUID (`centinela_alerts` 40/40,
  `approval_queue` 6/6 — verified live, zero NULL/placeholder rows remaining as of 2026-07-21).

## What's deliberately left open — not silently closed by archiving

1. **JWT `tenant_id` type mismatch (T10)** — `core/security.py` puts a non-UUID string in the
   JWT, but the raw-RLS policies in `0003_enable_rls_policies.sql` cast to `::uuid`. Per
   Correction #2, this raw-RLS approach is now understood to be a **second, redundant**
   isolation mechanism — the sanctioned one (`core/identity_resolver.py::IdentityResolver`,
   built by the already-archived `agent-operations-multitenant-security`) already works
   correctly at the agent-operations governance chokepoint. Whether to finish fixing the raw-RLS
   path or retire it in favor of the sanctioned resolver is an open design question, not
   scheduled here.
2. **Permissive RLS policies still live** (`approval_queue_anon_all`,
   `centinela_alerts_select/insert/update`, `qual=true`) — now inert for the two services that
   moved to the service-role client (Layer 2), but not dropped. Application-layer defense
   (explicit `tenant_id` + endpoint auth, added later by `approval-queue-tenant-scoping`) is live
   and sufficient on its own; dropping the permissive policies is defense-in-depth hygiene, not a
   correctness requirement. `approval-queue-tenant-scoping`'s own design.md already flagged this
   as this change's responsibility to schedule — still unscheduled.
3. **Phase 2 (SyncManager integration, T16-T25)** — DEFERRED by founder decision (2026-06-24),
   blocked on a commercial negotiation that was never closed. A different technical path (daily
   local/manual CSV upload by Contexia-as-Cliente-Cero) was proposed as an alternative but never
   scoped into tasks — see `FOLLOWUP_local-ingestion-alternative.md` in this change's directory
   for the starting point if picked back up. Superseded in practice by
   `shadow-gl-real-data-ingestion` (archived 2026-08-13), which already ships CSV Siigo ingestion
   independent of SyncManager.
4. **Phase 3 (WSL/tunnel hardening, T26-T35)** — DEFERRED, same reason as Phase 2, lower priority.
5. **Stage 6 (E2E + production deploy sign-off, T36-T40)** — never reached; blocked on Phase 1
   actually being correct first (item 1/2 above).

## Recommendation for whoever picks this back up

Items 1 and 2 are the highest-value remaining work — they're genuine security hygiene (defense in
depth), not blocked on anything external. Items 3-5 need a founder decision on SyncManager before
they're worth scoping further; Phase 2's original goal is now partially superseded by
`shadow-gl-real-data-ingestion`.
