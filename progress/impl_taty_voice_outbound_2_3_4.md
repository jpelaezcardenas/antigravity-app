# Implementation report — taty-voice-outbound-calls, Tasks 2, 3, 4

Task 1 (cadence) was already done and was not touched.

## Files created

- `apps/backend/config.py` (edited) — added `VOICE_OUTBOUND_CALLS_ENABLED: bool = False`
  (wholly independent of the existing `VOICE_ENABLED`), and `TWILIO_ACCOUNT_SID`/
  `TWILIO_AUTH_TOKEN`/`TWILIO_FROM_NUMBER` (all empty defaults, fail closed).
- `apps/backend/services/twilio_client.py` — `httpx`-based client against Twilio's REST API
  (`Calls.json`). Did NOT add the `twilio` PyPI SDK — checked `requirements.txt` first, it isn't
  there, and this repo's own convention (`channels/whatsapp.py`) is a direct `httpx` call.
  `is_configured()` / `place_call(to_number, twiml)`, fail-soft (returns `None`, never raises).
- `apps/backend/core/voice_call_script.py` — opening script (Spanish, matching Taty's tone
  elsewhere) + qualification question list, both as data/constants, plus
  `next_qualification_question()` capped at 3.
- `apps/backend/services/voice_call_outcome.py` — `record_call_outcome(lead_id, current_stage,
  outcome)`, reuses `CrmService.advance_lead` — no new "call outcomes" table.
- `apps/backend/presentation/voice_outbound_endpoints.py` — `POST /internal/voice/outbound-call`.
- `apps/backend/main.py` (edited) — registered the new router in the existing, non-try/except
  `/internal/*` registration block (fail-loud on import/registration error, per ARCHITECTURE.md
  Decisión #22/#24), added it to the log line listing registered `/internal/*` routes.
- `apps/chatwoot-bridge/whisper_client.py` — `transcribe(audio_bytes, mime_type)`, POSTs to
  `LOCAL_WHISPER_URL`, mirrors `voicebox_client.py`'s fail-soft shape.
- Tests: `apps/backend/tests/test_twilio_client.py`, `test_voice_call_script.py`,
  `test_voice_call_outcome.py`, `test_voice_outbound_endpoint.py`;
  `apps/chatwoot-bridge/tests/test_whisper_client.py`.
- `openspec/changes/taty-voice-outbound-calls/tasks.md` — checked off sections 2/3/4 sub-items
  that are genuinely done and green (see file for exact marks; 2.3 and part of 3.2 left unchecked
  — both are founder/infra actions outside this session's scope).

## Constraint-by-constraint

1. **`VOICE_OUTBOUND_CALLS_ENABLED` default false, gates only the cloned voice, independent of
   `VOICE_ENABLED`.** Added to `config.py` as its own flag. The endpoint never references a
   cloned voice at all — the opening is always spoken via Twilio's own `<Say voice="Polly.Lupe"
   language="es-MX">` (a real, generic, non-cloned voice). If the flag is somehow `true`, the
   endpoint logs a warning and still uses the generic voice (there is no cloned-voice code path to
   switch into). `test_default_flag_never_uses_cloned_voice` and
   `test_enabling_voice_outbound_calls_does_not_touch_whatsapp_voice_flag` cover this.
2. **B2B leads can never reach an outbound call.** `_get_lead_for_call` reads `lead_type`; the
   endpoint raises 403 before doing anything else (before checking Twilio config or resolving the
   phone) when `lead_type == "business_interest"`.
   `test_business_interest_lead_is_refused` is the explicit failing-then-passing test.
3. **Endpoint contract.** `POST /internal/voice/outbound-call`, `OutboundCallRequest(lead_id,
   tenant_id)` with `model_config = ConfigDict(extra="ignore")` — any `phone` field in the request
   body is silently dropped by pydantic before the handler ever sees it.
   `test_caller_supplied_phone_field_is_ignored` proves the resolved `crm_leads.whatsapp_phone` is
   used regardless of what the request tries to smuggle in. Auth mirrors
   `voice_endpoints.py`/`cadence_endpoints.py` exactly (`_verify_internal_key`, missing key → 503,
   wrong key → 401, checked before anything else). Router registration in `main.py` is in the
   existing non-try/except block; a broken import there fails the process at startup, not a
   silent log-and-continue.
4. **Twilio credentials.** Only in `config.py`/Railway env vars. Confirmed
   `apps/chatwoot-bridge/` has zero Twilio references (`grep -ri twilio apps/chatwoot-bridge`
   returns nothing). `services/twilio_client.py` uses plain `httpx`, not the `twilio` SDK.
5. **VoiceBox network-path gap — documented, not papered over.** The endpoint's fixed
   `{lead_id, tenant_id}` request shape (constraint 3/spec.md) rules out smuggling
   pre-synthesized audio bytes through the same call, and Railway cannot reach the local
   VoiceBox instance (same problem `voicebox-local-voice-adoption` solved once for WhatsApp voice
   notes via a local-synthesize/backend-deliver split). For this change, "generic voice" is
   satisfied via Twilio's own `<Say>` TTS. This is called out in
   `voice_outbound_endpoints.py`'s module docstring and in tasks.md's 2.4 note — **true VoiceBox
   integration into this specific flow is a documented follow-up, not built in this session.**
6. **STT (`LOCAL_WHISPER_URL`).** `apps/chatwoot-bridge/whisper_client.py::transcribe()` posts
   audio to it and returns the transcript text, mirroring `voicebox_client.py`'s two-call-style
   module layout and fail-soft contract. All 6 tests in `test_whisper_client.py` mock the HTTP
   call with `respx` — no real Whisper server is touched. **Not done**: pointing
   `LOCAL_WHISPER_URL` at an actual running Whisper instance (founder/infra action, out of scope
   for this session) — left unchecked in tasks.md 3.2.
7. **Opening script + qualification flow.**
   - **4.1 — Colombian AI-disclosure law: could not confirm.** This session has no access to a
     legal database. `core/voice_call_script.py`'s module docstring says so explicitly and states
     the safe default was used regardless (always disclose AI identity) — per design.md's own
     risk mitigation. This is a real open item, not resolved by this session; do not treat it as
     legally verified.
   - Opening script (`OPENING_SCRIPT` in `core/voice_call_script.py`) is Spanish, matches
     `taty_lead_router.py`/`cadence_schedule.py`'s tone, and in order: states identity ("te habla
     Taty de Contexia"), discloses AI identity explicitly ("soy un asistente de inteligencia
     artificial"), states the reason in well under 10 words ("Te llamo por tu declaración de
     renta."), then asks a question. `test_voice_call_script.py` asserts the disclosure appears
     before the `?`, and that no monetary/plan/offer word (`$`, `cop`, `precio`, `plan`, `oferta`,
     `pago`, `costo`, `gratis`, `descuento`) appears anywhere in the opening turn.
   - Qualification flow: `QUALIFICATION_QUESTIONS` is a hardcoded, ordered
     situación→problema→urgencia list of exactly 3; `next_qualification_question(answered_count)`
     returns `None` once `answered_count >= 3` — `test_a_fourth_question_is_never_returned`
     proves a 4th question is never returned.
   - Outcome → CRM: `services/voice_call_outcome.py::record_call_outcome` reuses
     `CrmService.advance_lead` — `qualified` advances stage to `PROSPECTOS`; `not_interested`,
     `callback_requested`, `voicemail` all keep the current stage and only stamp `lead_type` (same
     "pass the current stage back, only change lead_type" convention `taty_lead_router.py` already
     uses for `business_interest`, per ARCHITECTURE.md Decisión #16). No new table.
   - Voicemail does not trigger a re-dial: `test_voicemail_keeps_current_stage_and_does_not_
     trigger_a_redial` patches `services.twilio_client.place_call` and asserts it is never called
     — true by construction, since `voice_call_outcome.py` never imports `twilio_client` at all.
     Nothing in this change auto-invokes the outbound-call endpoint from anywhere (there is no
     call-status webhook yet), so the lead's only path back into an active flow is the existing
     `taty-followup-cadence` poller reading `crm_leads` on its own schedule.

## Tests added and run (py311, the only interpreter with pytest installed per MEMORY.md)

```
cd apps/backend && py -3.11 -m pytest tests/test_twilio_client.py tests/test_voice_call_script.py \
  tests/test_voice_call_outcome.py tests/test_voice_outbound_endpoint.py -q
-> 31 passed

cd apps/chatwoot-bridge && py -3.11 -m pytest tests/test_whisper_client.py -q
-> 6 passed
```

## Regression sweep (Task 6.1's discipline applied here, not the full Stage-11 sweep)

Full backend suite:
```
cd apps/backend && py -3.11 -m pytest -q --ignore=tests/test_profile_support.py \
  --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py
-> 35 failed, 1227 passed, 120 skipped, 24 warnings
```
The 3 ignored files fail at collection with `AttributeError: 'FieldInfo' object has no attribute
'in_'` in `presentation/metrics_endpoints.py` — confirmed via `git stash` to be present
**identically on the unmodified branch** (not something this session introduced).

Full chatwoot-bridge suite:
```
cd apps/chatwoot-bridge && py -3.11 -m pytest -q
-> 2 failed, 91 passed, 1 warning
```
Both failures (`test_chatwoot_client.py::TestCreateIncomingMessage::test_posts_an_incoming_
message`, `test_process_message.py::TestSingleBrainInvariant::test_reply_comes_from_the_sales_
router_not_hermes`) confirmed via `git stash` to be present **identically on the unmodified
branch**.

None of the 35 (backend) / 2 (bridge) pre-existing failures touch any file this session created
or edited. Zero regressions from this work.

`import main` in `apps/backend` raises the same pre-existing `metrics_endpoints.py` error on both
the modified and unmodified tree (confirmed via `git stash`) — this is not a router-registration
regression from this session's `main.py` edit (import order places `metrics_endpoints` before the
new `voice_outbound_endpoints` import, so my router is never reached in that particular failure
path either way).

## Explicitly NOT done (out of scope for this session, per the task brief)

- Task 2.3: real Twilio account/Colombian number provisioning — founder action.
- Task 3.2 (partial): pointing `LOCAL_WHISPER_URL` at a real running Whisper instance — founder/
  infra action.
- `VOICE_OUTBOUND_CALLS_ENABLED` was not flipped; no real Twilio call was placed; no legal
  citation for Colombian AI-disclosure law was invented.
- Tasks 5-9 in tasks.md were not touched.
