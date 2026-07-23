# Task 10.5 — Remove onboarding-trigger call from the WhatsApp lead-intake path

## Context

Design correction (2026-07-23, per CLAUDE.md §7): `design.md` decision 5 and
`specs/chatwoot-hermes-bridge/spec.md`'s "New WhatsApp contacts trigger lead intake"
requirement were already corrected to remove the `POST
/api/v1/social-ops/onboarding/start` call — that endpoint is for B2B/paid-customer
21-day workspace onboarding (requires `company_name`/`customer_email`/
`payment_reference`, none of which exist for a fresh B2C WhatsApp lead) and the
call has always 422'd silently (swallowed by the bridge's fail-soft contract).
This task brings the code in `apps/chatwoot-bridge/` in line with the already
corrected spec/design.

## Files touched (exactly these 5, nothing else)

1. `apps/chatwoot-bridge/main.py`
   - `process_incoming_message`'s new-lead branch (`if intake_result and
     intake_result.get("is_new") and contact_id is not None:`) no longer calls
     `backend_client.trigger_onboarding()`. It now only calls
     `chatwoot_client.set_contact_attributes(...)`.

2. `apps/chatwoot-bridge/backend_client.py`
   - Removed the `trigger_onboarding()` function entirely (dead code — nothing
     calls it anymore).
   - Updated the module docstring: no longer describes an "onboarding trigger"
     responsibility; now states the bridge only finds-or-creates the CRM lead
     and tags the Chatwoot contact, and explicitly notes it never invokes the
     B2B onboarding flow. Fail-soft contract paragraph updated to reference only
     `whatsapp_intake`.

3. `apps/chatwoot-bridge/tests/test_backend_client.py`
   - Removed the entire `TestTriggerOnboarding` class (`test_posts_to_onboarding_start`,
     `test_failure_is_swallowed_not_raised`) — the function under test no
     longer exists.
   - Updated the module docstring to drop the "onboarding trigger" mention.

4. `apps/chatwoot-bridge/tests/test_process_message.py`
   - `mocked_clients` fixture: removed the `backend_client.trigger_onboarding`
     patch/mock (`onboarding` key removed from the yielded mocks dict).
   - Renamed/updated `test_new_lead_triggers_onboarding_and_sets_contact_attributes`
     -> `test_new_lead_sets_contact_attributes_without_onboarding`: drops the
     onboarding assertion, keeps the `set_contact_attributes` assertion
     (contact_id + `estado: "nuevo"`).
   - Renamed `test_returning_contact_does_not_trigger_onboarding` ->
     `test_returning_contact_does_not_set_contact_attributes`: drops the
     `onboarding.assert_not_called()`, keeps `set_attrs.assert_not_called()`
     (still correct — returning contacts never touch `set_contact_attributes`
     either).
   - `test_intake_failure_still_proceeds_to_hermes_reply`: dropped the
     `onboarding.assert_not_called()` line (nothing to assert anymore); kept
     the Hermes/reply assertions.
   - Updated the module docstring to note Task 10.5's contract (new lead only
     tags the contact, never triggers onboarding).

5. `openspec/changes/chatwoot-hermes-taty-bridge/tasks.md`
   - No edit made by this session — task 10.5's checkbox is left `[ ]` per the
     harness rule (implementer never self-approves; reviewer marks it done on
     APPROVED verdict). The task text itself was already present from a prior
     session (uncommitted working-tree state before this session started);
     confirmed via `git diff` that this session did not introduce or alter
     that text.

## Confirmation no other file was touched

`git status --short apps/chatwoot-bridge openspec/changes/chatwoot-hermes-taty-bridge/tasks.md`:

```
 M apps/chatwoot-bridge/backend_client.py
 M apps/chatwoot-bridge/main.py
 M apps/chatwoot-bridge/tests/test_backend_client.py
 M apps/chatwoot-bridge/tests/test_process_message.py
 M openspec/changes/chatwoot-hermes-taty-bridge/tasks.md
```

`git diff` on `tasks.md` shows only the pre-existing (already-authored,
uncommitted) task 10.5 text block being present with its checkbox unchecked —
no change made by this session to that file. `design.md` and
`specs/chatwoot-hermes-bridge/spec.md` were not touched (per instructions —
already correctly updated by a prior session).

`main.py`'s webhook filtering, Hermes client, Chatwoot client, `whatsapp_intake`,
and health check were left exactly as-is — only the single `trigger_onboarding()`
call site in the new-lead branch was removed.

## Test run (final)

Command: `cd apps/chatwoot-bridge && python -m pytest tests -v`

Result: **30 passed**, 1 warning (pre-existing `python_multipart` deprecation
warning from `starlette`, unrelated to this change), in 9.72s.

Full pass list:
- `tests/test_backend_client.py` — 5 passed (JWT signing x2, whatsapp_intake x3;
  `TestTriggerOnboarding` class removed, was 2 tests)
- `tests/test_chatwoot_client.py` — 4 passed
- `tests/test_health.py` — 1 passed
- `tests/test_hermes_client.py` — 5 passed
- `tests/test_process_message.py` — 6 passed (audio fallback, full pipeline
  order, new-lead sets attrs without onboarding, returning-contact skips attrs,
  intake-failure proceeds, Hermes-failure fallback)
- `tests/test_webhook_filter.py` — 9 passed

Total: 30 passed (down from the pre-task-10.5 baseline of 32 — expected, since
2 tests for the now-removed `trigger_onboarding()` function were deleted, not a
regression).

## No scope creep

`webhook` filtering, `hermes_client.py`, `chatwoot_client.py`,
`schemas.py`, `config.py`, `whatsapp_intake()`, and the `GET /` health check
were not touched — verified via `git status` above (only the 4 code/test files
+ tasks.md, which itself carries only the pre-existing uncommitted task text).
