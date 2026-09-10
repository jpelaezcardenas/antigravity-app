# Review -- taty-voice-outbound-calls, Tasks 2, 3, 4 (plus verification of 5, 6)

Verdict: APPROVED

## Verification performed

### Task 2 -- outbound-call endpoint
- apps/backend/presentation/voice_outbound_endpoints.py: order of operations in
  trigger_outbound_call_endpoint confirmed by direct read: auth (line 108) -> lead lookup (110) ->
  tenant match (114) -> B2B (lead_type == business_interest) rejection at line 119-124 ->
  only then twilio_client.is_configured() (126) -> phone resolution (129). A B2B lead is refused
  before any Twilio config check or phone lookup logic runs. Matches spec.md and design.md.
- OutboundCallRequest uses model_config = ConfigDict(extra=ignore); phone is always read
  from crm_leads via _get_lead_for_call, never from the request body -- confirmed in code and
  in test_caller_supplied_phone_field_is_ignored.
- apps/backend/services/twilio_client.py: plain httpx wrapper, not the twilio PyPI SDK.
  grep -ni twilio apps/backend/requirements.txt returned no match. No SDK dependency added.
- apps/backend/main.py: new router registered in the existing non-try/except /internal/* block
  (lines 264, 271-275) -- consistent with ARCHITECTURE.md Decision 22/24 fail-loud rule.

### Task 3 -- STT
- apps/chatwoot-bridge/whisper_client.py: httpx POST to LOCAL_WHISPER_URL, fail-soft (never
  raises), mirrors voicebox_client.py shape. LOCAL_WHISPER_URL is a pre-existing unused
  placeholder per ARCHITECTURE.md Decision 24 -- this module is the first live caller. Not
  pointed at a real running server (correctly left unchecked in tasks.md 3.2 as a founder/infra
  action).

### Task 4 -- opening script and qualification flow
- apps/backend/core/voice_call_script.py: opening always states AI disclosure
  (soy un asistente de inteligencia artificial) before the first question; no price/plan/offer
  words anywhere in OPENING_SCRIPT. QUALIFICATION_QUESTIONS is a hardcoded, ordered, 3-item
  list; next_qualification_question returns None once answered_count is 3 or more.
- apps/backend/services/voice_call_outcome.py: record_call_outcome reuses
  CrmService.advance_lead; only qualified advances stage; voicemail, not_interested and
  callback_requested keep current stage and stamp lead_type. No new table. voicemail never
  calls twilio_client.place_call -- true by construction, voice_call_outcome.py does not import
  twilio_client at all (confirmed by reading the file imports).
- Task 4.1 (Colombian AI-disclosure law): correctly flagged as not legally confirmed, with the
  safe default (always disclose) applied and documented in the module docstring and tasks.md.
  This is an honest open gap, not a fabricated confirmation -- acceptable per the task brief.

### Task 5 -- non-goal guards (verified independently, not just trusted)
- 5.1 confirmed: see order-of-operations check above -- B2B rejection happens strictly before
  any Twilio/phone logic.
- 5.2 confirmed: grep -ri twilio apps/chatwoot-bridge (run independently) returned zero matches,
  code and config.
- 5.3 confirmed: VOICE_OUTBOUND_CALLS_ENABLED (config.py line 143) and VOICE_ENABLED (config.py
  line 131) are separate, independent boolean fields with independent defaults and comments.
  test_enabling_voice_outbound_calls_does_not_touch_whatsapp_voice_flag explicitly toggles one
  and asserts the other is unaffected in both directions.

### Absolute restriction -- no cloned-voice path, ever
- Grepped all five new or modified files for tatiana, cloned and voicebox -- every match is
  inside a comment or docstring explaining the ABSENCE of a cloned-voice code path, never a
  reference to an actual cloned-voice profile ID or a VoiceBox call from the backend.
- _build_twiml (voice_outbound_endpoints.py lines 87-98) is the only place TwiML is constructed,
  and it hardcodes a Polly Lupe Say voice, language es-MX -- Twilio own generic TTS. There is no
  branch, flag check, or code path anywhere in voice_outbound_endpoints.py, twilio_client.py, or
  voice_call_script.py that selects a different voice or calls VoiceBox. Even when
  VOICE_OUTBOUND_CALLS_ENABLED is True (line 134), the code only logs a warning and still falls
  through to the same _build_twiml, generic voice -- confirmed by reading the full function body,
  not just the comment. test_default_flag_never_uses_cloned_voice and
  test_happy_path_places_call_with_generic_voice (asserting voicebox is not in twiml) cover this.
- No path, however unlikely, reaches the cloned voice. Approved on this point.

### Minor issue found, not blocking
- core/voice_call_script.py docstring references services/voice_call_orchestration.py as the
  seam that would need to change -- that file does not exist; the actual seam is
  presentation/voice_outbound_endpoints.py, function _build_twiml. Doc-only inaccuracy, no
  functional or security impact (confirmed no code path exists under either name that touches a
  cloned voice). Should be fixed in a follow-up but does not block this review.

### Task 6 -- testing sweep (run independently, not trusted from the report)
- apps/backend: py -3.11 -m pytest -q --ignore=tests/test_profile_support.py
  --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py resulted in
  35 failed, 1227 passed, 120 skipped -- exact same count and exact same failing test names as
  the implementer report (radar, secure_llm, shadow_gl stage1/4/5/8, whatsapp_inbox, wizard tests
  -- none touch any file this session created or edited).
- apps/chatwoot-bridge: py -3.11 -m pytest -q resulted in 2 failed, 91 passed -- same two
  failures (test_chatwoot_client.py test_posts_an_incoming_message,
  test_process_message.py test_reply_comes_from_the_sales_router_not_hermes), unrelated to this
  work.
- The 3 ignored backend files fail at collection with ModuleNotFoundError, no module named
  apps.backend -- independently confirmed, unrelated to this session (import path issue in
  pre-existing test modules).
- New test files (test_twilio_client.py, test_voice_call_script.py, test_voice_call_outcome.py,
  test_voice_outbound_endpoint.py, test_whisper_client.py) do not mock the exact boundary they
  claim to test -- inspected test_twilio_client.py (mocks httpx.AsyncClient, asserts on request
  params) and test_whisper_client.py (uses respx to mock HTTP, not the function under test) -- no
  self-mocking pattern of the kind ARCHITECTURE.md Decision 22 flagged as a prior incident.
- No real network call to Twilio or Whisper in any test -- confirmed via grep for
  respx, AsyncMock and monkeypatch usage in all new test files; no unmocked
  httpx.AsyncClient or real request left in place.

### Scope creep and policy checks
- VOICE_OUTBOUND_CALLS_ENABLED defaults to False everywhere (config.py, no env override, no
  test flips the actual setting object without monkeypatch cleanup).
- Tasks 1 (cadence -- already shipped and deployed separately), 7, 8, 9 in tasks.md are untouched
  by this diff.
- No Twilio account or number was created (task 2.3 correctly left unchecked).
- apps/backend/requirements.txt has no new twilio SDK entry.
- tasks.md edits for sections 2, 3 and 4 match what the code actually does -- no over-claiming
  (2.3 and part of 3.2 correctly left unchecked as founder/infra actions).

## Checkpoints
- C1 (implements only the assigned tasks 2, 3, 4; does not touch 1, 7, 8, 9): [x]
- C2 (TDD -- tests exist and assert real outcomes, not just no exception): [x]
- C3 (no fabricated stubs or placeholders, no disabled type-checking): [x]
- C4 (respects ARCHITECTURE.md tenant/RLS and /internal/* plus INTERNAL_API_KEY patterns): [x]
- C5 (absolute restriction: no cloned-voice code path under any flag state): [x]
- C6 (Twilio credentials and dependencies isolated to backend only, never chatwoot-bridge): [x]
- C7 (test sweep green relative to baseline, zero new regressions): [x]
- C8 (docs-sync -- no ARCHITECTURE.md container or dependency change required by this diff;
  tasks.md updated accurately): [x]

## Required changes (if any)

None blocking. Optional follow-up (non-blocking): fix the stale
services/voice_call_orchestration.py reference in core/voice_call_script.py docstring to
point at presentation/voice_outbound_endpoints.py, function _build_twiml.
