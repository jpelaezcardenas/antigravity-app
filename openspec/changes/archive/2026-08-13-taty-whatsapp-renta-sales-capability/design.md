## Context

Three independent pieces of Taty already exist and must converge into one, per the founder's
explicit constraint (2026-08-11 conversation): *"que esto no sea o que sea una función más de
Taty"* — this cannot produce a second Taty.

- **`TatyAgentService`** (`services/taty_service.py`) — the real brain. Telegram and the PWA both
  call `get_taty_service()`. Profile `taty-v1`, tenant-derived persona, `resolve_request_tenant_scope`
  for auth.
- **`taty_lead_router.py`** — a parallel, keyword-first decision tree that never touches
  `TatyAgentService`. It owns real, correct, already-spec'd side effects (lead CRM advance, Wompi
  HITL enqueue, persona-field persistence) but also generates reply *text* itself, via two raw
  `get_anonymized_ai_response` calls with no profile.
- **Hermes** (`~/.hermes/profiles/contexia/`) — runs the `contexia` profile, which `AGENTES.md`
  names as Taty's substrate for the TIER-2 "Conversational Operator" role. Confirmed: no separate
  `taty` Hermes profile exists; `contexia` is it.

The three layers (identity / channel / capability) model in `proposal.md`'s Why section is the
frame every decision below serves: identity (`TatyAgentService` + `taty-v1` + `contexia` profile)
does not change; WhatsApp joins as a channel; renta-persona-natural sales joins as a capability.

## Decisions

1. **WhatsApp calls `TatyAgentService`; `taty_lead_router` stops writing reply text.**
   *Alternative considered and rejected*: make `taty_lead_router`'s LLM calls profile-aware and
   call it a day — this was the first draft of this plan. Rejected because it produces exactly the
   outcome the founder ruled out: a second, WhatsApp-only Taty persona/prompt that can drift from
   Telegram/PWA's. Routing through the existing service is not more work — `taty_lead_router`
   already computes everything `TatyAgentService` needs (lead stage, persona fields); it becomes an
   input builder instead of a reply generator.

2. **`taty_lead_router`'s functions become tools, not gates.** Concretely: `_detect_persona_fields`,
   `advance_lead`, `_enqueue_wompi_link_approval`, `verify_wompi_transaction` keep their exact
   current implementations and call sites' semantics (this is a routing change, not a rewrite of
   correct code). What changes is that they run as side effects of a Taty turn rather than as
   branches that pre-empt one. The Wompi HITL gate (`taty-wompi-link-hitl-gate`) is untouched code —
   `_enqueue_wompi_link_approval` still does exactly what it does today; no automatic send is
   introduced anywhere in this change.

3. **WhatsApp sales leads resolve to Cliente Cero's tenant, not a new tenant concept.** A
   `crm_leads` row created by `CrmService.whatsapp_intake` belongs to Contexia's own sales pipeline
   — these are Contexia's prospects, not yet a provisioned B2B client with their own tenant. This is
   exactly the same resolution Telegram's staging identity already uses
   (`taty-fiscal-assistant` spec, "Staging identity falls back to Cliente Cero"). No new
   tenant-resolution branch is needed; `TatyAgentService` is called with Cliente Cero's tenant uuid
   for this channel, always — there is no "authenticated caller with unresolved tenant" case on
   this path, since WhatsApp leads are never an authenticated session.

4. **`taty-v1` profile change applies to all three channels, deliberately, not scoped to
   WhatsApp.** *Alternative considered*: give WhatsApp its own profile
   (`taty-whatsapp-v1`) to avoid any risk to Telegram/PWA. Rejected — that recreates the "two
   Tatys" problem one layer down (two provider chains for one agent identity is the same mistake
   as two prompts). One profile, one routing decision, verified on all three surfaces before
   Stage 11 closes (see tasks.md's regression requirement).

5. **Provider choice: Groq `openai/gpt-oss-120b` primary, DeepSeek V4-Flash fallback, GLM 5.2
   removed from the chain.** Cost comparison (2026-08 pricing, see proposal.md/plan for sources):
   GLM 5.2 at Z.ai list price ($1.40/$4.40 per M tokens) is the most expensive of every option
   evaluated — roughly 9× `gpt-oss-120b`'s $0.15/$0.60. GLM's cheap tier is a flat coding
   subscription, a different product that does not apply to API calls like Taty's. At Taty's actual
   message size (~300 tokens today, up to ~2,800 with a fuller sales persona), every evaluated
   model except GLM costs under $10/month at 1,000 msg/day — so the deciding factors are latency
   and Spanish-language quality, not price. *Mitigation for the quality unknown*: run the 12 real
   messages already sitting in `whatsapp_inbound_events` through the top 3 candidates
   (`gpt-oss-120b`, `qwen3.6-27b`, DeepSeek V4-Flash) as a manual A/B before locking the choice in
   `PROFILE_CONFIGS` — tasks.md Stage 2 includes this as a gating step, not a follow-up.

6. **Chatwoot becomes the sole outbound sender; the backend adds a `deliver` flag rather than
   deleting `send_whatsapp_message`.** *Alternative considered*: delete the direct-send call
   entirely. Rejected — `POST /leads/{id}/reply` may have callers other than the bridge (it's a
   general internal endpoint), and removing send capability from the backend entirely would break
   any path that doesn't go through Chatwoot. A boolean flag, defaulted per-caller, is strictly
   additive and reversible.

7. **KB schema fix is additive only.** New columns with a default (`client_id text not null default
   '__global__'`), a *new* RPC overload alongside the existing `match_threshold`-keyed one. Zero
   existing rows (`knowledge_chunks` is empty — verified live), so there is no backfill risk, but
   the additive shape means any other undiscovered caller of the old RPC signature keeps working
   regardless.

## Correction found during implementation (2026-08-11, Stage 3)

The original Stage 3 plan assumed `taty_lead_router.py` would keep calling
`agents.secure_llm.get_anonymized_ai_response` directly and just needed a `profile_name` parameter
threaded through it. Reading `services/taty_service.py::ask()` in full while starting Stage 3
showed this premise was wrong: `TatyAgentService.ask()` does **not** use `secure_llm.py` at all —
it has its own established pattern (`Anonymizer.mask()` directly, then
`get_llm_engine().get_ai_response_with_profile(profile_name=...)`, then `Anonymizer.unmask()`).
That is how it already correctly reaches the `taty-v1` profile for Telegram/PWA today.

Since Stage 4 deletes `taty_lead_router`'s two raw LLM calls (`_classify_fiscal_question`,
`_synthesize_kb_reply`) entirely and replaces them with a call into `TatyAgentService` — per
Decision 1, that was always the point — adding `profile_name` to `secure_llm.py` would fix a call
site that stops existing one stage later. **Dropped**: `secure_llm.py` is not touched by this
change. The WhatsApp channel reaches `taty-v1` for free once Stage 4 lands, through
`TatyAgentService`'s existing internal pattern — no new plumbing needed. Stage 3's real remaining
work is unchanged: the provider chain itself (`PROFILE_CONFIGS["taty-v1"]`) still points at
`llama-2-7b`/GLM regardless of which caller reaches it, and still needs repointing, A/B testing,
and Telegram/PWA regression coverage before Stage 4 can safely route WhatsApp through it.

## Second correction found during implementation (2026-08-11, Stage 3 regression testing)

While regression-testing `TatyAgentService.ask()` for Telegram/PWA (tasks.md 3.6/3.7), a transient
Gemini rate-limit made `_retrieve_pgvector` fall back to `_retrieve_memory` — and the answer that
came back stated a stale UVT figure and a fabricated contact number, reproducing 3.3's A/B
hallucination finding through the real production path. Root cause: **the in-memory KB fallback
is a separate, out-of-sync store**, not a cache of pgvector. `ensure_dian_loaded()`
(`taty_service.py:33`) loads only the original 48-chunk `dian_chunks.json` into memory at import
time; it has no knowledge of the 84 chunks (79 curated + 5 renta-natural, with the correct
figures) now seeded into pgvector by this change. Any pgvector hiccup — not specific to this
change, this is a pre-existing structural property of `kb_seeding_service.py` — silently degrades
every Taty fiscal answer, on every channel, to a smaller and staler knowledge base with no
signal to the caller that this happened. Not fixed in this change (real scope of its own: does
the memory fallback still make sense at all, versus failing loudly or lazily syncing from
pgvector); flagged in tasks.md Stage 3 and for the Stage 7 runbook.

## Risks / Trade-offs

- **[Risk] Changing the shared `taty-v1` profile chain for a WhatsApp fix could regress Telegram or
  the PWA.** This is the single largest risk in this change. → **Mitigation**: tasks.md makes
  Telegram (`@contexia_bot`) and PWA regression checks a hard gate before Stage 11, not a
  nice-to-have. If either regresses and can't be fixed quickly, the fallback is scoping the
  provider change to a WhatsApp-specific override the `TatyAgentService` call site passes
  explicitly, at the cost of the "one routing decision" property in Decision 4 — acceptable as a
  last resort, not a first move.
- **[Risk] KB seed content quality.** A renta-persona-natural chunk set with an invented or
  outdated figure would have Taty state it as fact to a paying prospect. → **Mitigation**: every
  chunk's fiscal figures must trace to a confirmed source before seeding; tasks.md requires this
  explicitly rather than leaving it to implementation-time judgment.
- **[Trade-off] Sales-funnel context is added to `TatyAgentService`'s prompt-building, growing its
  responsibility.** Accepted — the alternative (a parallel service) is exactly what this change
  exists to undo.
- **[Out of scope, flagged not fixed] `route_lead_document` has no caller** — inbound WhatsApp
  documents (RUT, extractos) are silently dropped today. Pre-existing, not introduced by this
  change; worth its own follow-up once the conversational path is stable.

## Migration Plan

1. **KB schema migration** first, alone — additive, zero rows at risk, unblocks seeding
   independently of any router change.
2. **Seed renta-persona-natural content**, verify retrieval works stand-alone (direct
   `retrieve_similar` call) before wiring it into a live conversation.
3. **`secure_llm.py` profile-parameter + `llm_engine.py` provider-chain change**, verified against
   Telegram and PWA *before* WhatsApp is touched at all — this isolates whether a regression came
   from the profile change or the routing change.
4. **`taty_lead_router` → `TatyAgentService` routing change**, with WhatsApp still pointed at the
   test inbox (`3`) — so a bad reply is only visible in test conversations, not live customer
   chats.
5. **Chatwoot delivery cutover** (`deliver` flag + inbox `1`) last, only once 1-4 are verified
   individually — this is the step that makes the channel live for a real customer.
6. **Rollback**: each step is independently revertible. Step 5 (inbox cutover) has the highest
   blast radius if wrong (a real customer gets no reply, or a duplicate) — revert by pointing the
   bridge's `CHATWOOT_WHATSAPP_INBOX_ID` back to `3` and re-enabling direct `send_whatsapp_message`,
   which restores exactly today's (safe, if unhelpful) behavior.
