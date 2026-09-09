# Review — whatsapp-b2b-lead-bridge (FINAL, all groups)

**Verdict:** APPROVED

## Independent verification performed

1. **Non-goal guard (a) — no `tenants`/`b2b_clients` writes.** Re-grepped
   `apps/backend/services/taty_lead_router.py` and `apps/chatwoot-bridge/main.py` for
   `tenants|b2b_clients`: zero matches in both, confirming the implementer's claim. Read
   `crm_service.py:545` — the only new write path (`business_interest` classification) reuses
   the existing `advance_lead`/`whatsapp_intake` update against `crm_leads` only, no independent
   Supabase query. `apps/backend/migrations/0049_crm_leads_lead_type.sql` is a single additive
   `ALTER TABLE crm_leads ADD COLUMN` + `COMMENT ON COLUMN` — no `INSERT`, no other table.

2. **Non-goal guard (b) — `hermes-hubspot-poller` Company/Deal rule untouched.** Read
   `apps/hermes-hubspot-poller/poller.py` directly: line 6 (`b2b_clients -> HubSpot Company
   ONLY — never a Deal`) and line 110 (`Deliberately no Deal is ever created here`) are intact,
   verbatim as the implementer quoted. **Correction to the implementer's report**: `git status`
   at review time shows `apps/hermes-hubspot-poller/hubspot_client.py` and `supabase_client.py`
   ARE modified in the working tree (plus new `http_retry.py` + its test), contradicting the
   report's "no files under apps/hermes-hubspot-poller/ in the working tree diff" claim. Read the
   diff: it is unrelated pre-existing dirty work (an `httpx` retry wrapper, `request_with_retry`)
   that does not touch the Deal-creation logic at all — confirmed the Deal-skip comment and
   `_sync_b2b_client`/`sync_b2b_clients` are byte-identical to what the report cites. The
   inaccuracy is cosmetic (wrong premise, right conclusion) and does not change the verdict, but
   the implementer should not claim "no diff" when one exists — flagging for the record.

3. **Holistic coherence across Groups 1-4.** `classify_lead_intent()` (`taty_lead_router.py:80-119`)
   adds `BUSINESS_INTEREST_KEYWORDS`, checked after payment-confirmation and before
   sales-interest — read directly, matches the design intent (a business-shaped message with
   both business and payment keywords still resolves to `payment_confirmation` first). The write
   path (`crm_service.py:545`) and the Chatwoot tagging diff (`main.py`, `_INTENT_TO_SERVICIO_INTERES`
   + the new `business_interest` branch ahead of the `es_asalariado` branch) are consistent: the
   classifier's signal flows through wiring into `lead_type`, and independently into Chatwoot
   contact attributes, without either depending on tenant/b2b_client provisioning. The
   `main.py` diff read in full is 12 lines, purely additive, and does not touch `send_reply` or
   the `private` kwarg.

4. **Migration not applied.** `0049_crm_leads_lead_type.sql` exists on disk only (untracked,
   `?? apps/backend/migrations/0049_crm_leads_lead_type.sql`), not committed, not applied — Stage
   11.1 correctly gates this behind explicit founder confirmation.

5. **`tasks.md` state matches reality.** Groups 1-4 are `[x]`, Group 5.1 and 6.1 are still `[ ]`
   (left for the leader to flip per instruction), Stage 11 fully `[ ]`. No premature marking.

6. **Test regression — independently re-run, not trusted from the report.**
   - `py -3.11 -m pytest tests/test_taty_lead_router.py tests/test_crm_service.py
     tests/test_crm_service_b2b_writes.py tests/test_whatsapp_endpoints.py
     tests/test_whatsapp_reply_voice_allowed.py -q` → **107 passed, 4 skipped, 0 failed**
     (consistent with the report's split totals; the difference is just which suites were
     batched together).
   - `cd apps/chatwoot-bridge && py -3.11 -m pytest tests/test_process_message.py -q` →
     **11 passed, 1 failed** (`TestSingleBrainInvariant::
     test_reply_comes_from_the_sales_router_not_hermes`), identical mismatch
     (`private=True` unexpected).
   - Verified the pre-existing-failure claim independently rather than trusting Group 4's
     stash reproduction: `git show 8a748f7:apps/chatwoot-bridge/main.py | grep private=True`
     shows `send_reply(conversation_id, reply_text, private=True)` **already present at commit
     8a748f7** (`voicebox-local-voice-adoption`, merged before this change started). `git diff
     HEAD -- apps/chatwoot-bridge/main.py` (this change's actual uncommitted diff) contains no
     reference to `private` or `send_reply` at all — 12 lines, purely additive to the intent
     dictionaries. This is conclusive: the failure predates and is untouched by
     whatsapp-b2b-lead-bridge. Confirmed out of scope, correctly not fixed here.
   - Ran the full `apps/backend` suite unfiltered: 3 collection errors
     (`test_profile_support.py`, `test_swarm_operators.py`, `test_t11_integration.py`), all
     `ModuleNotFoundError: No module named 'apps.backend'` — a pre-existing sys.path/packaging
     issue unrelated to any file this change touches (confirmed by reading the failing imports:
     `apps.backend.agents.llm_engine`, `apps.backend.operators.swarm`,
     `apps.backend.operators.conductor` — none of which `taty_lead_router.py`/`crm_service.py`/
     `main.py` import or are imported by). Consistent with project memory's documented baseline
     (`project_pytest_interpreter_py311.md`).

## Checkpoints
- C1 (non-goal guard: no tenant/b2b_client writes): [x]
- C2 (non-goal guard: hubspot poller Deal rule untouched): [x] — with the working-tree-dirty
  correction noted above (cosmetic, doesn't change outcome)
- C3 (holistic Groups 1-4 coherence): [x]
- C4 (migration 0049 unapplied, gated behind founder confirmation): [x]
- C5 (tasks.md reflects real state, Stage 11 unmarked): [x]
- C6 (zero real regression from this change, independently confirmed): [x]
- C7 (docs-sync — no container/dependency change in ARCHITECTURE.md needed): [x] — this change
  only touches an existing service's internal classification logic + an additive column; no new
  container, no new external dependency, no change to data flow topology. ARCHITECTURE.md does
  not need an update for this change (Stage 11's deployment report, not this review, will record
  the eventual production verification per task 11.4).

## Required changes (if any)
None. Ready for the leader to flip Group 5.1/6.1 checkboxes and proceed to Stage 11 (migration
apply requires separate explicit founder confirmation; deploy/production verification is
out of scope for this review session per the task instructions).
