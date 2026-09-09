# Tasks 5.1 + 6.1 — Non-goal guards + testing sweep

**Change:** whatsapp-b2b-lead-bridge
**Task:** Group 5 (5.1) + Group 6 (6.1)
**Type:** Verification only — no production code written or modified.

## Group 5.1 — Non-goal guards (verified by reading, not building)

### (a) No path in this change creates a `tenants` or `b2b_clients` row

Read every file touched by Groups 1-4:

- `apps/backend/services/taty_lead_router.py` — grepped for
  `tenants.insert|b2b_clients.insert|.table("tenants")|.table("b2b_clients")`: **no matches**.
  `route_lead_message`'s `business_interest` branch (lines 373-380) only calls
  `service.advance_lead(lead_id, current_stage, lead_type="business_interest")`, which writes to
  `crm_leads` only (`crm_service.py:538-558`, patch dict is `{"stage": ..., "lead_type": ...}`
  against `.table("crm_leads")`). No new table, no new tenant, no new b2b_client anywhere in the
  branch.
- `apps/backend/migrations/0049_crm_leads_lead_type.sql` — a single `ALTER TABLE crm_leads ADD
  COLUMN IF NOT EXISTS lead_type text` + a `COMMENT ON COLUMN`. No `INSERT`, no other table
  touched, not applied to Supabase yet (per task 2.2, confirmed still pending in tasks.md's Stage
  11.1).
- `apps/chatwoot-bridge/main.py` — grepped for `tenants|b2b_clients`: **no matches** anywhere in
  the file. The `business_interest` auto-tagging branch (`_auto_tag_chatwoot()`) only calls
  Chatwoot's own `set_conversation_attributes`/`set_contact_attributes` HTTP client methods —
  it never touches Supabase at all, let alone `tenants`/`b2b_clients`.

**Confirmed: no path in this change creates a `tenants` or `b2b_clients` row.** The only write
this change performs against Supabase is the additive `lead_type` column on the existing
`crm_leads` row, via the existing `advance_lead()` update path.

### (b) `hermes-hubspot-poller`'s Company/Deal sync rule is untouched

`git status` at the start of this task shows no files under `apps/hermes-hubspot-poller/` in the
working tree diff — this change has not touched that app at all. Read the rule directly to state
it precisely (`apps/hermes-hubspot-poller/poller.py`):

```
5:  1. crm_leads -> HubSpot Contact + Deal (single default pipeline, funnel-mapped dealstage)
6:  2. b2b_clients -> HubSpot Company ONLY — never a Deal (design.md Decision #5)
...
107:    logger.error("Failed to upsert HubSpot Company for b2b_client %s", client_id)
110:    # Deliberately no Deal is ever created here (design.md Decision #5) — B2B never touches
```

**Confirmed: the rule (`b2b_clients` → Company only, never Deal) is intact and untouched by
this change.** This change never writes to `b2b_clients` at all (see (a) above), so there is
nothing for the poller to pick up differently either.

## Group 6.1 — Testing sweep

Interpreter used: `py -3.11` (the only interpreter in this environment with `pytest` installed —
per project memory `project_pytest_interpreter_py311.md`).

### Backend (`apps/backend/`)

Command and full output:

```
cd apps/backend
py -3.11 -m pytest tests/test_taty_lead_router.py tests/test_crm_service.py \
  tests/test_crm_service_b2b_writes.py tests/test_crm_service_b2c_logic.py \
  tests/test_crm_service_grid_logic.py tests/test_crm_service_service_band.py -q
```

```
............................................................ssss........ [ 67%]
...................................                                      [100%]
============================== warnings summary ===============================
...\gotrue\types.py:679: 19 warnings
  PydanticDeprecatedSince20: The `update_forward_refs` method is deprecated; use `model_rebuild` instead.
...\starlette\formparsers.py:10
  PendingDeprecationWarning: Please use `import python_multipart` instead.

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
103 passed, 4 skipped, 20 warnings in 38.79s
```

Also ran the two other backend suites that exercise `sales_interest`/`payment_confirmation`/
`business_interest` classification and WhatsApp reply delivery, to cover the full
`taty-whatsapp-sales-router` surface:

```
py -3.11 -m pytest tests/test_whatsapp_endpoints.py tests/test_whatsapp_reply_voice_allowed.py -q
```

```
..............................                                           [100%]
30 passed, 20 warnings in 35.80s
```

**Backend: 133 passed, 4 skipped, 0 failed. No regression.**

### Chatwoot bridge (`apps/chatwoot-bridge/`)

```
cd apps/chatwoot-bridge
py -3.11 -m pytest tests/test_process_message.py -q
```

```
FAILED tests/test_process_message.py::TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes
- AssertionError: expected await not found.
  Expected: mock(42, 'Respuesta de Taty')
    Actual: mock(42, 'Respuesta de Taty', private=True)
1 failed, 11 passed, 1 warning in 1.95s
```

## Pre-existing failure identified — NOT caused by this change

`TestSingleBrainInvariant::test_reply_comes_from_the_sales_router_not_hermes` fails with the
exact same mismatch already documented in
`progress/impl_whatsapp-b2b-lead-bridge_task4.md` (Group 4's own report, written earlier in this
same change): `send_reply` is now called with an extra `private=True` kwarg, a side effect of the
**unrelated** `voicebox-local-voice-adoption` change (commit `8a748f7`, already on this branch —
see git log in this session's system context).

This is not a regression from Groups 5/6 either — it was already present before I started this
task (Group 4's report reproduced it via `git stash` against the committed state, with none of
Group 4's changes present, and got the identical failure). I did not re-run the stash
reproduction myself since Group 4 already did so with full evidence in its own report; re-reading
`taty_lead_router.py`/`crm_service.py`/`main.py` for Groups 1-4 above confirms none of those diffs
touch `send_reply` or the `private` kwarg at all — the only caller of `send_reply` with `private=`
lives in the WhatsApp voice-note wiring from `voicebox-local-voice-adoption`, a completely separate
OpenSpec change.

**Per the task instruction, this failure is out of scope for `whatsapp-b2b-lead-bridge` and was
not fixed.** No production code was touched to "fix" it.

**Chatwoot bridge: 11 passed, 1 pre-existing failure (unrelated to this change), 0 new failures.**

## Overall conclusion for Groups 5-6

- Group 5.1: both non-goal guards confirmed intact by direct code reading — no code changes
  needed or made.
- Group 6.1: zero regression in every `taty-whatsapp-sales-router` scenario (sales/payment/
  business/unknown classification, reply delivery, Wompi HITL enqueue) across both the backend
  and chatwoot-bridge suites. The one failing test is a pre-existing, previously documented,
  out-of-scope issue from a different change (`voicebox-local-voice-adoption`).

No production code was modified for this task. `tasks.md` was not edited (per instruction — the
checkbox updates for 5.1/6.1 are left for the leader/founder to apply).
