## 0. Setup: Create Feature Branch (MANDATORY - FIRST STEP)

- [x] 0.1 Created `feature/taty-whatsapp-renta-sales-capability` from `main`.
- [x] 0.2 Verified via `git branch --show-current`.

## 1. Knowledge base schema repair (design.md Migration Plan step 1)

- [x] 1.1 Added `TestPgvectorSchemaMatchesRetrieveSimilar` to `tests/test_kb_seeding.py`, gated by
  `RUN_KB_PGVECTOR=1` (matching the file's existing convention). Confirmed it reproduced the real
  failure before the fix (RLS `42501` on seed; would have been an RPC-signature error pre-migration).
- [x] 1.2 Migration numbering corrected: the actual latest local file was `0037` (not `0035` as
  first assumed — `apps/backend/migrations/` and `apps/backend/supabase/migrations/` are two
  parallel directories; `migrations/` numbered files are the live convention, confirmed against
  Supabase's own `list_migrations` history). Wrote
  `apps/backend/migrations/0038_knowledge_chunks_client_id.sql`. Also discovered
  `20260527_knowledge_chunks.sql` (the file that originally defined the table) was itself never
  actually applied as written — its header says "apply manually... app works without it" — so what
  was live before this migration was a materially different, simpler schema. 0038 reconciles that
  divergence, additively.
- [x] 1.3 Applied via `mcp__supabase__apply_migration` (name matches filename convention). Verified
  live: `client_id`/`source` columns present with correct defaults; both RPC overloads
  (`p_client_id`-keyed and `match_threshold`-keyed) coexist in `pg_proc`.
- [x] 1.4 Re-ran 1.1's tests — pass.
- [x] 1.5 Confirmed via `pg_proc` query — both overloads present, pre-existing one untouched.
- [x] 1.6 **Found and fixed a second, deeper bug during 1.1's test**: `kb_seeding_service.py`
  built its own Supabase client from `settings.SUPABASE_KEY` (anon role). Live RLS on
  `knowledge_chunks`: SELECT granted only to `authenticated`, INSERT only to `service_role`;
  `match_knowledge_chunks` is `SECURITY INVOKER` so RLS applies through the RPC too. An anon
  client would have hard-failed on every seed AND silently returned zero rows on every read
  forever (RLS filters SELECT rows rather than erroring) — reproducing the exact original bug
  even after the schema fix. Repointed to the shared `core.supabase_client.get_service_supabase()`
  (the codebase's established service-role accessor, per migration `0037`'s own precedent).
  Verified: seed + retrieve round-trip test passes against live Supabase; DB left clean
  (`select count(*) from knowledge_chunks where client_id='test-taty-whatsapp-renta-sales-capability'` = 0
  after the test's cleanup).

## 2. Renta-persona-natural KB content

- [x] 2.1 Drafted `apps/backend/kb/renta_natural_chunks.json` (5 chunks): Art. 592 threshold
  ($69.718.600 = 1.400 UVT × $49.799 AG2025, founder-confirmed, cross-checked against UVT 2025/2026
  values via web search), partial-but-honest plazos calendar (5 confirmed digit-pairs, explicit
  "don't invent the rest" instruction baked into the chunk itself), documentos requeridos (sourced
  from the actual `RUT_REQUEST_MESSAGE`/`EXTRACTOS_REQUEST_MESSAGE` strings already live in
  `taty_lead_router.py`, not invented), Entidad-B scope (sourced verbatim-paraphrased from
  `.antigravity/GROUND_TRUTH.md`). **Price was deliberately left out of this file** — see 2.1b.
  Also seeded the founder's own pre-curated `apps/backend/kb/dian_chunks_expanded.json` (79
  chunks, previously dead/unreferenced data) alongside it.
- [x] 2.1b **Pricing discrepancy found and resolved with the founder**: `crm_service.py`'s
  `RENTA_NATURAL_PRICE_CENTS = 8_900_000` ($89.000 COP) is a single fixed price, confirmed against
  all 7 real `crm_wompi_transactions` rows (100% consistent at $89.000) — contradicting the
  founder's recollection of "~$300.000, varies by movements." Founder decided: real tiered pricing
  by asalariado vs. independiente/freelancer. **Blocked on the two actual price numbers** — not
  invented. See Stage 2.1c.
- [ ] 2.1c FOUNDER: provide the two tier prices (asalariado / independiente-freelancer). Once
  given: (a) add a KB chunk stating both tiers honestly, (b) this is a real code change beyond KB
  content — `RENTA_NATURAL_PRICE_CENTS`'s single-constant shape in `crm_service.py` must become
  tier-aware in `checkout_lead_payment`, which needs its own tasks under this stage once the
  numbers exist (not designed yet — genuinely new scope, not silently absorbed into "just a KB
  seed task"). Until this lands, Taty must not state a specific price to a WhatsApp lead.
- [x] 2.2 Seeded via direct `seed_knowledge_base("__global__", chunks)` calls (matches the
  existing `seed-dian` CLI hook's own pattern) — not yet via the HTTP endpoint (that's Stage 11's
  curl verification, separate).
- [x] 2.3 **Found and fixed two additional live bugs while seeding, beyond the two already known**:
  (a) `OPENAI_API_KEY` (the primary embedding provider) has zero credits in production
  (`insufficient_quota`/`credit_balance_exhausted`) — a real, currently-live production issue, not
  caused by this change. FOUNDER ACTION: add credits, or accept Gemini as primary until resolved.
  (b) The Gemini fallback was dead code in every environment, including production:
  `google-generativeai` was never in `requirements.txt` (added now), and the hardcoded model
  `models/embedding-001` no longer exists (404 — retired). Fixed to `models/gemini-embedding-001`
  with `output_dimensionality=1536` pinned to match the schema (the model defaults to 3072 dims).
  Verified: `count(*) = 84`, `count(embedding) = 84` — zero orphaned rows.
- [x] 2.4 `retrieve_similar("te toca declarar renta", "__global__", top_k=3)` — the literal bug-report
  question — returns 3 relevant chunks (similarity 0.72/0.70/0.69): "qué es declarar renta persona
  natural", "plazos 2026", "Art. 592 tope". The retrieval path Taty will actually use now works
  end-to-end against live production Supabase.

## 3. Provider chain repointing (design.md Migration Plan step 3)

- [x] 3.1 **SUPERSEDED, see design.md "Correction found during implementation"**: originally
  planned to add `profile_name` to `secure_llm.get_anonymized_ai_response`. Found while starting
  this stage that `TatyAgentService.ask()` doesn't use `secure_llm.py` at all — it has its own
  established profile-aware call pattern. Stage 4 deletes `taty_lead_router`'s only two callers of
  `get_anonymized_ai_response` (the ones that would have needed a profile) and replaces them with
  a `TatyAgentService` call. `secure_llm.py` is not touched by this change.
- [x] 3.2 **SUPERSEDED** — same reason as 3.1. No code change needed here.
- [x] 3.3 A/B'd `openai/gpt-oss-120b` vs `qwen/qwen3.6-27b` (both via Groq) against the 12 real
  messages in `whatsapp_inbound_events`, using Taty's actual system prompt
  (`taty_service.py::_build_system_prompt`). **DeepSeek V4-Flash could not be tested — no
  `DEEPSEEK_API_KEY` exists anywhere (not in Railway, not locally); deferred, see 3.4.**
  - `qwen3.6-27b` **disqualified**: it is a reasoning model whose API response surfaces its
    `<think>...</think>` chain-of-thought as `content` — every one of the 12 test calls returned
    only English internal reasoning, never a final Spanish answer, even at 200 output tokens.
  - `gpt-oss-120b` is also a reasoning model, but at low `max_tokens` (200-800, my initial test
    budget) its hidden reasoning consumed the whole budget before any visible content — 2/12
    outputs came back empty. Confirmed this is an artifact of my test harness, not of production
    config: `TatyAgentService` already calls with `max_tokens=2000` (`taty_service.py:174`); at
    that budget both previously-empty messages completed with full, fluent, correctly-toned
    Spanish responses (one `finish_reason=stop`, fully complete).
  - **Winner: `openai/gpt-oss-120b`**, conditional on 2000-token budgets (already true) and — this
    is the important part — **conditional on KB grounding actually being wired in Stage 4**: the
    ungrounded A/B responses **hallucinated dangerous fiscal figures with full confidence** —
    stated "1.400.607 UVT" as the ingresos-brutos threshold (the real figure is 1.400 UVT, a
    1000×  error), a stale/wrong UVT value ($42.562), and a **fabricated contact email and phone
    number that don't exist**. This isn't specific to this model — any ungrounded LLM will do
    this. It confirms the `taty-fiscal-assistant` delta spec's "never invent a figure it can't
    trace to retrieved content" requirement is safety-critical, not optional polish, and Stage 4
    must not ship without it actually wired end-to-end.
- [ ] 3.4 **Deferred, not blocking**: add a DeepSeek client to `agents/llm_engine.py` once
  `DEEPSEEK_API_KEY` exists. Until then, the `taty-v1` fallback chain uses only providers with
  real credentials (Groq primary, Gemini fallback — `GEMINI_API_KEY` confirmed present).
- [x] 3.5 Updated `PROFILE_CONFIGS["taty-v1"]`: `primary` = `GROQ` (model repointed to
  `openai/gpt-oss-120b`), `fallback_chain` = `[GROQ, GEMINI, OPENROUTER]`. Removed GLM and the
  implicit `llama-2-7b-chat`/OpenRouter-Free default from this profile's chain specifically — no
  other profile's chain touched.
- [x] 3.6/3.7 **Regression gate — Telegram + PWA**: called `TatyAgentService.ask()` directly
  (the exact shared function both channels invoke — `telegram_endpoints.py:181`,
  `taty_endpoints.py:181/246`) with `channel="telegram"` and `channel="dashboard"` against Cliente
  Cero's real tenant. Both produced complete, well-formed, correctly-toned Spanish answers,
  `error_code: None`, confidence 0.6. No crash, no regression in structure/behavior from the
  profile repoint.
  - **Also independently reproduced the same hallucination risk found in 3.3's A/B**, this time
    through the real production call path, not a synthetic test: the "¿Qué es el UVT?" answer
    stated "UVT 2024 = $42.562" (stale/wrong) and fabricated a contact email + phone number.
    Traced the cause: `_retrieve_pgvector` hit a transient Gemini rate-limit during this test and
    silently fell back to the **in-memory KB store**, which is a **separate, out-of-sync copy** —
    `ensure_dian_loaded()` (`taty_service.py:33`) only ever loads the original 48-chunk
    `dian_chunks.json` into memory; it never sees the 84 chunks now seeded into pgvector (79
    curated + 5 new renta-natural chunks with the correct UVT/threshold figures). **This is a
    real, structural gap, not a one-off**: any pgvector hiccup — Gemini rate limit, transient
    Supabase error, anything caught by `_retrieve_pgvector`'s broad `except` — silently degrades
    ALL of Taty's fiscal answers (not just WhatsApp) to a smaller, staler, unsynced fallback KB.
    Not fixed here (real scope, deserves its own design decision on whether the memory fallback
    should exist at all vs. fail loudly) — flagged for the founder and for Stage 7's runbook.
- [x] 3.8 Cleared to proceed to Stage 4.

**Operational note, not a task**: while committing this stage, discovered another session
(likely Manus or a parallel Claude Code session, sharing this same local checkout) committed
directly onto the checked-out `feature/taty-whatsapp-renta-sales-capability` branch and fast-
forward-merged it into `main` — an unrelated frontend commit ("Update WhatsApp number..."). No
data lost (fast-forward is non-destructive), but `main` now carries this change's in-progress work
mixed with that commit. Founder decision: continue committing locally on `main`, but **do not
`git push` until the entire change (through Stage 14) is complete and verified** — avoids
publishing partial work either session didn't intend to ship yet.

## 4. Route WhatsApp through TatyAgentService (design.md Migration Plan step 4)

- [x] 4.1 Added `tests/test_taty_service_whatsapp_channel.py` (12 tests, TDD-first): `_build_prompt`
  accepts `conversation_history` (no-op when omitted — regression-safe for Telegram/PWA, byte-for-
  byte identical whitespace verified by hand); `_build_system_prompt` accepts `lead_context`
  (stage, persona, offer/documents, price-non-invention, and — added mid-stage, see 4.6 —
  contact-info-non-invention).
- [x] 4.2 Added the WhatsApp calling convention to `services/taty_service.py`: `ask()` gained
  `conversation_history`/`lead_context` params, threaded into `_build_prompt`/`_build_system_prompt`.
  Cliente Cero resolution reuses the existing `core.tenant_context.resolve_cliente_cero_tenant_id`
  helper — no new resolution branch (design.md Decision 3).
- [x] 4.3 Rewrote `taty_lead_router.py`'s `unknown`-intent branch to call
  `get_taty_service().ask(channel="whatsapp", ...)` instead of the retired
  `_classify_fiscal_question`/`_synthesize_kb_reply` (both deleted — confirmed no other caller
  anywhere in the codebase before removing). `sales_interest`/`payment_confirmation` untouched,
  by design — their CRM/Wompi side effects and static replies are unchanged. `STATIC_UNKNOWN_REPLY`
  removed entirely (Taty now handles conversational messages herself); `KB_FALLBACK_REPLY` kept as
  the sole last-resort fallback for tenant-unresolved or `ask()`-raises/errors.
- [x] 4.4 `POST /leads/{lead_id}/reply` (`whatsapp_endpoints.py`) now accepts an optional `history`
  field (`HistoryTurn` list), converted to plain dicts and passed through to `route_lead_message`.
- [x] 4.5 68/68 tests pass across `test_taty_service_whatsapp_channel.py` (new),
  `test_taty_lead_router.py` (rewrote the 3 test classes that covered the retired
  classify-then-synthesize flow into `TestBuildLeadContext` + `TestRouteLeadMessageUnknownRoutesToTaty`
  — 8 new tests covering exactly the delta spec's scenarios: Taty answer used verbatim, history
  passed through, this-turn persona changes visible before persistence, unresolved-tenant and
  ask()-error/exception graceful fallback), `test_taty_ask_tenant_scoping.py` and
  `test_taty_tenant_profiles.py` (unchanged, confirming no regression to the existing
  tenant-resolution contract).
- [x] 4.6 Manual verification with a real test lead (created via `find_or_create_lead`, cleaned up
  after) against the exact 4 original bug-report messages. **None produced the old static replies.**
  Found and fixed one more real issue during this check: the model fabricated a plausible-looking
  Contexia email/phone/website when asked "Xomo lo contacto?" — same hallucination class as the
  fiscal-figure risk from Stage 3's A/B, just for contact details instead of numbers. Added an
  unconditional never-invent-contact-details instruction to `_build_system_prompt` (mirrors the
  price-non-invention pattern; unlike price there's no "confirmed" source to gate on, so it's
  always present). Re-verified: no fabricated contact info in either affected message afterward.
  Minor, non-blocking cosmetic quirk noticed: the model sometimes cites its own system-prompt
  instructions as a "source" (e.g. "Política de contacto de Contexia... 【Developer instructions】")
  — doesn't invent data, just an odd citation style; not fixed here.
- [x] 4.7 Verified live with a real test lead: `sales_interest` still returns the static reply with
  no Wompi link in the text, and exactly one `approval_queue` row lands with
  `draft_type="wompi_payment_link"` — the HITL gate (commit `0839eda`) is untouched.

## 5. Chatwoot sole-sender delivery cutover (design.md Migration Plan step 5 — last, highest blast radius)

- [x] 5.1 Added `deliver: bool = True` to `POST /leads/{lead_id}/reply`; `False` skips
  `send_whatsapp_message` and returns reply text only. 24/24 `test_whatsapp_endpoints.py` pass.
- [x] 5.2 `apps/chatwoot-bridge/backend_client.py::taty_reply` now always sends `deliver: false` —
  `main.py::process_incoming_message` already called `chatwoot_client.send_reply` right after, no
  change needed there. 8/8 `test_backend_client.py` pass (new `TestTatyReply`).
- [x] **Sequencing correction found live**: switching the bridge's inbox + restarting it BEFORE
  the backend's `deliver` flag was deployed would have double-messaged a real customer (old
  deployed backend ignores the unknown field and sends directly; Chatwoot, now on the real inbox,
  also sends). Deployed 5.1-5.2 to Railway first (commit `671c1ed`, pushed and confirmed live —
  old deployment `b608d456` → `REMOVED`, new `2239d802` → `SUCCESS`), ahead of this change's own
  Stage 11, specifically so the local cutover below is safe. Founder-approved 2026-08-11.
- [x] 5.3 `apps/chatwoot-bridge/.env`: `CHATWOOT_WHATSAPP_INBOX_ID` `3` → `1`.
- [x] 5.4 `apps/chatwoot-bridge/.env.example`: added the three vars that were missing
  (`CHATWOOT_WHATSAPP_INBOX_ID`, `INBOX_POLLER_ENABLED`, `INBOX_POLL_INTERVAL_SECONDS`).
- [x] 5.5 Restarted the `ContexiaChatwootBridge` Scheduled Task (stop → start). Confirmed healthy:
  `GET http://localhost:8090/` → `{"status":"ok","service":"chatwoot-hermes-bridge",...}`.
- [x] 5.6 Verified via existing, unmodified, passing test coverage rather than a live injection
  against the real customer-facing inbox (safer — no risk of a stray test message reaching a real
  number): `tests/test_webhook_filter.py::test_bot_off_label_pauses_processing` — the bridge's own
  webhook handler checks the `bot_off` label before ever reaching `process_incoming_message`. 9/9
  pass, untouched by this change.
- [x] **Real operational bug found and fixed while attempting 5.7**: the founder's first real test
  message ("Hola" / "Renta" to +57 310 6229289, 2026-08-11 ~16:44) got a correct, conversational
  reply and reached the phone — proving Stages 1-4 work end-to-end against a real customer message
  — but investigation (Chatwoot's own Postgres: `conversations`/`messages` tables) showed it landed
  in **conversation id 3, inbox_id 3** (the old test/injection channel), not inbox `1`. Root cause:
  `Stop-ScheduledTask` / `Start-ScheduledTask` did NOT actually replace the running bridge process —
  `run_bridge.ps1`'s watchdog self-check (`if port 8090 already answers, exit 0 — no-op`) is
  designed for crash recovery, not a deliberate config-reload restart, and cannot tell a healthy
  *stale* process from a healthy *fresh* one. The uvicorn process from 9:15 AM that morning (hours
  before any Stage 5 edit) was still alive and serving, with the old `CHATWOOT_WHATSAPP_INBOX_ID=3`
  and pre-`deliver`-flag code loaded in memory the whole time — so what the founder actually
  verified was the OLD architecture (confirmed by the delivery path: the backend defaulted
  `deliver=True` since the stale bridge never sent the new field, and Meta got the message from
  the direct-send path exactly as it did before this change existed).
  **Fixed**: `Stop-Process -Id <pid> -Force` on the actual uvicorn process, confirmed port 8090
  went quiet, then `Start-ScheduledTask` — new process confirmed (new PID, creation time matching
  the restart) with a fresh log file. That log showed two transient, non-blocking issues on
  startup, both self-resolved within the same log (confirmed by the log's own later lines and a
  live re-check): a `502 Bad Gateway` on the first `/inbox/pending` poll (Railway's normal
  post-deploy warm-up window; the very next poll 5s later returned `200`) and an
  `httpx.LocalProtocolError: Illegal header value b'Bearer '` from `hermes_client`'s startup
  liveness probe (pre-existing, documented as inert in `main.py`'s own module docstring —
  `HERMES_API_KEY` is blank in this local setup, unrelated to the reply-generation path this
  change touches).
  **Operational gap flagged for the Stage 7 runbook, not fixed in code here** (real scope of its
  own): the watchdog cannot currently distinguish "needs a deliberate restart after a config
  change" from "already healthy" — the correct manual procedure (kill the actual PID, not just the
  scheduled task) needs to be documented so this doesn't silently repeat next time `.env` changes.
- [ ] 5.7 **Real-phone verification, retry (FOUNDER ACTION — the test that matters)**: now that the
  bridge is genuinely running fresh, send another WhatsApp message from a physical phone to
  **+57 310 6229289**. Confirm: (a) it appears in Chatwoot inbox `1` ("Taty Contadora Amiga
  24/7") — a NEW conversation there, not conversation 3 again; (b) Taty's reply is conversational
  and arrives on the phone; (c) it arrives **exactly once**, not duplicated; (d) typing a reply
  directly in that Chatwoot conversation also reaches the phone (did NOT work before this change —
  inbox `3` had no Meta credentials to deliver a human's reply). **Known active condition to
  expect while testing**: Gemini's free embedding quota is exhausted right now (confirmed live,
  `429 ResourceExhausted`, from this session's own heavy testing volume today) — retrieval may
  silently degrade to the smaller, unsynced in-memory KB (see design.md's "Second correction"), so
  a reply might occasionally read as more generic/less grounded than the answers seen earlier
  today until the quota resets or `OPENAI_API_KEY` is credited (tasks.md 2.3).
- [ ] 5.8 If 5.7 fails in a way that risks live customer traffic: revert by setting
  `CHATWOOT_WHATSAPP_INBOX_ID` back to `3` in `apps/chatwoot-bridge/.env` and — critically, per the
  bug just found — kill the actual bridge process by PID before restarting the scheduled task, not
  just `Stop-ScheduledTask`. This alone is sufficient (the backend's `deliver` flag defaults to
  `True`, so reverting the bridge's config immediately restores the exact pre-Stage-5 behavior
  without needing a second Railway deploy).

## 6. Founder-owned Meta sustainability actions (tracked, not blocking Stage 1-5)

- [x] 6.1 Added `/privacy`, `/terms`, `/data-deletion` rewrites to `vercel.json`, proxying to the
  same Railway backend as `/api/v1/:path*`. Validated JSON syntax; deploys with the next Vercel
  push (Stage 14).
- [ ] 6.2 FOUNDER: start Business Verification in Meta Business Manager (raises `TIER_250`).
- [ ] 6.3 FOUNDER: re-verify the display name (`code_verification_status` is `EXPIRED`).
- [ ] 6.4 FOUNDER: create `es_CO` message templates for >24h re-engagement (only `hello_world`/
  `en_US` exists today). Not blocking the inbound-first motion.

## 7. Manus handoff runbook

- [x] 7.1 Created `docs/runbooks/taty-whatsapp-campaign.md`: link + attribution convention, real
  limits, what Taty can/cannot say (price + contact-info non-invention, Entidad B), where leads
  land, `bot_off` handover, the Wompi HITL gate, KB health check (the in-memory/pgvector desync
  risk from Stage 3/4), and how to bring the stack up — including the stale-process restart
  gotcha found live in Stage 5, so it doesn't silently repeat.

## 8. Repo hygiene (found during investigation, low-risk, included per proposal.md Impact)

- [x] 8.1 Re-verified live (hash still matched) then deleted untracked
  `app-admin/dashboard-assets/index-DblwMcm3.js` — was byte-identical (via `git hash-object`) to
  the blob `surface-and-routing-standardization` deleted in `c3eba88`; `vercel.json:191` still
  routes to it.
- [x] 8.2 Already committed — this session's very first commit (`406f2cb`) staged
  `docker-compose.chatwoot.yml` along with the OpenSpec archive/open work and picked up the
  pre-existing uncommitted PID-guard fix in the process. Confirmed via `git show 406f2cb --stat`.

## 9. Review and Update Existing Unit Tests (MANDATORY)

- [x] 9.1 Done in Stage 4: `test_taty_lead_router.py` rewritten for the new routing behavior.
- [x] 9.2 **N/A** — superseded per Stage 3's design.md correction: `secure_llm.py` was never
  touched, so it never needed a `profile_name` parameter.
- [x] 9.3 Done: KB migration RPC overload tested in Stage 1
  (`TestPgvectorSchemaMatchesRetrieveSimilar`), `deliver` flag tested in Stage 5
  (`test_whatsapp_endpoints.py`, `test_backend_client.py`).
- [x] 9.4 **Fixed, not just documented**: removed the dead `LLMProvider.OLLAMA` enum member
  (`llm_engine.py:46`) — confirmed via repo-wide grep it had exactly one reference anywhere, inside
  this failing test's own assertion string. Also corrected the module docstring's stale failover
  order (still said "Ollama → OpenRouter Free → ..."; the real chain never included Ollama). All
  27 tests across `test_model_selector_cloud_only.py` + `test_llm_engine.py` pass now (1 skip,
  a real-call E2E test gated behind its own flag).

## 10. Run Unit Tests and Verify Database State (MANDATORY)

- [ ] 10.1 Capture pre-test baseline: `knowledge_chunks` row count, `crm_leads` count (9 as of
  2026-08-11), `whatsapp_inbound_events` count (12 as of 2026-08-11).
- [ ] 10.2 Run targeted tests: `pytest apps/backend/tests/test_taty_lead_router.py
  apps/backend/tests/test_whatsapp_endpoints.py -v`.
- [ ] 10.3 Run `RUN_TESTS=1 bash init.sh` (full backend suite) — confirm green, or that any failure
  is on the same pre-existing list `pwa-tenant-aware-screens` recorded (40 pre-existing failures),
  not a new regression.
- [ ] 10.4 Verify post-test DB state matches baseline (test data cleaned up); restore if not.
- [ ] 10.5 Create report `openspec/changes/taty-whatsapp-renta-sales-capability/reports/YYYY-MM-DD-step-10-unit-test-and-db-verification.md`.

## 11. Manual Endpoint Testing with curl (MANDATORY - AGENT MUST EXECUTE)

- [ ] 11.1 `curl -X POST .../api/v1/kb/search` against the seeded renta content, verify non-empty
  results.
- [ ] 11.2 `curl -X POST .../api/v1/channels/whatsapp/leads/{id}/reply` with `deliver=false` against
  a test lead, verify text-only response, no outbound send attempted.
- [ ] 11.3 Test error cases: malformed payload, non-existent `lead_id`.
- [ ] 11.4 Document all commands/responses in the same reports folder.

## 12. E2E Testing with Playwright MCP

- [ ] 12.1 **Not applicable** — this change has no frontend surface (per proposal.md Impact: "No
  frontend changes"). The real end-to-end verification is Stage 5's physical-phone test (5.7),
  documented there instead.

## 13. Update Technical Documentation (MANDATORY)

- [ ] 13.1 Update `ARCHITECTURE.md`'s Chatwoot + bridge row / Caja Real flow section if the
  delivery-path change affects anything documented there.
- [ ] 13.2 Update `AGENTES.md`'s Taty entry to reflect the WhatsApp channel now routing through
  `TatyAgentService` (currently describes Telegram + `/api/v1/agents` only).
- [ ] 13.3 Confirm `docs/runbooks/taty-whatsapp-campaign.md` (Stage 7) is complete and accurate as
  of the final implementation.

## 14. Stage 11: Deploy to Production (MANDATORY - CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker (no frontend change expected, verify unaffected)
- Backend URL: https://antigravity-app-production-175a.up.railway.app

- [ ] 14.1 Merge `feature/taty-whatsapp-renta-sales-capability` → main, push.
- [ ] 14.2 Set `DEEPSEEK_API_KEY` (and any other new env var from Stage 3) in Railway production.
- [ ] 14.3 Railway deploy green; `GET /api/v1/health` returns 200.
- [ ] 14.4 Vercel build green (rewrites from 6.1 live at `contexia.online/privacy` etc — 200, not
  404).
- [ ] 14.5 Production smoke test: repeat 5.7's real-phone test against production, not local Docker
  Chatwoot — confirm the full path (Meta → Railway → Chatwoot inbox `1` → Taty reply → delivered
  once) works against the deployed backend, not just local.
- [ ] 14.6 Create report: `openspec/changes/taty-whatsapp-renta-sales-capability/reports/YYYY-MM-DD-deployment.md`.

## 15. Close

- [ ] 15.1 `opsx:sync` the four delta specs (`taty-whatsapp-sales-router`, `taty-fiscal-assistant`,
  `taty-knowledge-base`, `chatwoot-whatsapp-delivery`) into main `openspec/specs/`.
- [ ] 15.2 `opsx:archive` this change.
- [ ] 15.3 Update `feature_list.json`: mark `taty-whatsapp-renta-sales-capability` `done`, set
  `active` to whatever comes next (or `null` if nothing is queued).
