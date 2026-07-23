# Design — Taty Per-Tenant Profile Resolution

## D1. Profile source: derive from `tenants` + in-code `DEFAULT_PROFILE` template (no new table)

**Chosen.** `_get_tenant_profile(tenant_id)` does a single sync `get_supabase().table("tenants")
.select("id, nit, legal_name, is_cliente_cero, company_id").eq("id", tenant_id).execute()` (same
sync-Supabase-from-a-sync-function pattern already used by `financials_service.py`), then merges
identity fields (`legal_name`, `nit`) onto a module-level `DEFAULT_PROFILE` (tone, enabled
knowledge sources, escalation keywords). `_get_tenant_profile()` is the single seam — a future
per-tenant override (jsonb column, or companion table) can be added behind it without touching
any caller.

**Rejected — new `taty_profiles` table.** Reintroduces exactly the failure mode this change
removes: a per-client row that must be seeded and can be forgotten, so a newly provisioned
tenant would again hit "Cliente no configurado" until someone remembers to seed it. Today's 3
hardcoded profiles differ from each other only in flavor text (`tono`, `sector`) that nothing
downstream actually branches on except the prompt string — not enough variance to justify
migration + RLS surface.

**Rejected — reuse off-repo `agent_profiles`.** Its DDL is not in the repo (applied ad hoc to
Supabase, irreproducible from git history) and it's keyed by legacy text `company_id`, not tenant
uuid. Extending it deepens the debt this change is retiring.

**Compliance constraint (GROUND_TRUTH):** `DEFAULT_PROFILE.regimen = None`. `_build_prompt()`
omits the régimen clause entirely when `regimen is None` instead of asserting `"Régimen Común"`
— Taty must not assert an unverified tax regime for a real client. `fuentes_habilitadas` defaults
to `["dian_normograma"]`; `is_cliente_cero=True` additionally enables `"contexia_fiscal"`
(Contexia-internal docs must never be exposed to another tenant).

## D2. Legacy 3 profiles: retire, no compat shim

`AGENT_PROFILES` is deleted outright. `ferez-001`/`martinez-001` are demo-only — no live caller
passes them (verified: only `tests/` and doc files reference them). `ctx-001` survives only as
data, via `tenants.company_id = 'ctx-001'` (already backfilled for Cliente Cero) — Telegram's
existing `company_id`-keyed mapping keeps working through a translation step (D6), not through
the old dict.

## D3. API surface: auth + canonical resolution, `company_id` deprecated-and-ignored

`POST`/`GET /api/v1/agents/ask` gain `user: dict = Depends(get_current_user)` and copy the
`financials_endpoints.py` resolution block verbatim in spirit:
1. `resolved_tenant_id` present → use it (the caller's own tenant).
2. Else caller is the staging identity (`user["id"] == _STAGING_USER["id"]`) → Cliente Cero via a
   local `_resolve_cliente_cero_tenant_id()` (same 10-line helper duplicated in
   `financials_endpoints.py` — matching existing convention beats inventing a shared module
   mid-change).
3. Else (authenticated but unresolved) → **clear in-band error**, never Cliente Cero.

`TatyAskRequest.company_id` becomes `Optional[str]`, documented deprecated, and is **never used
for resolution** — this closes the current spoofing hole where any caller can request any
profile by supplying an arbitrary `company_id`. Kept optional (not removed) so any external caller
still sending it doesn't get a 422.

**Error shape for case 3:** `ask()`'s existing contract is "never raises, always returns a
response dict" (see `_error_response`). Case 3 stays in that contract: HTTP 200 with
`TatyAskResponse` plus a new optional `error_code: "tenant_not_resolved"` field, a
human-readable Spanish `answer` telling the user their account isn't linked to a company, and
`requires_human_review=True`. Rejected: HTTP 403 — every existing consumer (dashboard, Telegram)
treats this endpoint as always-200 chat; a status-code branch would be a second, inconsistent
error contract for the same underlying condition `ask()` already models as a response field
(`_error_response` does the same for "Cliente no configurado" today).

`POST /api/v1/agents/taty/ask` (`agents_endpoints.py`, documented `DEPRECATED`) is deleted. It
duplicates `/agents/ask`, has zero consumers (verified: no in-repo caller besides its own docs),
and would break at the `ask()` signature change regardless — keeping a broken duplicate around
violates the no-ownerless-duplicate-paths rule.

## D4. `taty_intent_router.py`: delete, do not revive

**Rejected — revive as canonical entry point.** `route_message(tenant_id, message)` already takes
a tenant_id, which looks tempting to wire in directly. But making it the entry point for
`/agents/ask` would (a) change the response contract from `answer/citations/confidence` to
`reply/approval_id`, breaking every existing consumer without a compensating change to them; (b)
pull `pulso_diario_service`, `radar_service`, and an `approval_queue` **write**
(`enqueue_taty_escalation`) into what is today a read-only RAG Q&A path — a materially larger
blast radius than "resolve the profile correctly"; (c) roughly double this change's test surface
for a feature (conversational commands: "what's my risk score", "fix this invoice") that nobody
asked for in this proposal. That is scope creep, not tenant scoping.

**Chosen — delete**, along with `tests/test_taty_intent_router.py`. Git history preserves the
code; a future change can reintroduce tenant-scoped intent routing deliberately, as its own
proposal, if the product need arises. This satisfies the "no ownerless duplicate paths" mandate
without inventing new scope.

## D5. `ask()` signature: hard rename, no compat shim

`ask(company_id, ...)` → `ask(tenant_id, ...)`. All 3 live callers
(`taty_endpoints.py`, `telegram_endpoints.py`, and the now-deleted `agents_endpoints.py` route)
are updated in this same change — a compat alias accepting both names would itself be exactly
the kind of ownerless duplicate surface this change is closing, and would silently mask a
caller still passing a legacy demo key instead of surfacing it as `tenant_not_found`.

No caching layer is added for the profile lookup: one indexed primary-key select is negligible
next to the 2–4s LLM call that follows it in the same request; a cache would be premature
optimization and a staleness bug vector (a client's `legal_name` changing would need explicit
invalidation).

## D6. Telegram: translate `company_id` → `tenant_id` at the call site only

`telegram_chat_mappings` keeps storing `company_id` (Telegram-side registry, unrelated to this
change's scope). A new helper `_resolve_tenant_for_company_id(company_id)` does
`tenants.select("id").eq("company_id", company_id)` and is used **only** to build the argument
passed to `taty.ask(tenant_id=...)`. If no match, the existing "❌ Este chat no está
configurado" reply fires unchanged. The Social Ops onboarding branch (which also reads
`company_id` from the same mapping, line 138 of `telegram_endpoints.py`) is untouched — it is a
separate consumer of the mapping table, not of Taty.

**Rejected — hardcode Cliente Cero for any resolution failure.** Would silently mis-scope any
future non-Contexia Telegram mapping to Contexia's own data instead of surfacing the
configuration gap.

## D7. Knowledge-base retrieval keying

The resolved profile carries `kb_client_id = tenants.company_id or tenant_id`. This preserves
Cliente Cero's existing `knowledge_chunks` rows (keyed `'ctx-001'` in both the pgvector and
in-memory backends) without a data migration, and gives every other tenant a stable per-tenant
key (their own uuid) for future use, while `kb_seeding_service.retrieve_similar()`'s existing
`"__global__"` fallback (where the shared DIAN normograma corpus is seeded) already covers
tenants with no dedicated chunks — no change needed in `kb_seeding_service.py`.

**Rejected — re-key existing `'ctx-001'` chunks to Cliente Cero's uuid.** A data migration for
zero functional gain; `company_id` already resolves correctly via the `or` fallback above.

## Risks
1. **No DB migration** in this change is the point of D1 — there is nothing to roll back beyond
   the code diff itself.
2. **Auth flip on `/agents/ask`** could 401 an unknown external caller under
   `AUTH_ENFORCED=true`. Verified: zero in-repo consumers today (the Búnker bundle calls
   `/llm/analyze`, `/agents/onboarding/analyze`, `/agents/planner/generate-options` — never
   `/agents/ask`). Stage 11 checks Railway access logs before considering this closed.
3. **Prod `telegram_chat_mappings` rows referencing retired demo ids** (`ferez-001`,
   `martinez-001`) would start getting "no configurado" instead of a hardcoded profile. Detected
   by the mandatory DB-verification step (tasks.md Stage 7); the fix, if needed, is a data row
   update, not a code change.
4. **Compliance wording** in `_build_prompt()` is reviewed against `.antigravity/GROUND_TRUTH.md`
   at the reviewer gate before this change is approved.
