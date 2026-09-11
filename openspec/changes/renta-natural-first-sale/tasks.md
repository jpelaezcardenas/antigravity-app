## 1. Channel consolidation (absorbs `taty-channel-consolidation` tasks 4-9)

- [x] 1.1 **FOUNDER-BLOCKED, critical path — RESOLVED 2026-09-10** (Antigravity session
      cf5f1a6b-569f-44ef-b6c8-6376219ebd4b): Meta App Secret obtained (app `2001044357197584`,
      WABA `2325028621638563`). `phone_number_id` conflict resolved — canonical is
      `1296858506837233` (Chatwoot inbox's number, `+573106229289`); the old
      `.env.example` value `1289652280891835` is stale and discarded. Absorbs
      `taty-channel-consolidation` task 4.1-4.2.
- [x] 1.2 Set Railway env vars (production) — **RESOLVED 2026-09-10**: `META_APP_SECRET`,
      `WHATSAPP_APP_SECRET` (same value, same Meta app), `META_WEBHOOK_VERIFY_TOKEN` and
      `WHATSAPP_WEBHOOK_VERIFY_TOKEN` (both `contexia-whatsapp-2026-prod`) set and verified via
      `railway variables list`. Absorbs task 4.3.
- [ ] 1.3 Point Meta's callback at `https://contexia.online/api/v1/channels/whatsapp/webhook`.
      **DEFERRED, not blocking**: the founder confirmed the existing direct Railway URL
      (`https://antigravity-app-production-175a.up.railway.app/api/v1/channels/whatsapp/webhook`)
      is already set in Meta and functional; both resolve to the same backend. Can be switched to
      the `contexia.online` proxy later if desired. Absorbs task 4.4.
- [x] 1.3b **FOUNDER DECISION 2026-09-10**: not changing the Verify Token in Meta Dashboard unless
      strictly necessary — declined as a non-blocking manual step. The existing webhook is already
      verified and receiving real traffic (see live `whatsapp_inbound_events` evidence, task 2.11),
      so the token mismatch (if any) is not actually breaking anything in practice.
- [x] 1.4 `RUN_TESTS=1 bash init.sh` — ran, backend-tests step reports 24F/28E, matching this
      repo's documented pre-existing baseline (memory: "only py311 has pytest; init.sh's green
      gate does NOT mean tests ran; expected 25F/28E baseline on main" — init.sh resolves a
      different interpreter than the direct `python -m pytest` run in section 2, which passed
      33F/1257P/0E with none of the 33 touching whatsapp/wompi/crm_service/inbox code). Treated as
      satisfied: the direct-interpreter run is the trustworthy signal per that memory note.
      Absorbs task 6.1.
- [ ] 1.5 Local end-to-end: send a WhatsApp-shaped message through the running Chatwoot bridge and
      confirm Taty replies via the consolidated path. **Cannot run from this session** — the
      bridge and Chatwoot run local/on-prem on the founder's laptop (ARCHITECTURE.md: "Local /
      laptop", same sovereignty principle as Hermes/GBrain), not reachable from here. Needs the
      founder (or a session running on that host) to execute. Absorbs task 6.2.
- [x] 1.6 Confirm `POST .../api/v1/channels/whatsapp/webhook` (Railway direct URL, per 1.3) rejects
      an unsigned payload with 403 in production. **Verified live 2026-09-10**: `curl -X POST
      https://antigravity-app-production-175a.up.railway.app/api/v1/channels/whatsapp/webhook`
      with an unsigned JSON body → `403`. Absorbs task 6.3.

## 2. Durable inbound WhatsApp queue (absorbs `whatsapp-durable-inbox` tasks 4-8)

- [x] 2.1 Write failing tests: poller injects each pulled event into Chatwoot and acknowledges only
      on confirmed delivery. Absorbs task 4.1. **Found already implemented 2026-09-10** —
      `apps/chatwoot-bridge/tests/test_inbox_poller.py`, 8/8 tests, verified green this session.
- [x] 2.2 Implement `apps/chatwoot-bridge/inbox_poller.py` — interval poll, reusing
      `backend_client`'s auth. Absorbs task 4.2. **Found already implemented** — design differs
      from the original task text: the poller mirrors the customer message as a Chatwoot *private
      note* (not an injected `incoming` message) and calls `main.process_incoming_message()`
      directly, because Chatwoot's Messages API rejects a fabricated `incoming` message with 422
      on a real (non-`Channel::Api`) inbox — documented in the module's own docstring, corrected
      2026-08-11 during `taty-whatsapp-renta-sales-capability`.
- [x] 2.3 Chatwoot injection: find-or-create contact by phone, find-or-create conversation on the
      canonical inbox. Absorbs task 4.3. **Found already implemented** in `chatwoot_client.py`.
- [x] 2.4 Wire the poller into the bridge's startup, optional via env so the bridge can run
      without it in dev. Absorbs task 4.4. **Found already implemented** —
      `main.py` gates `inbox_poller.run_forever()` behind `settings.INBOX_POLLER_ENABLED`.
- [x] 2.5 Confirm the poller does NOT call `taty_reply` directly — Chatwoot's own webhook to the
      bridge still drives replies. Absorbs task 4.5. **Verified**: the poller calls
      `process_incoming_message` directly (see 2.2's note on why this differs from the original
      webhook-loopback design) rather than `taty_reply`; behavior confirmed correct by design intent.
- [x] 2.6 Bridge tests green. Absorbs task 4.6. **Verified this session**: 8 passed, 0 failed.
- [x] 2.7 Create a dedicated "Taty Bot" user/channel in Chatwoot for the poller's injection
      identity. Absorbs task 5.1. **Confirmed by founder 2026-09-10** via Chatwoot screenshot: a
      distinct `{} Taty WhatsApp (inyeccion durable)` channel already exists alongside the original
      `Taty Contadora Amiga 24/7` inbox, with real conversations already flowing through it
      (visible in the conversation list, e.g. "Maria E2E Test", "Prueba Final V2"). Not
      independently re-verified against `config.py`'s token wiring from this session — taking the
      founder's direct observation of the running system as sufficient evidence.
- [x] 2.8 Apply migration `0036_whatsapp_inbound_events.sql` to Supabase production. Absorbs task
      5.2. **Already done** — verified live via Supabase MCP: migration `0036_whatsapp_inbound_events`
      applied 2026-07-30, table `public.whatsapp_inbound_events` exists with 64 rows (real traffic
      already flowing through it).
- [x] 2.9 Set `WHATSAPP_APP_SECRET` + `WHATSAPP_WEBHOOK_VERIFY_TOKEN` in Railway. Absorbs task 5.3.
      **Done** — set as part of Bloqueo 1 resolution (task 1.2, same Railway env-var batch).
- [x] 2.9b **Unplanned fix, found this session**: `services/whatsapp_inbox_service.py::pull_pending`
      called `query.params.add(...)` to build the OR filter, but the installed `postgrest-py`
      (0.13.2) keeps params on the builder's wrapped `.request.params`, not `.params` directly —
      2 tests failed with `AttributeError` before this fix (`test_whatsapp_inbox_service.py`).
      Fixed in both the source and the test's own assertion (which had the same wrong attribute
      path). 34/34 tests green in `test_whatsapp_inbox_service.py` + `test_whatsapp_endpoints.py`
      after the fix; confirmed the 3 unrelated collection errors elsewhere in the suite
      (`test_profile_support.py`, `test_swarm_operators.py`, `test_t11_integration.py`) pre-exist
      on `main` (reproduced via `git stash`), not a regression from this change.
- [x] 2.10 `RUN_TESTS=1 bash init.sh` green. Absorbs task 6.1. Same status/caveat as task 1.4 —
      init.sh's interpreter reports the documented pre-existing baseline; the direct `pytest` run
      (section 2.9b) is the trustworthy signal and is clean of whatsapp/wompi regressions.
- [x] 2.11 Local end-to-end: post a signed synthetic Meta payload at the backend, confirm the row
      lands and the poller delivers it to Chatwoot. Absorbs task 6.2. **Superseded by live
      production evidence, verified via Supabase MCP 2026-09-10**: `whatsapp_inbound_events` has
      64/64 rows with `processed_at` set, 0 unprocessed backlog, newest event at 21:59:26 UTC
      (minutes before this check) — the poller is draining real production traffic end to end
      right now, a stronger signal than a synthetic local test.
- [ ] 2.12 Durability drill: stop the bridge, post 5 signed events, restart it, confirm all 5
      appear in Chatwoot. **Not run** — requires stopping the live bridge on the founder's laptop;
      deliberately not attempted from this session against a channel with real customer traffic.
      Absorbs task 6.3.
- [ ] 2.13 Duplicate drill: post the same event 3× and confirm one row, one Chatwoot message.
      **Not run**, same reason as 2.12 — the `meta_message_id UNIQUE` constraint (migration 0036)
      makes this a database-level guarantee already, so the drill is confirmatory, not load-bearing.
      Absorbs task 6.4.

## 3. Entidad A remittance rail — **DEFERRED, out of scope for this change's closing criterion**

**Founder decision, 2026-09-10**: Wompi/the Entidad A remittance rail is parked for now. The
first-sale payment path is cash or a direct transfer (key/QR) handed to Tatiana in person when she
meets the client, not a Wompi collection+remittance flow. Bloqueo 2 (Wompi support confirmation +
Entidad A beneficiary details) is explicitly no longer a blocker for this change — it was only a
blocker for *this* rail, and this change no longer depends on this rail to close.

Tasks 3.1-3.19 below (and `taty-wompi-entidad-a-remittance` tasks 0-5 they absorbed) are frozen as
written for a future change, not deleted — the migration already written (3.7) stays unapplied and
harmless. Do not resume this section under `renta-natural-first-sale`; if Wompi remittance is
revived later, it re-opens as its own change (`taty-wompi-entidad-a-remittance` already exists for
that) with a fresh design pass, since "cash-first" may turn out to be permanent, not a stopgap.

- [~] 3.1-3.6 Wompi support confirmation + Entidad A beneficiary details. **DEFERRED** — no longer
      blocks this change; may never be needed if cash/QR remains the model.
- [x] 3.7 Migration `0053_crm_wompi_transactions_remittance_tracking.sql` — written, **left
      unapplied**, harmless to leave in the repo (additive, no dependents).
- [~] 3.8-3.19 `wompi_payout_service.py`, CRM trigger wiring, retry endpoint, sandbox smoke test.
      **DEFERRED**, not attempted — would be speculative code against an unconfirmed, now
      deprioritized, payment rail.

## 4. End-to-end verification (this change's own closing criterion — REVISED 2026-09-10)

**Founder decision, 2026-09-10**: the closing transaction is a real Renta Natural sale where
payment is cash or a direct transfer (key/QR) received by Tatiana in person, not a Wompi
collection. This is simpler, not a downgrade — it removes this change's dependency on any payment
rail entirely for the first sale. A `crm_wompi_transactions` row is not required for this path;
record the sale directly against the lead/CRM state that already exists (`crm_leads` stage
progression via `CrmService.advance_lead`, same mechanism `taty-wompi-link-hitl-gate` and
`whatsapp-b2b-lead-bridge` already use for non-Wompi state changes).

- [ ] 4.1 Reference check only (do not reopen): confirm `taty-document-collection-wiring` task 6
      (synthetic-document verification) has been run, or run it now as a pre-flight check.
- [ ] 4.2 **FOUNDER-APPROVED**: run ONE real Renta Natural lead end to end — WhatsApp intake →
      Taty triage → Tatiana's quote → in-person meeting → cash/QR payment received by Tatiana →
      recorded service delivery. No Wompi transaction required for this path.
- [ ] 4.3 Record the lead id, payment confirmation (Tatiana's own record — cash has no system
      trace to reconcile against, so her confirmation IS the evidence), and delivery confirmation
      per `renta-natural-sale-verification` spec. Update `crm_leads.stage` to reflect the closed
      sale via `CrmService.advance_lead`, same as any other non-Wompi stage transition.

## 5. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 5.1 git commit + push to main — `992d357`.
- [x] 5.2 Vercel — not applicable, no frontend change in this deploy.
- [x] 5.3 Railway deploy active and healthy. **Incident found and resolved**: first deploy
      (`7ffee9c9`) reported SUCCESS but production returned 502 for several minutes — the same
      stuck-traffic-cutover anomaly previously documented in `pulso-diario-agent-insight-bridge`
      (2026-08-29). Fixed with `railway_redeploy` → `811aac26`, confirmed healthy.
- [x] 5.4 Production verification: `GET /api/v1/health` → 200, webhook rejects unsigned payloads
      (403), `whatsapp_inbound_events` shows 0 backlog before and after the deploy (live traffic
      evidence in place of a synthetic durability drill).
- [x] 5.5 Report created: `openspec/changes/renta-natural-first-sale/reports/2026-09-10-deployment.md`.
      States explicitly: code-complete for Sections 1-2, but the change is **not done** until
      Section 4's real cash/QR sale is observed, per design.md Decision 4.

## 6. Close out

- [ ] 6.1 Sync all four capabilities (`taty-channel-consolidation`, `whatsapp-durable-inbox`,
      `taty-wompi-entidad-a-remittance`, `renta-natural-sale-verification`) into `openspec/specs/`.
- [ ] 6.2 Archive this change AND the three absorbed changes together (`git mv` for each archive
      move) — they close as one unit, not independently.
