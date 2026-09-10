# Task 5 — Non-goal guards (verify, don't build)

**Change:** b2c-social-lead-capture
**Status of change at verification time:** only 1 commit exists (`34b1a8e docs(openspec):
propose b2c-social-lead-capture`) — no implementation code for this capability exists in the
repo yet. Confirmed via `git log --oneline --all | grep -i "b2c-social-lead-capture"`.

## 5.1 — No coupling to taty-voice-outbound-calls, hermes-hubspot-poller, or any B2B path

Since this change has no code yet, verification reduces to: does any EXISTING code in those
three areas reference or depend on this capability (`social-capture`, `b2c-social-lead-capture`,
a `crm_leads.source` stamp tied to it, etc.)?

Evidence:

```
grep -rn "social-capture|social_capture|b2c-social-lead-capture|b2c_social" apps/backend --include="*.py" -l
→ (no matches)

grep -rln "taty.voice.outbound|voice_outbound|taty-voice-outbound" apps/backend --include="*.py"
→ apps/backend/config.py
  apps/backend/core/cadence_schedule.py
  apps/backend/core/voice_call_script.py
  apps/backend/main.py
  apps/backend/presentation/voice_outbound_endpoints.py
  apps/backend/services/twilio_client.py
  apps/backend/services/voice_call_outcome.py
  apps/backend/tests/test_cadence_endpoint.py
  apps/backend/tests/test_twilio_client.py
  apps/backend/tests/test_voice_call_outcome.py
  apps/backend/tests/test_voice_outbound_endpoint.py

grep -n "social|b2c" on each of those files
→ no matches (grep exit 0 with empty output before the crm_service.py block below)

grep -rln "hubspot" apps/backend --include="*.py"
→ apps/backend/services/crm_service.py  (only file referencing hubspot at all)

grep -n "social|b2c" apps/backend/services/crm_service.py
→ 3 hits, all unrelated to this change:
  - line 3: "mirroring services.social_ops_service" (a different, pre-existing module —
    Social Content Ops, not social lead capture)
  - line 58, 73, 489, 509: "B2C sell-machine funnel" / "b2c_pipeline" — this is the
    PRE-EXISTING `crm-b2c-sell-machine-cockpit` change (Change B, referenced explicitly in the
    comment), a different capability with its own funnel/pipeline, NOT
    `b2c-social-lead-capture`. No reference to this change's endpoint, source tag, or design.

find apps/hermes-hubspot-poller -type f | xargs grep -ln "social|b2c"
→ (no matches)
```

**Conclusion:** no existing code in `taty-voice-outbound-calls`, `hermes-hubspot-poller`, or any
B2B path references or depends on `b2c-social-lead-capture`. The only "b2c" hits found belong to
the unrelated, pre-existing `crm-b2c-sell-machine-cockpit` change and the unrelated
`social_ops_service` module (Social Content Ops). Since this change's own code has not been
written yet, there is nothing on this change's side that could create the coupling either.
Guard confirmed → **5.1 marked `[x]`**.

## 5.2 — `contexia-wizard/` untouched by this change

Evidence:

```
git status --porcelain contexia-wizard/
→ (empty — no pending changes)

git log --oneline -5 -- contexia-wizard/
→ 378338b Update WhatsApp number to 573106229289 across landing and wizard
  4992da4 fix(pricing): update crear empresa price to 1.200.000 COP
  8388f15 Merge branch 'claude/angry-sutherland-976d5d' into main for Stage 11 deployment
  7de746a feat(wizard): personalización Rueda de Negocios Estud-IA 2026-06-17
  0116be4 feat(sso): go-live hardening — fail-closed middleware, CORS cleanup, drop carlos refs

git status --porcelain | grep -i wizard
→ (empty)
```

None of the 5 most recent commits touching `contexia-wizard/` mention or belong to
`b2c-social-lead-capture` (the change branch is `feat/voicebox-local-voice-adoption`, an unrelated
prior change — confirmed via git status at session start). There are zero uncommitted changes
under `contexia-wizard/`. Guard confirmed → **5.2 marked `[x]`**.

## Files touched

- `openspec/changes/b2c-social-lead-capture/tasks.md` — marked 5.1 and 5.2 `[x]` with the
  evidence above.

No code was written or modified. This is a read-only verification task per its own description.
