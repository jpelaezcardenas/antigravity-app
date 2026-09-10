# Review — task taty-followup-cadence (`taty-voice-outbound-calls`, Task 1)

**Verdict:** APPROVED

## Checkpoints

- C1 (tasks.md 1.1 — failing tests written for the three scenarios first, TDD): [x]
  `tests/test_cadence_schedule.py`, `tests/test_cadence_endpoint.py`,
  `tests/test_taty_lead_router_cadence_reset.py` map 1:1 to spec.md's three scenarios.
- C2 (tasks.md 1.2 — day-indexed D1/D2/D4/D7/D14 table, text-only, no invented price/legal claim):
  [x] `apps/backend/core/cadence_schedule.py:30-66` — `CADENCE_SCHEDULE` has exactly `{1,2,4,7,14}`;
  `test_cadence_schedule.py:13-18` asserts no `$`/`%`/`garantiz` token in any message.
- C3 (tasks.md 1.3 — cadence poller, mirrors existing poller pattern, no new send mechanism): [x]
  `apps/hermes-cadence-poller/` mirrors `hermes-gmail-poller/` layout; sends via
  `POST /internal/cadence/send-touch` → `channels/whatsapp.py::send_whatsapp_message`, the existing
  Chatwoot delivery path — no new send code.
- C4 (tasks.md 1.4 — Scheduled Task registration): [x] `register_poller_task.ps1` diffed 1:1
  against `hermes-gmail-poller/register_poller_task.ps1` — same `New-ScheduledTaskAction
  -WorkingDirectory $scriptDir` pattern, `pythonw.exe`/`python.exe` fallback, `AtLogOn` +
  repeating trigger. Correctly does NOT introduce the `cmd /c cd /d ...` wrapper that the stale
  tasks.md:20-22 text describes — that text describes an older, since-abandoned pattern; the repo's
  actual poller scripts (Gmail/Siigo/HubSpot) never use it. Not registered on this machine, per the
  implementer's own report — correct, `Register-ScheduledTask` is a founder action.
- C5 (tasks.md 1.5 — tests green): [x] Verified independently, not "implementer says so":
  - `pytest tests/test_cadence_schedule.py tests/test_cadence_endpoint.py
    tests/test_taty_lead_router_cadence_reset.py tests/test_taty_lead_router.py` → 86 passed.
  - `apps/hermes-cadence-poller/tests/` → 13 passed.
  - Regression sweep (`test_whatsapp_endpoints.py`, `test_taty_endpoints_tenant_scoping.py`,
    `test_voice_endpoint_auth.py`, `test_whatsapp_reply_voice_allowed.py`,
    `test_crm_whatsapp_intake.py`) → 62 passed, 0 failed.
- C6 (spec.md scenario 1 — silent lead gets next scripted touch, cadence advances): [x]
  `test_cadence_endpoint.py::test_happy_path_sends_and_advances_cadence` exercises the real
  `send_cadence_touch_endpoint` coroutine end-to-end (auth → eligibility → threshold → send →
  advance), only mocking the Supabase/WhatsApp I/O boundaries, not the logic under test. Threshold
  logic itself (`next_due_day`) is tested directly and unmocked in `test_cadence_schedule.py`.
- C7 (spec.md scenario 2 — a lead who replies exits the cadence, enforced at a real write path):
  [x] Not just asserted in a docstring. `taty_lead_router.py:392-400` calls
  `_record_inbound_and_reset_cadence(lead_id)` unconditionally at the top of `route_lead_message`
  — the single entry point every real inbound WhatsApp message passes through
  (`presentation/whatsapp_endpoints.py::taty_lead_reply` calls it directly, confirmed via the
  docstring cross-reference and this file's existing routing structure). The reset function itself
  (`_record_inbound_and_reset_cadence`, lines 167-183) is tested unmocked in
  `TestRecordInboundAndResetCadence` — it patches only `get_service_supabase` (the DB boundary),
  then asserts the real update payload sets `cadence_day: None` and stamps `last_inbound_at`. This
  is the one place I checked hardest for the "test mocks the exact frontier it claims to verify"
  failure mode from ARCHITECTURE.md Decisión #22 — it does not: the boundary mocked is Supabase
  I/O, the logic asserted (clearing `cadence_day`, never reusing `updated_at`) is real.
- C8 (spec.md scenario 3 — day-14 completion sends no further touch): [x]
  `next_due_day(current_day=14, ...)` returns `None` unconditionally (schedule-level, unmocked) and
  `test_completed_cadence_sends_no_further_touch` exercises the real endpoint against a lead with
  `cadence_completed_at` set → `sent=False, reason="cadence_completed"`.
- C9 (spec.md — task inert without config, not a silent no-op): [x] confirmed via implementer
  report + code read: missing `INTERNAL_API_KEY`/Supabase creds → poller logs an error and returns
  `{"skipped": True, "reason": ...}`, matching the Gmail/Siigo poller convention.
- C10 (ARCHITECTURE.md Decisión #22/#24 — `/internal/*` pattern): [x]
  `cadence_endpoints.py:47-52` checks the header before any body validation, 503 on unset env var,
  401 on mismatch, verified live via `test_missing_internal_key_env_returns_503`,
  `test_wrong_key_returns_401`, and `test_auth_is_checked_before_day_validation` (day=999 with a
  wrong key still returns 401, not 400 — anti-enumeration). `main.py:255-269` registers
  `cadence_router` under `_internal_router` with **no** `try/except` wrapper, consistent with the
  explicit comment there citing the Decisión #22 incident.
- C11 (ARCHITECTURE.md Decisión #23 discipline — migrations written, never applied without
  founder approval): [x] `migrations/0051_crm_leads_cadence.sql` is a plain `ALTER TABLE ... ADD
  COLUMN IF NOT EXISTS` file with an explicit header stating it is NOT applied and why; no
  evidence anywhere (poller, tests, scripts) of a live `psql`/Supabase migration run. The
  `register_poller_task.ps1` prerequisites list explicitly tells the founder to apply it first.
- C12 (scope discipline — nothing from Tasks 2-9 touched): [x] `git status --short` shows only
  cadence-scoped new/modified files (`core/cadence_schedule.py`, `presentation/cadence_endpoints.py`,
  `main.py` router registration, `services/taty_lead_router.py` inbound hook, cadence tests,
  `apps/hermes-cadence-poller/`) plus pre-existing unrelated dirty files from earlier sessions
  (`plan_features.py`, `TenantInfoCard.tsx`, `UpgradePlanBanner.tsx`, `radar-adoption-tracking`
  deletions) that predate this task and are not this implementer's work. Grepped for
  `Twilio`/`VOICE_OUTBOUND_CALLS_ENABLED`/`LOCAL_WHISPER_URL`/qualification/opening-script across
  the new poller and `cadence_endpoints.py` — the only hit is a doc comment stating explicit
  *non*-dependency on those flags (`cadence_endpoints.py:3`), not usage.
- Docs-sync: [x] No container/dependency change — this is a new internal endpoint + local poller
  following an already-documented pattern (Decisión #22's poller precedent). No ARCHITECTURE.md
  update required for this piece; Stage 11 (deploy) and its own report are correctly left as the
  implementer's documented next step, not yet done, matching tasks.md 1.5/11.1.

## Notes (non-blocking)

- Migration 0051 is unapplied — expected and correct per the founder-approval discipline. The
  poller/endpoint degrade in a controlled way (500 from the Supabase client on the missing
  columns) until applied; this is documented in the migration file header and the implementer
  report, not hidden.
- `apps/hermes-cadence-poller/cadence_rules.py` deliberately duplicates the threshold table rather
  than importing backend code across the process boundary — same convention as the other pollers,
  acceptable and explained in the implementer's own comment.

No required changes.
