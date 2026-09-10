# Implementer report — Task 1 `taty-followup-cadence` (`taty-voice-outbound-calls`)

Scope: Task 1 only (1.1–1.5). Tasks 2-9 (Twilio/voice outbound calls) untouched — blocked on
founder consent, explicitly out of scope this session.

## What was built

### Backend (Railway-deployed)

- `apps/backend/migrations/0051_crm_leads_cadence.sql` — adds `crm_leads.last_inbound_at`,
  `crm_leads.cadence_day`, `crm_leads.cadence_completed_at`. **NOT applied to the live database.**
  Applying migrations requires explicit founder approval (see file header for the full rationale
  on why `last_inbound_at` is a new explicit column rather than reusing `updated_at`, which is
  bumped by unrelated writes like `advance_lead`/`update_tax_profile`).
- `apps/backend/core/cadence_schedule.py` — the day-indexed message table (D1/D2/D4/D7/D14),
  Spanish WhatsApp copy with no invented price/legal claim, plus `next_due_day()`.
- `apps/backend/presentation/cadence_endpoints.py` — `POST /internal/cadence/send-touch`
  (`{lead_id, day}` body only — never trusts a caller-supplied message string). Follows the
  `/internal/*` + `INTERNAL_API_KEY` pattern from `voice_endpoints.py` exactly: auth checked
  before anything else, missing key → 503, wrong key → 401, malformed `day` → 400, unknown lead →
  404, everything else (stage not `NUEVOS`, cadence already completed, day already sent, not due
  yet, no phone, send failed) → 200 `{sent: false, reason: "..."}`.
- `apps/backend/services/taty_lead_router.py` — `route_lead_message()` now calls
  `_record_inbound_and_reset_cadence(lead_id)` on every inbound message (best-effort, wrapped in
  try/except so a Supabase hiccup never blocks the actual reply to the lead — matches this file's
  existing degrade-gracefully convention on the `unknown`-intent branch). This is what makes "a
  lead who replies exits the automated cadence" true.
- `apps/backend/main.py` — registered `cadence_router` under `_internal_router` exactly like
  `siigo_sync_router`/`ingest_file_router`/`voice_router` (no try/except around registration, per
  ARCHITECTURE.md Decisions #22/#24).

### Local poller (`apps/hermes-cadence-poller/`, mirrors `apps/hermes-gmail-poller/` layout)

- `config.py`, `cadence_rules.py` (deliberately duplicated threshold table, not imported from
  backend — cross-package boundary, comment explains why drift here is harmless), `supabase_client.py`,
  `poller.py`, `main.py`, `requirements.txt`, `register_poller_task.ps1`, `tests/`.
- Inert-without-config: missing `INTERNAL_API_KEY` or Supabase creds logs an error and returns
  `{"skipped": True, "reason": ...}` — never a silent "nothing was due".
- `register_poller_task.ps1` mirrors the **current, actually-working**
  `hermes-gmail-poller/register_poller_task.ps1` pattern: `New-ScheduledTaskAction` with
  `-WorkingDirectory $scriptDir`, `pythonw.exe`/`python.exe` fallback via `Get-Command`, `AtLogOn`
  trigger + a repeating trigger (60 min, day-granular cadence doesn't need 15-min polling). **Not
  registered on this machine** — writing the script is the deliverable per the task prompt; actual
  `Register-ScheduledTask` is a founder action.

## Test results

Backend (Python 3.11 — the only interpreter with pytest installed, per
`project_pytest_interpreter_py311` memory):

```
tests/test_cadence_schedule.py tests/test_cadence_endpoint.py
tests/test_taty_lead_router_cadence_reset.py tests/test_taty_lead_router.py
86 passed
```

Broader regression sweep (files this change touches or is adjacent to):

```
tests/test_whatsapp_endpoints.py tests/test_taty_lead_router.py
tests/test_taty_endpoints_tenant_scoping.py tests/test_voice_endpoint_auth.py
tests/test_whatsapp_reply_voice_allowed.py tests/test_crm_whatsapp_intake.py
122 passed, 0 failed
```

Poller (`apps/hermes-cadence-poller/`):

```
tests/test_cadence_rules.py tests/test_poller.py
13 passed
```

Zero-regression discipline: confirmed `python -c "import main"` fails identically on `main`
(pre-existing `metrics_endpoints.py` FastAPI/Pydantic version incompatibility, unrelated to this
change — reproduced via `git stash`/`git stash pop`, same `AttributeError:
'FieldInfo' object has no attribute 'in_'` on both). No test suite in this repo currently
exercises the full `app` import path for that reason; all cadence tests import only the specific
modules touched, same as the existing `test_voice_endpoint_auth.py` pattern.

## Deferred / not verifiable from this sandbox

- Migration `0051_crm_leads_cadence.sql` — written and reviewed at the file level only, **not
  applied**. Needs explicit founder approval.
- Windows Scheduled Task registration (`Register-ScheduledTask`) — script written, not run.
- No live Supabase or Railway endpoint was hit; all tests mock at the module boundary (Supabase
  client, `httpx`, `send_whatsapp_message`), same convention as every other poller/internal-
  endpoint test in this repo.
- Deploy (Stage 11: git push to main, Railway auto-deploy, live verification) not performed —
  that is this change's next step per its own tasks.md (1.5 "Deploy this piece independently"),
  and is a separate action from implementation.

## Files touched/created

- `apps/backend/migrations/0051_crm_leads_cadence.sql` (new, unapplied)
- `apps/backend/core/cadence_schedule.py` (new)
- `apps/backend/presentation/cadence_endpoints.py` (new)
- `apps/backend/main.py` (modified — router registration)
- `apps/backend/services/taty_lead_router.py` (modified — cadence reset on inbound)
- `apps/backend/tests/test_cadence_schedule.py` (new)
- `apps/backend/tests/test_cadence_endpoint.py` (new)
- `apps/backend/tests/test_taty_lead_router_cadence_reset.py` (new)
- `apps/hermes-cadence-poller/config.py`, `cadence_rules.py`, `supabase_client.py`, `poller.py`,
  `main.py`, `requirements.txt`, `register_poller_task.ps1` (all new)
- `apps/hermes-cadence-poller/tests/test_cadence_rules.py`, `tests/test_poller.py` (new)
