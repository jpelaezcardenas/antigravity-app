## Context

`crm_leads` has `CONSTRAINT uq_crm_leads_tenant_phone UNIQUE (tenant_id, whatsapp_phone)` (`apps/backend/migrations/0022_crm_b2c_sell_machine.sql:21`) — the table was designed multi-tenant from the start. Two independent find-or-create implementations exist against it:

- `CrmService.whatsapp_intake` (`apps/backend/services/crm_service.py:386-411`, added for `chatwoot-hermes-taty-bridge`): resolves the Cliente Cero tenant via the shared `_resolve_cliente_cero_tenant_id` helper (same pattern as `b2c_pipeline`/`advance_lead`), then looks up `.eq("tenant_id", tenant_id).eq("whatsapp_phone", normalized_phone)`.
- `taty_lead_router.find_or_create_lead` (`apps/backend/services/taty_lead_router.py:246-278`, shipped in `taty-whatsapp-sales-router`): looks up `.eq("whatsapp_phone", whatsapp_phone)` only — no `tenant_id` filter at all — then separately re-resolves the Cliente Cero tenant (its own inline query against `tenants`, duplicating `_resolve_cliente_cero_tenant_id`'s logic) only for the insert path.

Both are reachable in production code today, gated behind separate feature flags (`CRM_CANONICAL` for the Chatwoot-bridge path, `WHATSAPP_CANONICAL` for the native WhatsApp Cloud API path in `whatsapp_endpoints.py`) — both default `False`, so neither has received real traffic yet, but both are real, shipped, tested code paths, not dead code.

Also relevant: this repo is actively building multi-tenant support (`per-tenant-client-access`, an in-progress OpenSpec change at the time of writing) — the risk window for a tenant-less phone lookup causing a real cross-tenant leak is closing, not theoretical-forever.

**Hard dependency**: `CrmService.whatsapp_intake` does not exist on `main` yet — it was added on `feature/chatwoot-hermes-taty-bridge`, which has not merged. This change cannot be implemented against `main` as a base; its feature branch must branch from `feature/chatwoot-hermes-taty-bridge` instead (see tasks.md Step 0), and this change should not be archived before (or independently of) that one merging.

## Goals / Non-Goals

**Goals:**
- Exactly one implementation of "find-or-create a `crm_leads` row by WhatsApp phone," tenant-scoped, reused everywhere.
- Zero change to any external API contract or caller signature — this is an internal correctness fix, not a feature.
- Preserve `find_or_create_lead`'s `full_name`-on-create behavior (used by `whatsapp_endpoints.py`).

**Non-Goals:**
- Reconciling the two parallel WhatsApp *channels* (`taty_lead_router`'s direct Meta WhatsApp Cloud API integration vs. the Chatwoot-mediated bridge) — that is a separate, larger architectural question (LLM-conversational vs. deterministic-intent-routing, different product surfaces) explicitly out of scope here. This change only touches the shared `crm_leads` find-or-create primitive both happen to need.
- Migrating any existing production data — see Risks below for why none exists to migrate.
- Changing `route_lead_message`/`route_lead_document`'s behavior — they consume a `lead_id` string and are untouched.

## Decisions

1. **`find_or_create_lead` becomes a thin delegating wrapper around `CrmService.whatsapp_intake`, not a parallel tenant-scoped rewrite.** Alternative considered (the review's option (a) verbatim): add a `.eq("tenant_id", ...)` filter to `find_or_create_lead`'s own query, reusing `_resolve_cliente_cero_tenant_id` directly. Rejected: this still leaves two copies of the same lookup/insert logic that could drift again later. Delegating to the already-reviewed, already-tested `whatsapp_intake` leaves exactly one implementation, matching the proposal's stated goal.

2. **`CrmService.whatsapp_intake` gains an optional `full_name: str | None = None` parameter**, applied only on the insert path (`full_name or whatsapp_phone`, matching `find_or_create_lead`'s existing fallback-to-phone behavior exactly) — never touched on the lookup/existing-row path. Alternative considered: drop `full_name` support entirely, since the Chatwoot bridge never needed it. Rejected: `whatsapp_endpoints.py` passes `event.get("actor_name")` today; silently dropping that on delegation would be an observable regression for the native WhatsApp channel, not a neutral refactor.

3. **`find_or_create_lead`'s signature and return type are preserved exactly**: `find_or_create_lead(whatsapp_phone: str, full_name: Optional[str] = None) -> str`. It calls `CrmService.whatsapp_intake(whatsapp_phone, full_name=full_name)` and returns `result["lead_id"]`. No caller (`whatsapp_endpoints.py`) changes.

4. **Existing unit tests for `find_or_create_lead` must be rewritten, not just patched**, since they currently mock `get_service_supabase` directly with a query-chain shape (`.select().eq().execute()`) that matches the *old* implementation, not `whatsapp_intake`'s (`.select().eq().eq().maybe_single().execute()`). After delegation, these tests should mock `get_crm_service()`/`CrmService.whatsapp_intake` instead — the same pattern `test_taty_lead_router.py`'s `route_lead_message` tests already use for `get_crm_service()`. This is not a workaround; it correctly reflects that `find_or_create_lead` no longer talks to Supabase directly.

## Risks / Trade-offs

- **[Risk] Phone-normalization change could orphan a pre-existing row.** `whatsapp_intake`'s `_normalize_whatsapp_phone` (strips non-digits, keeps a leading `+`) may format a phone differently than `find_or_create_lead`'s previous exact-match. → **Mitigation**: `WHATSAPP_CANONICAL` defaults `False` and has never been flipped on in production (confirmed: no real WhatsApp Business number/token configured yet, per `taty_lead_router.py`'s own module docstring and `whatsapp_endpoints.py`'s feature-flag gating) — there is no live `crm_leads` data created via this path to orphan. If this channel goes live before this change lands, re-verify this risk is still moot.
- **[Trade-off] `find_or_create_lead` now makes one extra Python-level call (through `CrmService`) instead of querying Supabase inline** — negligible overhead (same underlying HTTP round-trip count: one lookup, optionally one insert), acceptable for eliminating duplicated logic.

## Migration Plan

1. Extend `CrmService.whatsapp_intake` with the optional `full_name` param (backward-compatible — existing callers passing none are unaffected).
2. Rewrite `find_or_create_lead` to delegate.
3. Update `test_taty_lead_router.py`'s two `find_or_create_lead` tests to mock at the `CrmService`/`get_crm_service` boundary instead of `get_service_supabase`.
4. Extend `test_crm_whatsapp_intake.py` with a case covering the new `full_name` parameter.
5. Run both test files plus the full backend regression suite.
6. Rollback: revert the commit — no data migration was performed, nothing to undo beyond code.

## Open Questions

- Whether `taty_lead_router.py`'s direct Meta WhatsApp Cloud API channel and the Chatwoot-mediated bridge are both meant to ship long-term, or whether one will eventually be retired in favor of the other — explicitly deferred, not this change's decision to make.
