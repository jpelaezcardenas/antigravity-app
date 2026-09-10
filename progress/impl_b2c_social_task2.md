# Task 2 — Backend: public, rate-limited capture endpoint

**Change:** `b2c-social-lead-capture`
**Task:** 2 (2.1-2.4) in `openspec/changes/b2c-social-lead-capture/tasks.md`

## Endpoint path (confirmed, per design.md's "confirm exact path" note)

`POST /api/v1/crm/social-capture/partial`

Mounted unconditionally in `apps/backend/presentation/router.py` via a **new, separate
router** (`presentation/social_capture_endpoints.py`), prefix `/crm`, alongside — but not
inside — the existing `crm_router`. This is deliberate: `crm_router` applies
`get_current_user` as a router-level dependency (it backs the tenant-scoped B2B/B2C
cockpit), and this endpoint must be genuinely public/unauthenticated. Mounting
unconditionally (not behind a feature flag) mirrors the `whatsapp_router` reasoning
already documented in that file — a flag here would risk silently dropping real
ad-traffic leads.

## What was implemented

1. **`apps/backend/services/social_capture_throttle.py`** (new) — in-process, dict-backed
   throttle. No global rate limiter exists in this backend (re-verified by reading
   `apps/backend/main.py` — confirmed, matches design.md's finding). Two independent
   checks:
   - IP window: `IP_MAX_REQUESTS` (5) requests per `IP_WINDOW_SECONDS` (60) per IP,
     tracked with a per-IP `deque` of monotonic timestamps, old entries pruned lazily.
   - Phone window: `PHONE_WINDOW_SECONDS` (600) — a repeat normalized phone number
     within the window is flagged as a repeat; the caller (the endpoint) treats this as
     a no-op and never calls the service layer again for it.
   - `reset()` exported for test isolation (module-level state).

2. **`apps/backend/services/crm_service.py`** — `CrmService.whatsapp_intake` gained an
   additive `source: Optional[str] = None` parameter. Stamped **only on the insert
   (create) path**, mirroring the existing `full_name` handling in the same method — an
   existing lead's `source` attribution is never overwritten by a later capture. This is
   the reuse point requested by tasks.md 2.2/5.1: no duplicate find-or-create logic was
   written, the same method `whatsapp-intake` already calls was extended additively.

3. **`apps/backend/presentation/social_capture_endpoints.py`** (new) — the endpoint
   itself:
   - Resolves `request.client.host` as the throttle key.
   - IP-throttled request → `HTTPException(429)`, service layer never touched.
   - Repeat-phone request (within window) → `200 {"is_new": false, "throttled_repeat":
     true}`, service layer never touched.
   - Otherwise → calls `get_crm_service().whatsapp_intake(whatsapp_phone,
     full_name=..., source=...)` (the exact same method/logic `whatsapp-intake` uses) and
     records the phone capture only on success.
   - No `Depends(get_current_user)` anywhere on this router — confirmed public.

4. **`apps/backend/presentation/router.py`** — registered the new router (import +
   `include_router(social_capture_router, prefix="/crm", ...)`, right after the
   `whatsapp_router` mount, with a comment explaining why it's separate from
   `crm_router`).

## Tests (TDD)

New file: `apps/backend/tests/test_social_capture_endpoints.py` (6 tests), covering:
- Unauthenticated request succeeds (no Authorization header at all).
- Delegates to `CrmService.whatsapp_intake` with `full_name`/`source` passed through
  (reuse, not duplication).
- IP throttle rejects the request past `IP_MAX_REQUESTS` within the window (429), and
  the accepted requests before that stay 200.
- Repeat phone number within the throttle window (in a different `+`/no-`+` format,
  proving it goes through the same normalizer) is a no-op — returns
  `{"is_new": false, "throttled_repeat": true}` and `whatsapp_intake` is called exactly
  once across both requests.
- A throttled-repeat response doesn't itself call the service (belt-and-suspenders on
  the above).
- `CrmService.whatsapp_intake` service-layer test: `source` is stamped on the insert
  payload on the create path (mirrors the fixture pattern in
  `test_crm_whatsapp_intake.py`).

Existing `apps/backend/tests/test_crm_whatsapp_intake.py` re-run unmodified to confirm
no regression from the additive `source` parameter.

### Actual pytest output

```
$ py -3.11 -m pytest tests/test_social_capture_endpoints.py tests/test_crm_whatsapp_intake.py -v

============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
collected 18 items

tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_unauthenticated_request_succeeds PASSED [  5%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_delegates_to_crm_service_whatsapp_intake_with_source PASSED [ 11%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_ip_throttle_rejects_excess_requests PASSED [ 16%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_repeat_phone_within_window_is_a_no_op PASSED [ 22%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialEndpoint::test_repeat_phone_does_not_count_against_ip_throttle_capacity PASSED [ 27%]
tests/test_social_capture_endpoints.py::TestSocialCapturePartialCrmServiceSourceStamping::test_source_stamped_only_on_insert_path PASSED [ 33%]
tests/test_crm_whatsapp_intake.py::TestNormalizeWhatsappPhone::test_plus_and_no_plus_forms_normalize_to_the_same_value PASSED [ 38%]
tests/test_crm_whatsapp_intake.py::TestNormalizeWhatsappPhone::test_normalized_form_has_no_plus PASSED [ 44%]
tests/test_crm_whatsapp_intake.py::TestNormalizeWhatsappPhone::test_strips_spaces_and_punctuation PASSED [ 50%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeService::test_existing_lead_found_regardless_of_plus_prefix_format PASSED [ 55%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeService::test_new_phone_creates_lead_in_nuevos_stage PASSED [ 61%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeService::test_new_phone_with_full_name_creates_lead_with_that_name PASSED [ 66%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeService::test_new_phone_without_full_name_falls_back_to_phone PASSED [ 72%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeService::test_known_phone_lookup_ignores_full_name_argument PASSED [ 77%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeService::test_known_phone_is_found_not_duplicated PASSED [ 83%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeEndpoint::test_new_phone_returns_is_new_true PASSED [ 88%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeEndpoint::test_known_phone_returns_is_new_false PASSED [ 94%]
tests/test_crm_whatsapp_intake.py::TestWhatsappIntakeEndpoint::test_unauthenticated_call_is_rejected PASSED [100%]

======================== 18 passed, 1 warning in 8.22s ========================
```

Interpreter used: `py -3.11` (per `MEMORY.md`'s `project_pytest_interpreter_py311` note —
only py311 has pytest installed; `./init.sh`'s green gate alone does not mean tests ran).

## Files touched

- `apps/backend/services/social_capture_throttle.py` (new)
- `apps/backend/presentation/social_capture_endpoints.py` (new)
- `apps/backend/tests/test_social_capture_endpoints.py` (new)
- `apps/backend/services/crm_service.py` (edit — additive `source` param on
  `whatsapp_intake`)
- `apps/backend/presentation/router.py` (edit — import + mount new router)

## Non-goal guards respected

- Did not touch `taty-voice-outbound-calls`, `hermes-hubspot-poller`, or any B2B path.
- Did not touch `taty-document-collection-wiring` (separate in-progress change).
- Did not touch Task 3 (first-contact WhatsApp trigger), Task 4 (frontend landing page),
  Task 6 (full sweep), or Stage 11.
- Did not add a global rate-limiting middleware (`slowapi`) — throttle is scoped
  narrowly to this one endpoint, per design.md's explicit Non-Goal.

## Open questions / deviations from plan

- None. The endpoint path was ambiguous in tasks.md ("confirm exact path") — confirmed
  as `POST /api/v1/crm/social-capture/partial`, matching design.md Decision 2's stated
  name exactly, so Task 3/Task 4 can depend on a stable, already-decided path.
- I did **not** run the full backend test sweep (Task 6's job, not this task's) — I ran
  the new test file plus the directly-related `test_crm_whatsapp_intake.py` (the file
  whose behavior I extended) to confirm no regression there. A full-sweep `py -3.11 -m
  pytest -q` was started but exceeded the 120s foreground timeout and was moved to a
  background job; I did not wait on it since a full sweep is explicitly Task 6's scope,
  not Task 2's — flagging this for whoever picks up Task 6.
