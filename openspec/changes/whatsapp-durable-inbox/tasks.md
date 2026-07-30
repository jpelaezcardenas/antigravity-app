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

- [ ] 5.1 Create a dedicated **"Taty Bot"** user in Chatwoot and use ITS access token as the
      bridge's `CHATWOOT_API_TOKEN`. Without this, bot and human replies are indistinguishable in
      Chatwoot's database (`sender_id` is identical) and the October
      keep-or-migrate decision has no data behind it.
- [ ] 5.2 Approve applying migration `0036` to Supabase.
- [ ] 5.3 Set `WHATSAPP_APP_SECRET` + `WHATSAPP_WEBHOOK_VERIFY_TOKEN` in Railway (inherited gate
      from `taty-channel-consolidation` — the receiver rejects everything until they exist).

## 6. Verify

- [ ] 6.1 `RUN_TESTS=1 bash init.sh` green.
- [ ] 6.2 Local end-to-end: post a signed synthetic Meta payload at the backend → confirm the row
      lands → run the poller → confirm the conversation appears in Chatwoot.
- [ ] 6.3 Durability drill: stop the bridge, post 5 signed events, restart it → all 5 appear in
      Chatwoot, none duplicated.
- [ ] 6.4 Duplicate drill: post the same event 3× → one row, one Chatwoot message.

## 7. Stage 11 — Deploy to Production (MANDATORY)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

- [ ] 7.1 git commit + push to `main`
- [ ] 7.2 Railway deploy active and healthy (`GET /api/v1/health` → 200)
- [ ] 7.3 Confirm the inbox health endpoint reports a real backlog figure in production
- [ ] 7.4 Create report: `openspec/changes/whatsapp-durable-inbox/reports/YYYY-MM-DD-deployment.md`

## 8. Archive

- [ ] 8.1 Sync the capability into `openspec/specs/` and archive (`git mv` for the archive move).
