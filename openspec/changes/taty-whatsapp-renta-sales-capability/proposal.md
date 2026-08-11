## Why

Taty's WhatsApp channel is live end-to-end (Meta → Railway webhook → Chatwoot poller → bridge →
`taty_lead_router`) but is stuck answering two fixed strings in a loop. Verified live 2026-08-11
against real inbound messages already sitting in `whatsapp_inbound_events`
("Hola ayudame", "Si, mi cedula es 98670827", "Ok", "Xomo lo contacto?"): the transport works — the
reply-generation brain does not.

Three concrete, verified root causes, not one:

1. **`route_lead_message` only reaches an LLM on the `unknown` intent branch** (`taty_lead_router.py:322-388`).
   `sales_interest` and `payment_confirmation` are fully static strings by design (this matches the
   currently-documented `taty-whatsapp-sales-router` spec) — but greetings, contact questions, and
   typo'd fiscal questions don't match any keyword, so they fall through to `unknown`, and today
   that branch's LLM call defaults through the provider chain's first entry: OpenRouter Free's
   `meta-llama/llama-2-7b-chat` (`llm_engine.py:124,563`). `get_anonymized_ai_response` has no
   `profile_name` parameter (`secure_llm.py:36-40`), so the `taty-v1`/GLM profile already defined
   in `PROFILE_CONFIGS` is unreachable from this path — it was built for a channel this router
   never calls into.
2. **The knowledge base is empty AND schema-mismatched**, not just unseeded. Live check
   (`knowledge_chunks`, Supabase `kpynymwghfwshvcvevxq`): 0 rows, and the table has no `client_id`
   column while `kb_seeding_service.retrieve_similar` calls `match_knowledge_chunks(query_embedding,
   p_client_id, match_count)` — a signature that doesn't exist. The RPC that does exist takes
   `(query_embedding, match_threshold, match_count)`. Seeding today would fail outright, not just
   return empty.
3. **WhatsApp is the only Taty channel that bypasses `TatyAgentService`.** Telegram
   (`telegram_endpoints.py:178`) and the PWA (`taty_endpoints.py:181,246`) both call
   `get_taty_service()` — one brain, one persona, the `taty-v1` profile, tenant-derived guardrails.
   `taty_lead_router.py` runs an entirely separate, parallel decision tree that never touches that
   service. Per the founder's explicit constraint: **Taty is one agent; selling declaración de
   renta must be a capability of that agent, not a second implementation of Taty.**

Separately, the delivery path duplicates messages once the correct Chatwoot inbox is used: the
backend calls `send_whatsapp_message` directly (`whatsapp_endpoints.py:150-154`) *and* the intended
inbox (`Taty Contadora Amiga 24/7`, id `1`, real Meta-linked `Channel::Whatsapp`) would also
deliver via Chatwoot's own credentials — today the bridge is pointed at inbox `3`
(`Channel::Api`, an injection-only test channel that cannot deliver to a real phone), which avoids
the collision by accident, not by design, and as a side effect means a human replying from Chatwoot
today never reaches the customer.

## What Changes

- **WhatsApp routes through `TatyAgentService`** (`services/taty_service.py`) instead of
  `taty_lead_router` generating reply text itself. Same profile (`taty-v1`), same persona, same
  Entidad B guardrails already enforced for Telegram/PWA. `taty_lead_router.py` keeps its
  well-scoped, already-spec'd responsibilities — lead find-or-create, intent-triggered CRM/Wompi
  side effects, persona-field persistence — as tools Taty's WhatsApp turn invokes, not as the thing
  that writes the reply text.
- **New sales-funnel capability on `TatyAgentService`**: when the caller is a WhatsApp lead, Taty
  gains context (lead stage, known persona fields, the renta-persona-natural offer: price, what's
  included, required documents) and can converse freely instead of falling through to either of the
  two static strings.
- **`taty-v1` profile's provider chain is repointed**: off `llama-2-7b-chat` / GLM 5.2, onto
  `groq/openai-gpt-oss-120b` primary with a DeepSeek/Gemini fallback chain (see design.md for the
  cost comparison that drove this — GLM 5.2 at list price is the most expensive option evaluated,
  not the cheapest). This change is shared by all three channels; Telegram and PWA regression
  coverage is mandatory before Stage 11 closes, not optional.
- **`knowledge_chunks` schema is repaired**: additive migration adds `client_id`/`source` columns
  and the `match_knowledge_chunks(query_embedding, p_client_id, match_count)` overload the code
  already expects, without touching the existing `match_threshold` overload or any other consumer.
  Seeded with a new renta-persona-natural-focused chunk set (confirmed figures only — no invented
  fiscal thresholds).
- **Chatwoot becomes the sole outbound sender** for the WhatsApp channel. The backend's
  `POST /leads/{id}/reply` gains a `deliver` flag; when called from the bridge it returns text only,
  and Chatwoot (now pointed at inbox `1`, the real Meta-linked inbox) delivers via its own
  credentials — which also means a human agent's reply typed in Chatwoot finally reaches the
  customer, which it does not today.
- **BREAKING**: the two static replies (`STATIC_UNKNOWN_REPLY`, `KB_FALLBACK_REPLY`) and their
  governing requirement in `taty-whatsapp-sales-router` are retired for the `unknown` branch —
  replaced by Taty's own graceful "let me get a human to help" fallback when the KB genuinely has
  nothing relevant, which is a behavior change to an already-spec'd requirement, not new scope.

## Non-goals

- Outbound/cold campaign sending, template messages, or anything requiring Meta Business
  Verification — out of scope for this change. The sales motion is inbound-first
  (`wa.me` links in content, customer opens the 24h service window); verification and template
  creation are founder-owned Meta-dashboard actions tracked separately, not engineering tasks here.
- `route_lead_document` (RUT/extractos intake) — confirmed dead code (no caller), real but
  pre-existing gap, not created by this change. Flagged, not fixed, here.
- Re-litigating the Wompi HITL gate (`taty-wompi-link-hitl-gate`) — its approval-queue mechanism is
  reused as-is. This change does not touch `_enqueue_wompi_link_approval` or `approve_draft`'s
  `wompi_payment_link` branch.
- Re-litigating WhatsApp ingress/signature verification (`taty-channel-consolidation`,
  `whatsapp-durable-inbox`) — this change builds on that transport, doesn't change it.
- Meta Business Verification, plantillas es_CO, `/privacy` `vercel.json` rewrite — founder-facing
  Meta/infra actions, tracked in this change's tasks as explicit founder items, not silently
  dropped.

## Capabilities

### New Capabilities
- `taty-knowledge-base`: the pgvector schema contract (`knowledge_chunks` columns, the
  `p_client_id`-keyed RPC overload) that `kb_seeding_service` requires to actually store and
  retrieve chunks, plus the renta-persona-natural seed content.
- `chatwoot-whatsapp-delivery`: the invariant that exactly one system (Chatwoot, via its own Meta
  credentials on the real inbox) delivers outbound WhatsApp messages for the Taty sales channel —
  the backend never double-sends, and a human's Chatwoot reply reaches the customer.

### Modified Capabilities
- `taty-whatsapp-sales-router`: the `unknown`-branch fallback requirement changes from
  "two static strings, KB-grounded synthesis in between" to "routes to `TatyAgentService`"; the
  "replies are sent back over WhatsApp" requirement changes from "always via
  `send_whatsapp_message`" to "via the configured delivery flag, defaulting to Chatwoot for the
  WhatsApp channel." `sales_interest`/`payment_confirmation`'s CRM/Wompi side effects are
  unchanged.
- `taty-fiscal-assistant`: `TatyAgentService` gains a WhatsApp-channel calling convention and a
  sales-funnel tool set (lead stage, persona fields, offer context). Its existing tenant-resolution
  contract (`resolve_request_tenant_scope`, Cliente-Cero-for-staging, never-leak-another-tenant) is
  unchanged — WhatsApp sales leads resolve to Cliente Cero's tenant (Contexia's own prospects, not
  yet a provisioned B2B client), the same path already used by Telegram.

## Impact

- **Backend**: `apps/backend/services/taty_lead_router.py` (loses reply-text generation, keeps
  tools), `apps/backend/services/taty_service.py` (gains WhatsApp calling convention + sales-funnel
  tools), `apps/backend/agents/secure_llm.py` (`profile_name` param), `apps/backend/agents/llm_engine.py`
  (`taty-v1` provider chain), `apps/backend/presentation/whatsapp_endpoints.py` (`deliver` flag,
  history in the reply payload), `apps/backend/supabase/migrations/` (new additive migration,
  numbered after the existing `0035`), `apps/backend/kb/renta_natural_chunks.json` (new).
- **Bridge**: `apps/chatwoot-bridge/.env` (inbox id `3` → `1`), `.env.example` (documented, it's
  missing three vars already live in the real `.env`).
- **No frontend changes.**
- **Docs**: new `docs/runbooks/taty-whatsapp-campaign.md` (none exists today for Chatwoot/WhatsApp
  operations); `vercel.json` gains rewrites for `/privacy`, `/terms`, `/data-deletion` (currently
  404 on `contexia.online`, needed for Meta Business Verification).
- **Repo hygiene found during investigation, included as low-risk cleanup**: untracked
  `app-admin/dashboard-assets/index-DblwMcm3.js` is byte-identical to the blob
  `surface-and-routing-standardization` deleted (`c3eba88`) and is still routed to by
  `vercel.json:191` — removed. Uncommitted PID-guard fix in `docker-compose.chatwoot.yml`
  committed.
