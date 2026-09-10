# Implementer report — b2c-social-lead-capture, Task 3

**Task:** "First-contact trigger (text only, no voice/Twilio dependency)"
(`openspec/changes/b2c-social-lead-capture/tasks.md`, section 3, subtasks 3.1-3.3).

## Step 1 — hygiene fix (tasks.md 2.1-2.4)

Before any new code, marked `[x]` on subtasks 2.1, 2.2, 2.3, 2.4 in
`openspec/changes/b2c-social-lead-capture/tasks.md` (section "## 2. Backend: public,
rate-limited capture endpoint"), per the reviewer's non-blocking "Required changes" note
in `progress/review_b2c_social_task2.md` (verdict **APPROVED**, reviewer independently
re-ran `cd apps/backend && py -3.11 -m pytest tests/test_social_capture_endpoints.py
tests/test_crm_whatsapp_intake.py -v` → **18 passed in 6.13s**). Added an inline note
in `tasks.md` pointing at that review file — no new evidence was fabricated, only the
existing approval was cited.

## Step 2 — Task 3 implementation

**TDD, real red-then-green.** Added 3 new tests to
`apps/backend/tests/test_social_capture_endpoints.py`
(`TestSocialCaptureFirstContactTrigger`) that patch
`presentation.social_capture_endpoints.send_whatsapp_message` — confirmed genuinely red
first (`AttributeError: <module ...> does not have the attribute 'send_whatsapp_message'`,
since the import didn't exist yet), then implemented the trigger and confirmed green.

**Design decision followed exactly (design.md Decision 4):** "the same delivery mechanism
`taty_lead_router.py` already uses for outbound WhatsApp text sends the first message."
`taty_lead_router.py` is off-limits this session (concurrently dirtied by the parallel
`taty-document-collection-wiring` change per the task's hard restrictions), so instead of
importing from it I traced the actual reusable primitive one layer down:
`channels/whatsapp.py::send_whatsapp_message` — the same async function
`taty_lead_router.py`, `crm_service.py::approve_payment`, and
`presentation/cadence_endpoints.py::send_touch` all call directly. `cadence_endpoints.py`
is the closest precedent for calling it straight from a presentation-layer endpoint
(`from channels.whatsapp import send_whatsapp_message` at module scope,
`await send_whatsapp_message(phone, step.message)`), so `social_capture_endpoints.py`
follows that exact pattern — no new send mechanism, no Twilio/voice dependency (Twilio
lives entirely in `services/twilio_client.py`, untouched).

**Implementation (`apps/backend/presentation/social_capture_endpoints.py`):**
- Added `from channels.whatsapp import send_whatsapp_message`.
- Added a module-level `FIRST_CONTACT_MESSAGE` constant (short, generic opening ping —
  Taty's own conversational skill, ARCHITECTURE.md Decision #25, takes over from the
  reply).
- `social_capture_partial` became `async def` (it now awaits `send_whatsapp_message`).
- After `record_phone_capture`, the trigger fires **only** when
  `result.get("is_new")` is `True` — i.e. only on `CrmService.whatsapp_intake`'s
  create path. This naturally covers both no-duplicate-send cases the task asked for:
  - a phone found as an *existing* lead (`is_new: False`) never sends;
  - a phone rejected earlier by the throttle's `is_phone_repeat` check never even
    reaches `whatsapp_intake`, so it can't send either.
- `send_whatsapp_message`'s own `False` return (e.g. WHATSAPP_TOKEN not configured) is
  logged as a warning, matching `cadence_endpoints.py`'s existing handling — never
  raised, never blocks the capture response.

## Files touched

- `apps/backend/presentation/social_capture_endpoints.py` (edited — added the trigger)
- `apps/backend/tests/test_social_capture_endpoints.py` (edited — added
  `TestSocialCaptureFirstContactTrigger`, 3 new tests)
- `openspec/changes/b2c-social-lead-capture/tasks.md` (edited — checked off 2.1-2.4,
  added the retroactive-approval note)

**Explicitly NOT touched** (confirmed via `git status`, pre-existing dirty state from the
parallel `taty-document-collection-wiring` session, per the task's hard restriction):
`apps/backend/channels/whatsapp.py`, `apps/backend/core/plan_features.py`,
`apps/backend/tests/test_whatsapp_channel.py`, `services/taty_lead_router.py`,
`tests/test_taty_lead_router.py`. No migration created or applied. No `taty-voice-outbound-
calls` file touched.

## Test commands + real output

```
cd apps/backend && py -3.11 -m pytest tests/test_social_capture_endpoints.py -v
```
```
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_unauthenticated_request_succeeds PASSED [ 11%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_delegates_to_crm_service_whatsapp_intake_with_source PASSED [ 22%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_ip_throttle_rejects_excess_requests PASSED [ 33%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_repeat_phone_within_window_is_a_no_op PASSED [ 44%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_repeat_phone_does_not_count_against_ip_throttle_capacity PASSED [ 55%]
tests/test_social_capture_endpoints.py::TestSocialCaptureFirstContactTrigger::test_new_capture_sends_exactly_one_whatsapp_message PASSED [ 66%]
tests/test_social_capture_endpoints.py::TestSocialCaptureFirstContactTrigger::test_repeat_capture_of_existing_lead_sends_no_message PASSED [ 77%]
tests/test_social_capture_endpoints.py::TestSocialCaptureFirstContactTrigger::test_throttled_repeat_phone_sends_no_message PASSED [ 88%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialCrmServiceSourceStamping::test_source_stamped_only_on_insert_path PASSED [100%]

======================== 9 passed, 1 warning in 0.80s =========================
```

Zero-regression check against the sibling `whatsapp_intake` suite that Task 2's reviewer
already validated:

```
cd apps/backend && py -3.11 -m pytest tests/test_social_capture_endpoints.py tests/test_crm_whatsapp_intake.py -v
```
```
======================== 21 passed, 1 warning in 1.66s ========================
```
(all 12 pre-existing `test_crm_whatsapp_intake.py` tests still pass, plus all 9 in
`test_social_capture_endpoints.py` — 3 new from Task 3.)

**Before-red confirmation** (captured before implementing, proving the tests weren't
mock-gamed to always pass):

```
tests/test_social_capture_endpoints.py::TestSocialCaptureFirstContactTrigger::test_new_capture_sends_exactly_one_whatsapp_message FAILED
tests/test_social_capture_endpoints.py::TestSocialCaptureFirstContactTrigger::test_repeat_capture_of_existing_lead_sends_no_message FAILED
tests/test_social_capture_endpoints.py::TestSocialCaptureFirstContactTrigger::test_throttled_repeat_phone_sends_no_message FAILED
AttributeError: <module 'presentation.social_capture_endpoints' ...> does not have the attribute 'send_whatsapp_message'
=================== 3 failed, 6 passed, 1 warning in 1.53s ====================
```

## Explicitly not done (per task scope + hard restrictions)

- Task 3.4/checkbox marking in `tasks.md` — per HARNESS.md, the implementer never
  self-approves; the reviewer marks Task 3 `[x]` after review.
- Task 4 (frontend landing page), Task 6 (full sweep), Stage 11 (deploy) — out of
  scope for this task, untouched.
- No full-suite `-q` sweep run here (that's Task 6's explicit job per
  `progress/review_b2c_social_task2.md`'s own precedent) — only the scoped/related
  test files above, which is what Task 3.3 ("Tests green") asks for.
