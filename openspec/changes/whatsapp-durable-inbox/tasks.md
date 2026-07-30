## 1. Migration — `whatsapp_inbound_events`

- [x] 1.1 Write `apps/backend/migrations/0036_whatsapp_inbound_events.sql`: table with
      `meta_message_id` UNIQUE (the dedup mechanism), normalized payload columns, `claimed_at`,
      `processed_at`, `created_at`. Idempotent (`IF NOT EXISTS`), additive only.
- [x] 1.2 Index for the pull query (unprocessed + unclaimed, ordered by `created_at`).
- [x] 1.3 Applied to Supabase 2026-07-30 with founder confirmation. Verified: all 11 columns
      present as designed, RLS enabled.

## 2. Receiver — persist, do not process

- [x] 2.1 Failing tests: a signed single-message payload stores exactly one row and returns 200;
      the lead router is NOT called during the request.
- [x] 2.2 Failing test: the same `meta_message_id` delivered 3× stores one row, all respond 200.
- [x] 2.3 New `apps/backend/services/whatsapp_inbox_service.py` with
      `store_inbound_events(events)` using `INSERT … ON CONFLICT (meta_message_id) DO NOTHING`.
- [x] 2.4 Wire `POST /webhook` in `presentation/whatsapp_endpoints.py` to call it after signature
      verification (the endpoint already stopped inline-routing in `taty-channel-consolidation`).
- [x] 2.5 Confirmed: `normalize_whatsapp_webhook` already exposes Meta's id as `source_event_id`
      (`channels/whatsapp.py`). **But it falls back to `""` when absent** — with a UNIQUE column
      that would collide every un-idded message into one row and silently discard real ones. The
      service therefore SKIPS such events loudly instead of writing a blank id; covered by
      `test_event_without_meta_id_is_never_written`.
- [x] 2.6 Tests green.

## 3. Pull / acknowledge contract

- [x] 3.1 Failing tests: pull returns unprocessed events and claims them; a second pull does not
      return claimed-and-unexpired events; an expired claim is redelivered; unauthenticated → 401.
- [x] 3.2 `GET /channels/whatsapp/inbox/pending` (authenticated, limit + claim TTL).
- [x] 3.3 `POST /channels/whatsapp/inbox/ack` (authenticated, marks `processed_at`).
- [x] 3.4 `GET /channels/whatsapp/inbox/health` — backlog depth + oldest unprocessed age
      (design.md Risk: a queue nobody watches is a queue that quietly grows).
- [x] 3.5 Tests green.

## 4. Bridge poller + Chatwoot injection

- [x] 4.1 Failing tests: poller injects each pulled event into Chatwoot and acknowledges only on
      success; a failed injection leaves the event unacknowledged.
- [x] 4.2 `apps/chatwoot-bridge/inbox_poller.py` — interval poll, reusing `backend_client`'s
      existing `sign_tenant_jwt()` / `_headers()` auth path.
- [x] 4.3 Chatwoot injection: find-or-create contact by phone, find-or-create conversation on the
      WhatsApp inbox, create the incoming message.
- [x] 4.4 Wire the poller into the bridge's startup; keep it optional via env so the bridge can
      still run without it.
- [x] 4.5 Do NOT call `taty_reply` from the poller — Chatwoot's own webhook to the bridge drives
      the reply, preserving the single-brain invariant and the `bot_off` HITL check
      (design.md Decision 6).
- [x] 4.6 Bridge tests green.

## 5. FOUNDER ACTION — prerequisites

- [x] 5.1 Created 'Taty Bot' (user id 4) directly in Chatwoot's Postgres: agent role on account 2,
      member of inbox 1 (Taty Contadora Amiga), own access_tokens row. ITS token (not the founder's)
      is now CHATWOOT_API_TOKEN in apps/chatwoot-bridge/.env, so bot vs human replies are
      distinguishable by sender_id going forward.
- [x] 5.2 Approved and applied 2026-07-30.
- [x] 5.3 Set in Railway 2026-07-30: `WHATSAPP_WEBHOOK_VERIFY_TOKEN`, `META_WEBHOOK_VERIFY_TOKEN`
      (founder-agnostic, generated), `WHATSAPP_APP_SECRET` (founder-provided, real Meta app
      secret — the account has exactly one app, WhatsApp-only; no separate Instagram/Facebook app
      exists yet, so `META_APP_SECRET` stays empty and fails closed by design, not left over).

## 6. Verify

- [x] 6.1 Full backend suite: 732 passed / 40 failed / 112 skipped — same 40 pre-existing failures
      verified against a clean `main` worktree (2 more passing than before, from this change's new
      tests). `init.sh` structural gate green.
- [x] 6.2 Local end-to-end, done for real (not simulated): started the local backend (`:8080`) and
      bridge (`:8090`) against the live Chatwoot containers and the same production Supabase
      project. Built a signed synthetic Meta payload, POSTed it — row landed in
      `whatsapp_inbound_events`, the running poller (5s interval) picked it up unprompted, created
      the Chatwoot contact + conversation on the `Channel::Api` inbox (see design.md Decision 7),
      and posted the message. Verified directly in Chatwoot's Postgres: `messages` row exists,
      `message_type=0` (incoming), `sender_type=Contact`. `processed_at` set after ack.
      **Two real bugs found and fixed by this drill** (both were latent, neither caught by the
      730-passing suite because their mocks operated above the real client/query layer):
      1. `pull_pending`'s `.or_()` call — the installed `postgrest` (0.13.2) has no such method;
         it was added in a later release. Fixed to build the `or=(...)` param directly via
         `query.params.add(...)`, the same mechanism `.filter()` uses internally. New test
         (`TestPullPendingQueryConstruction`) builds the query against the REAL installed
         postgrest client class (no network) specifically so a missing/renamed method fails here
         again, instead of a `MagicMock` silently answering to anything.
      2. Chatwoot rejected `message_type: incoming` on the native `Channel::Whatsapp` inbox
         (`"Incoming messages are only allowed in Api inboxes"`) — a real design-assumption gap,
         not a code bug; resolved by design.md Decision 7 (dedicated `Channel::Api` inbox).
- [x] 6.3 Durability drill, done unintentionally and instructively: killing the bridge process
      mid-cycle (to apply a config fix) left the test event claimed-but-unprocessed — proving the
      claim mechanism works exactly as designed. Resetting `claimed_at` and letting a clean cycle
      run completed the injection with zero data loss.
- [x] 6.4 Duplicate drill: the same signed payload posted 3× total → exactly 1 row in
      `whatsapp_inbound_events`, exactly 1 message in Chatwoot. Forged-signature request (random
      hex, wrong secret) → `403`, confirmed on the same live backend instance.
      **Incident during this drill, disclosed and resolved**: enabling the real Supabase
      service-role key locally (needed for this test) caused an unrelated pre-existing test,
      `test_operator_task_service.py::test_rejects_a_decision_that_is_not_a_campaign_package`, to
      execute a REAL insert against production `operator_tasks` (previously it "passed" only
      because missing local credentials made the Supabase client fail to initialize — an
      accidental pass, not a real one). The test's mock ignores the `draft_type` filter, and
      `dispatch_campaign_package()` had no independent check of `decision.draft_type` before
      inserting — trusting the filter alone. 5 junk rows (`status=pending`, the same status
      Hermes/Manus poll for real dispatch) landed in production; founder confirmed, all 5 deleted
      by exact id, verified 0 remaining. Fixed the underlying gap with a defense-in-depth check
      in `operator_task_service.py` (reject if `decision.draft_type != "campaign_package"` even
      if the caller's filtering was wrong), re-verified 0 rows inserted on re-run, full suite
      back to the expected 40-failure baseline (732 passed).

## 7. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [x] 7.1 Merged via PR #8 (gh pr merge --merge --delete-branch).
- [x] 7.2 Railway deployment b7ffa31c SUCCESS, /api/v1/health 200 after documented cold-start.
- [ ] 7.3 Confirm the inbox health endpoint reports a real backlog figure in production
- [ ] 7.4 Create report: `openspec/changes/whatsapp-durable-inbox/reports/YYYY-MM-DD-deployment.md`

## 8. Archive

- [ ] 8.1 Sync the capability into `openspec/specs/` and archive (`git mv` for the archive move).
