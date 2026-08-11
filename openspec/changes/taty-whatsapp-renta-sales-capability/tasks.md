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

- [ ] 4.1 Write failing tests: a WhatsApp-channel call into `TatyAgentService` accepts history +
  persona fields + CRM stage + offer context, and resolves to Cliente Cero's tenant.
- [ ] 4.2 Add the WhatsApp calling convention to `services/taty_service.py` (design.md Decision 3 —
  Cliente Cero resolution, no new tenant-resolution branch needed).
- [ ] 4.3 In `taty_lead_router.py`, change the `unknown`-intent branch (and optionally
  `sales_interest`/`payment_confirmation`'s conversational framing, per design.md Decision 2 — CRM
  and Wompi side effects stay exactly as they are) to call the new `TatyAgentService` convention
  instead of `_classify_fiscal_question`/`_synthesize_kb_reply`. Remove `STATIC_UNKNOWN_REPLY` and
  `KB_FALLBACK_REPLY` only once the replacement path is verified working (keep them as the
  exception-path fallback text, per the delta spec's "graceful fallback" scenario).
- [ ] 4.4 Extend `POST /leads/{lead_id}/reply` (`whatsapp_endpoints.py`) to accept recent
  conversation history in the payload (bridge already tracks `MAX_HISTORY=10`).
- [ ] 4.5 Unit tests: the four scenarios in the `taty-whatsapp-sales-router` delta spec (grounded
  reply, graceful no-KB fallback, conversational non-fiscal reply, service-failure fallback) plus
  the three in `taty-fiscal-assistant`'s new requirements.
- [ ] 4.6 Manual verification against the test inbox (Chatwoot inbox `3`, still — do not cut over
  delivery yet): inject the same messages that produced the original bug report ("Hola ayudame",
  "Ok", "Xomo lo contacto?", "Si, mi cedula es 98670827") and confirm none produces
  `STATIC_UNKNOWN_REPLY` or `KB_FALLBACK_REPLY` verbatim.
- [ ] 4.7 Confirm the Wompi HITL gate is untouched: trigger `sales_interest`, confirm a draft lands
  in `approval_queue` with `draft_type="wompi_payment_link"` and no link is sent automatically.

## 5. Chatwoot sole-sender delivery cutover (design.md Migration Plan step 5 — last, highest blast radius)

- [ ] 5.1 Add a `deliver: bool = True` flag to `POST /leads/{lead_id}/reply`; when `False`, skip
  `send_whatsapp_message` and return reply text only.
- [ ] 5.2 Update `apps/chatwoot-bridge/main.py` to call the endpoint with `deliver=False` and
  deliver the returned text itself via `chatwoot_client.send_reply`.
- [ ] 5.3 Update `apps/chatwoot-bridge/.env`: `CHATWOOT_WHATSAPP_INBOX_ID` from `3` to `1`.
- [ ] 5.4 Update `apps/chatwoot-bridge/.env.example` to include the three vars missing from it
  today (`CHATWOOT_WHATSAPP_INBOX_ID`, `INBOX_POLLER_ENABLED`, `INBOX_POLL_INTERVAL_SECONDS`).
- [ ] 5.5 Restart the bridge (Scheduled Task `ContexiaChatwootBridge`), confirm it comes back
  healthy against inbox `1`.
- [ ] 5.6 Confirm `bot_off` still pauses automated replies (delta spec scenario) — tag a test
  conversation, send a message, confirm no automated reply is generated.
- [ ] 5.7 **Real-phone verification** (the test that matters): send a WhatsApp message from a
  physical phone to +57 310 6229289. Confirm: (a) it appears in Chatwoot inbox `1`; (b) Taty's
  reply is conversational and arrives on the phone; (c) it arrives exactly once, not duplicated;
  (d) a human-typed reply from Chatwoot also reaches the phone.
- [ ] 5.8 If 5.7 fails in a way that risks live customer traffic, revert 5.1-5.3 immediately
  (design.md Rollback: point `CHATWOOT_WHATSAPP_INBOX_ID` back to `3`, re-enable direct send) before
  investigating further.

## 6. Founder-owned Meta sustainability actions (tracked, not blocking Stage 1-5)

- [ ] 6.1 Add `/privacy`, `/terms`, `/data-deletion` rewrites to `vercel.json` (routes exist on
  Railway at `apps/backend/main.py:161,196,230` but 404 on `contexia.online` today — needed for
  Meta Business Verification). This one IS an engineering task.
- [ ] 6.2 FOUNDER: start Business Verification in Meta Business Manager (raises `TIER_250`).
- [ ] 6.3 FOUNDER: re-verify the display name (`code_verification_status` is `EXPIRED`).
- [ ] 6.4 FOUNDER: create `es_CO` message templates for >24h re-engagement (only `hello_world`/
  `en_US` exists today). Not blocking the inbound-first motion.

## 7. Manus handoff runbook

- [ ] 7.1 Create `docs/runbooks/taty-whatsapp-campaign.md`: `wa.me/573106229289` link convention
  with per-content UTM-style params for attribution; real limits (inbound effectively uncapped;
  250 business-initiated conversations/24h until 6.2 lands); what Taty can/cannot say (Entidad B
  limits); where leads land (Chatwoot inbox `1` + `crm_leads`); `bot_off` handover; the Wompi HITL
  gate; how to bring the local stack up (`docker compose -f docker-compose.chatwoot.yml up -d`,
  Scheduled Task `ContexiaChatwootBridge`).

## 8. Repo hygiene (found during investigation, low-risk, included per proposal.md Impact)

- [ ] 8.1 Delete untracked `app-admin/dashboard-assets/index-DblwMcm3.js` — confirmed
  byte-identical (via `git hash-object`) to the blob `surface-and-routing-standardization` deleted
  in `c3eba88`; `vercel.json:191` still routes to it.
- [ ] 8.2 Commit the uncommitted PID-guard fix already in the working tree for
  `docker-compose.chatwoot.yml` (stale-PID-file guard on the `chatwoot` service command).

## 9. Review and Update Existing Unit Tests (MANDATORY)

- [ ] 9.1 Update `apps/backend/tests/test_taty_lead_router.py` for the new routing behavior
  (reply generation delegated to `TatyAgentService`, static-string assertions removed/replaced).
- [ ] 9.2 Update/add tests for `secure_llm.py`'s new `profile_name` parameter.
- [ ] 9.3 Add tests for the KB migration's new RPC overload and the `deliver` flag on
  `whatsapp_endpoints.py`.
- [ ] 9.4 Confirm `test_model_selector_cloud_only.py`'s pre-existing failing assertion (found live
  2026-08-11: asserts `not hasattr(LLMProvider, 'OLLAMA')`, which is false against the current
  `llm_engine.py`) — fix or explicitly document as a pre-existing, unrelated failure, do not leave
  it unexplained in the test report.

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
