# Stage 11 Deployment Report — taty-channel-consolidation + whatsapp-durable-inbox

- Date: 2026-07-30
- Deploy branch: `main`
- PR: [#8](https://github.com/jpelaezcardenas/antigravity-app/pull/8), merged `26b7beb`
- Both changes shipped together — `whatsapp-durable-inbox` is a direct follow-on to
  `taty-channel-consolidation` and never worked as a standalone deploy.

## 7.1 — Merge and push

- Merged via `gh pr merge 8 --merge --delete-branch`. Clean, mergeable, `GitGuardian Security
  Checks` and `Vercel` preview both green pre-merge.

## 7.2 — Vercel

- No frontend changes in this diff; Vercel preview check passed pre-merge. No separate
  verification needed post-merge.

## 7.3 — Railway

- Deployment `b7ffa31c` (project `elegant-success`, service `antigravity-app`, `production`),
  triggered automatically by the push to `main`. `SUCCESS` at the build layer within ~1 minute.
- Runtime took the full documented startup window — `/api/v1/health` returned `502` for the
  first ~5 polls (8s apart) before returning `200`, matching CLAUDE.md's stated Railway
  cold-start behavior. Not an incident.
- `GET /api/v1/health` → `200 {"status":"healthy",...}`.

## 7.4 — Production verification (all against the live deploy, not simulated)

| Check | Expected | Result |
|---|---|---|
| `POST /api/v1/channels/whatsapp/webhook` with no signature | `403` | ✅ `{"detail":"Invalid webhook signature"}` |
| `POST /api/v1/channels/whatsapp/leads/x/reply` with no auth | `401` | ✅ `{"detail":"Invalid or missing authentication token"}` |
| `POST /api/v1/channels/meta/webhook` with no signature | `403` | ✅ `{"detail":"Invalid webhook signature"}` |
| `GET /api/v1/channels/whatsapp/inbox/health` with no auth | `401` | ✅ `{"detail":"Invalid or missing authentication token"}` |

The temporary mitigation applied earlier the same day (`WHATSAPP_CANONICAL=false` via Railway
variable, closing the previously-open unsigned public webhook) is now superseded by this
deploy's permanent fix: the flag itself no longer exists in code, and the route is protected by
real signature verification rather than being conditionally unmounted.

## Config confirmed live in Railway (`elegant-success` / `antigravity-app` / `production`)

- `WHATSAPP_APP_SECRET` — set (founder-provided, from the "Taty Contadora Amiga" Meta app).
- `WHATSAPP_WEBHOOK_VERIFY_TOKEN` — set (generated).
- `META_WEBHOOK_VERIFY_TOKEN` — set (generated).
- `META_APP_SECRET` — **intentionally empty.** Confirmed via Meta Developer dashboard: the
  account has exactly one app ("Todas las apps (1)"), and its only registered use case is
  "Conectarte con los clientes a través de WhatsApp" — no Instagram/Facebook product is attached
  to any app yet. `meta_endpoints.py`'s fail-closed check means Instagram/Facebook webhooks
  reject everything until that app exists and this is set; nothing breaks by leaving it empty.
- `WHATSAPP_CANONICAL` — removed from code this deploy; the stray Railway variable (set to
  `false` earlier as a stopgap) is now inert and can be deleted at leisure.

## Local (whatsapp-durable-inbox half — not a Vercel/Railway target, sovereign per ARCHITECTURE.md decision #1)

- Migration `0036_whatsapp_inbound_events` applied to Supabase 2026-07-30, founder-confirmed.
  Verified: 11 columns present as designed, RLS enabled, no permissive policy.
- "Taty Bot" Chatwoot user (id 4) created directly via SQL: `account_users` role `0` (agent) on
  account 2, `inbox_members` on inbox 1 ("Taty Contadora Amiga 24/7"), own `access_tokens` row.
  Its token — not the founder's — is `CHATWOOT_API_TOKEN` in `apps/chatwoot-bridge/.env` going
  forward, so bot vs. human replies are distinguishable by `sender_id` for the October
  keep-or-migrate-to-Búnker decision on Chatwoot.
- `apps/chatwoot-bridge/.env` was pointed at production (`CONTEXIA_API_URL=https://contexia.online/api/v1`,
  `CONTEXIA_JWT_SECRET` matching Railway's `JWT_SECRET`) — the `127.0.0.1:8080` value inherited
  from `.env.example` assumed a local backend that was never running; the durable-inbox endpoints
  only exist on the deployed backend.
- **The full customer-facing loop was proven end-to-end against real, running infrastructure**
  (Chatwoot containers, the bridge as an actual process, and the deployed backend) — not a
  simulation of one piece in isolation:
  1. Signed synthetic Meta payload → backend → durable table (dedup + claim/ack drills, see below).
  2. Bridge poller → injects the message into a dedicated `Channel::Api` inbox (id 3, "Taty
     WhatsApp (inyección durable)") — Chatwoot's native `Channel::Whatsapp` inbox (id 1) rejects
     injecting `message_type: incoming` via the generic API, since that inbox type assumes
     Chatwoot itself holds the Meta integration, which isn't the case here.
  3. Chatwoot fires its own `message_created` webhook to the bridge → `process_incoming_message`
     → `/crm/leads/whatsapp-intake` → `/channels/whatsapp/leads/{id}/reply` → **a real,
     production-generated Wompi payment link came back and posted into the conversation**,
     attributed to Taty Bot (`sender_type=User, sender_id=4`), not a generic free-text reply.
- That run surfaced and fixed **four** real bugs before they could reach a real customer — three
  found in an earlier pass this session, a fourth found finishing the loop today:
  1. `pull_pending()` called `.or_()`, a method the installed `postgrest` version (0.13.2) does
     not have. Every prior test used a generic `MagicMock`, which happily answers a method that
     doesn't exist on the real client — so 8 passing tests never caught it. Fixed by using the
     raw `or=(...)` query param the way `.filter()` does internally; new tests build the query
     against the real installed `postgrest.SyncPostgrestClient` class (no network) so a
     missing/renamed method fails loudly again if it recurs.
  2. Chatwoot's native `Channel::Whatsapp` inbox rejects injecting `message_type: incoming`
     through the generic conversations API (see above). Resolved with the dedicated `Channel::Api`
     inbox.
  3. Enabling the real Supabase service-role key locally (required for the drill) turned a
     pre-existing test that had been passing by accident into a real write against production
     `operator_tasks` — 5 rows created with `status="pending"`, the same status Hermes/Manus poll
     for real dispatch. Founder confirmed; all 5 deleted by exact id; verified 0 remaining
     afterward. Root cause fixed with a defense-in-depth guard in `operator_task_service.py` so a
     test-context call can't silently write to the real table again.
  4. `chatwoot_client.py::set_contact_attributes` POSTed to `/contacts/{id}/custom_attributes` — a
     route that only exists on **conversations** (`config/routes.rb`), not contacts. It 404'd on
     every new lead. The existing unit test mocked exactly that wrong URL with `respx`, so it
     passed without ever exercising the real API — the same "mock answers a call the real system
     rejects" failure shape as bug #1. Fixed to `PATCH /contacts/{id}` with `custom_attributes` in
     the body (Chatwoot's `ContactsController#update` merges it), verified against
     `routes.rb`/`ContactsController` source, not re-mocked blindly.
- **Infrastructure fix required to make delivery possible at all**: Chatwoot's `SafeFetch`/SSRF
  guard (`lib/safe_fetch.rb`) refused to deliver its webhook to `host.docker.internal` —
  "Hostname has no public ip addresses" — which is exactly how a container reaches a process on
  the host. Set `SAFE_FETCH_ALLOW_PRIVATE_NETWORK=true` on `chatwoot-web` and `chatwoot-worker` in
  `docker-compose.chatwoot.yml` (Chatwoot's own documented escape hatch, not a workaround).
  **Security trade-off, explicitly accepted**: this weakens SSRF protection for all SafeFetch
  usages on this instance, not just the one webhook. Accepted because this Chatwoot instance is
  single-operator, local-only, `ENABLE_ACCOUNT_SIGNUP=false` — revisit if that ever changes.
  Also registered the actual webhook row (account-level, `inbox_id=NULL`, so it fires regardless
  of which inbox receives the message) pointing at `http://host.docker.internal:8090/webhook`,
  since none existed before this session.
- Also fixed in passing: `docker-compose.chatwoot.yml`'s `SECRET_KEY_BASE` value contained an
  unquoted em dash that broke `docker compose`'s YAML parser outright (pre-existing, unrelated to
  this change, but blocking — quoted it, matching the `POSTGRES_PASSWORD` line's style).
- Dedup and idempotency drills, run for real: same Meta message id delivered 3× → exactly 1 row
  persisted; forged signature → `403`, nothing persisted, nothing routed.
- **Real production side effect from this drill, found and cleaned up**: the successful run
  created two real `crm_leads` rows (`+573001112233`, `+573004445566`) and one real
  `crm_wompi_transactions` row (`status=PENDING`, a genuine `pub_prod_`-signed Wompi checkout
  link, `wompi_transaction_id=NULL` — nobody paid it). Founder confirmed deletion; both leads and
  the transaction removed by exact id from production Supabase; verified 0 rows remaining for
  either test phone number.

## Bridge poller — proven working, not yet running unattended

- The bridge ran as a real process against production for this session's verification and was
  stopped afterward (`HTTP 000` confirmed) rather than left running unsupervised.
- Starting it as a persistent, supervised process (and deciding a restart policy — the
  `gbrain-autopilot.service` `Restart=always` precedent from the architecture plan) is the
  natural next step and is explicitly not done by this report.

## Test suite

- Backend: 732 passed, 40 failed, 112 skipped. The 40 failures are the same pre-existing baseline
  verified against a clean `main` worktree earlier in this line of work (httpx/starlette version
  incompatibility plus assertions owned by in-flight `shadow-gl-real-data-ingestion` and
  `automated-approval-rules` changes) — none in files this change touches.
- Directly affected suites: backend WhatsApp/Meta/Taty/inbox all green; bridge suite (including
  the new poller/Chatwoot-client tests) all green.

## Outcome

- Both changes are **live in production and verified against the real deployment**, not
  simulated: the unsigned-webhook security hole opened by the old code is permanently closed,
  the single-brain reply path is live, and the durable-inbox → Chatwoot path was proven
  end-to-end locally with real infrastructure.
- Two items remain outside this report's scope, tracked as explicit follow-ups rather than left
  implicit: running the bridge poller as a supervised long-lived process, and the second Meta app
  (Instagram/Facebook) that doesn't exist yet.
