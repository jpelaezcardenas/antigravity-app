## Context

Changes A/B built the CRM cockpit (B2B grid, B2C Kanban funnel). This change is unrelated to that
domain — it's the first piece of the agentic "Sell Machine" vision: an autonomous creative loop
that drafts marketing hooks, filters them against a brand rubric, and only surfaces survivors for
human approval. It runs entirely in-repo against simulated execution (no Meta/Wompi/WhatsApp
credentials needed) — later changes (F: Hermes→Manus bridge) will dispatch *approved* packages to
real execution.

Verified facts from research that shape this design:
- The existing Approval Queue's REST endpoint (`POST /api/v1/approval-queue/enqueue`) is hardcoded
  to a journal-entry request shape (`lines: [...]`) — it cannot accept an arbitrary payload without
  reshaping. But the underlying **service function**
  `ApprovalQueueService.enqueue_draft(draft_id, draft_type, journal_entry, memo)` accepts any dict
  as `journal_entry` (the field is misleadingly named but generically typed), and **skips the
  accounting Critic validation entirely for any `draft_type` not in `JOURNAL_ENTRY_DRAFT_TYPES =
  {"tax_correction"}`**. Other draft types (`taty_escalation`, `social_reply`) already enqueue by
  calling this service function directly from their own service code, not through the generic REST
  endpoint — this change follows that same precedent for `campaign_package`.
- `approve_draft`/`reject_draft` (and their REST endpoints `/approve`, `/reject`) are fully generic
  — no journal-entry-specific behavior — and can be reused as-is for approving/rejecting a
  `campaign_package` draft.
- `agent_critic.py` is a deterministic, LLM-free double-entry accounting validator — unrelated to
  content evaluation. No name collision risk; the new module is `content_evaluator.py`.
- The LLM call idiom (`llm_engine.get_ai_response_with_profile(...)`, wrapped in
  `try/except AllProvidersFailedError` with a deterministic fallback) is established by
  `social_ops_service.generate_idea_draft()` — this change follows it exactly for both the
  Copywriter and the Content Critic.
- `ai-specs/social-content-ops/` (the brand corpus: `content_ops_rules.md`, ground-truth doc) is
  **untracked in git** (`git status` shows `?? ai-specs/social-content-ops/`) — it is not committed
  and therefore would not exist in a fresh clone or on Railway. The brand rubric this change needs
  cannot depend on reading that folder at runtime.
- No hook-structure template exists anywhere in the repo or the brand corpus — this change defines
  one.

## Goals / Non-Goals

**Goals:**
- A working generate → evaluate → package → approve loop, runnable end-to-end today, producing a
  real, human-approved `campaign_package` row in the Approval Queue.
- Reuse the Approval Queue's existing approve/reject machinery untouched.
- Ground the Critic's rubric in Contexia's actual brand rules (`content_ops_rules.md` §7–8), baked
  into the backend so it doesn't depend on an uncommitted folder at runtime.
- Keep the frontend consistent with existing Búnker patterns (`IdeasTab.tsx`'s click-to-advance
  idiom, `@theme` tokens, no new libraries).

**Non-Goals:**
- Actually posting anything to Meta/Facebook/Instagram — that's Manus's job (Change F). This
  change's output is an *approved database row*, nothing more.
- Real ad budget allocation or spend — `budget` is a placeholder number in this change.
- Modifying the Approval Queue's own service/endpoint code — this change is a new *caller*, not a
  new capability of that subsystem.
- A/B testing, telemetry feedback, or multi-round campaign iteration — that's Change G.
- Committing the `ai-specs/social-content-ops/` folder to git — out of scope; this change instead
  bakes a condensed rubric directly into `content_evaluator.py` (see Decision 4).

## Decisions

1. **Enqueue via direct service call, not the generic REST endpoint.** `sell_machine_service.py`
   imports and calls `ApprovalQueueService.enqueue_draft(draft_id=uuid4, draft_type=
   "campaign_package", journal_entry=campaign_package_dict, memo=...)` directly — matching the
   established pattern for non-journal draft types. *Alternative considered*: extend
   `approval_queue_endpoints.py`'s `EnqueueRequest` model to accept a generic `payload: dict` for
   non-journal types. Rejected — that file is scoped to accounting drafts per its own tests
   (`test_approval_queue_persistence.py` etc.); changing its public contract is out of scope for a
   change that only needs to *call into* it, and the direct-service-call pattern is already how two
   other draft types work.

2. **`campaign_package` skips Critic validation in `enqueue_draft` (confirmed, not a bug) — this
   change's own Content Critic is the validation step**, running *before* enqueue, not after. The
   Approval Queue's `enqueue_draft` performs zero content validation for this draft type by design
   (it's not a `JOURNAL_ENTRY_DRAFT_TYPE`) — this change's Content Critic is the only quality gate,
   and it must run to completion (with survivors, even zero) before `sell_machine_service` calls
   `enqueue_draft` at all.

3. **New LLM profile: reuse `social-ops-v1`** (Groq primary + OpenRouter Free fallback) for both
   Copywriter and Content Critic calls, rather than adding two new named profiles
   (`copywriter-v1`/`content-critic-v1`) to `PROFILE_CONFIGS`. *Rationale*: this is a batch,
   non-interactive workflow (same tier as Social Ops' idea drafting), and adding new profile names
   before there's a reason to route them differently (e.g. a different model/temperature need) is
   premature — `PROFILE_CONFIGS` entries can be split out later without changing any calling code
   (the `profile_name` string is passed at call time, not baked into a type). *Alternative
   considered*: two new dedicated profiles now. Rejected — no evidence yet they need different
   routing than `social-ops-v1`; over-provisioning config for a hypothetical future need.

4. **Content Critic's brand rubric is a hardcoded string constant in `content_evaluator.py`**,
   condensed from `content_ops_rules.md` §7 ("Never" rules) and §8 (humanización rules), not a
   runtime file read from `ai-specs/`. *Rationale*: the `ai-specs/social-content-ops/` folder is
   untracked and would not exist in a deployed environment; hardcoding a condensed rubric (mirrors
   `taty_service.py`'s own hardcoded `KNOWLEDGE_SOURCES` MVP fallback pattern) is simple, correct,
   and deploys reliably. *Alternative considered*: commit `ai-specs/social-content-ops/` to git and
   read it at runtime. Rejected — that folder is explicitly out of this repo's canonical structure
   per `CLAUDE.md` §10 ("no crear carpetas `raw/`, `brain/`... aquí"); committing a 200KB+ legacy
   corpus as a side effect of this change is scope creep. A future change can formalize a real KB
   entry for brand voice if richer grounding is needed.

5. **Hook data shape**: `{headline: str, body: str, cta: str, pain_tag: str}`. A "hook" is one
   short marketing angle (headline + supporting line + call-to-action), tagged with the DIAN/tax
   pain it addresses (reusing the same `pain_tags` vocabulary Social Ops leads already use, for
   consistency). *Alternative considered*: a richer structure (multiple format variants per hook,
   e.g. IG vs FB copy). Rejected for this change — the campaign package's `creative_brief` field is
   where format/channel guidance lives instead; keeping the hook itself minimal keeps the
   Copywriter/Critic loop simple and testable.

6. **Frontend: a new top-level Búnker sidebar item ("Sell Machine"), not a CRM/Ventas sub-tab.**
   Matches the existing precedent (Social Content Ops, Onboarding are each standalone sections
   despite similar "creative/ops workflow" shape) and avoids overloading `CrmVentasSection.tsx`,
   whose `contexia-app/CLAUDE.md` contract explicitly scopes it to B2B retainers + B2C Renta
   Natural only. *Alternative considered*: a third `CrmVentasSection.tsx` tab. Rejected — would
   blur that component's documented, narrower scope for no file-count benefit that matters at this
   size.

7. **Critic gets at most one rewrite pass per hook.** If the Critic rejects a hook with a specific
   reason, the Copywriter is asked once to rewrite addressing that reason; the Critic re-evaluates
   the rewrite once; if still rejected, the hook is discarded (not retried again). *Rationale*:
   bounds the loop's cost/latency deterministically (max 2 LLM round-trips per hook) while still
   implementing the "evaluator-optimizer" pattern from the original vision, rather than either 0
   rewrites (pure filter, loses the "forces a rewrite" idea) or unbounded retries (unpredictable
   cost/latency, risk of infinite loops on a persistently-bad hook).

## Risks / Trade-offs

- **[Risk] LLM-based Critic is non-deterministic** — the same hook could pass or fail on different
  runs. → **Mitigation**: the deterministic fallback path (keyword-ban check for the explicit
  "Never" rules — e.g. "firma contable regulada," "estados financieros" in the wrong context) always
  runs as a backstop when the LLM call fails, and is itself a hard gate the LLM-based judgment
  cannot override in the *approve* direction (a hook that fails the keyword check is always
  rejected, regardless of what the LLM says) — see Task 4.2 for the exact precedence.
- **[Risk] `enqueue_draft`'s `tenant_id` is not persisted on the row (confirmed pre-existing gap,
  not introduced by this change)** — `campaign_package` rows, like `taty_escalation`/`social_reply`
  before them, will not be tenant-filterable via the DB column even though `list_drafts` accepts a
  `tenant_id` param. → **Mitigation**: out of scope to fix (pre-existing Approval Queue behavior,
  shared by every non-journal draft type already); Cliente Cero is the only tenant today so this
  has no practical effect, but is worth fixing in a dedicated Approval Queue hardening change later.
- **[Risk] No real budget/spend validation** — `budget` is an unchecked placeholder number. →
  **Mitigation**: explicitly a non-goal; Manus (Change F) or a future change adds real budget
  guardrails before any real spend is possible.
- **[Trade-off] Reusing `social-ops-v1`'s profile** means Copywriter/Critic share GLM/Groq quota and
  routing with Social Ops' idea generator — acceptable at current volume; revisit if either
  workflow needs independent rate limits or a different model.

## Migration Plan

1. No DB migration needed — this change writes only to the existing `approval_queue` table via the
   existing service function; no new tables.
2. Deploy backend (Railway) behind `SELL_MACHINE_CANONICAL` (default `false`) — dark deploy, same
   playbook as `CRM_CANONICAL`.
3. Deploy frontend (Vercel) with the new Búnker sidebar item — bump `sw.js` CACHE_VERSION, sync
   `contexia-app/out/` → `app/` additively (Python-based chunk verifier, per the established
   incident-avoidance process).
4. Flip `SELL_MACHINE_CANONICAL=true` on Railway after a prod smoke-test (generate a few hooks,
   confirm the Critic filters correctly, confirm a package reaches the Approval Queue and can be
   approved/rejected via the existing endpoints).
5. **Rollback**: flip the flag back to `false`; no destructive DB change to undo (only additive
   `approval_queue` rows with `draft_type='campaign_package'`, harmless to leave in place).

## Open Questions

- Exact N (hooks generated per request) and K (target survivor count) — defaulting to N=5, K≤3
  (matching the "3 survivors" the original vision describes), tunable via a request parameter.
- Whether to eventually give `campaign_package` its own dedicated `crm_wompi_transactions`-style
  table instead of living purely inside the generic `approval_queue.payload` jsonb — deferred until
  Change F needs richer querying/filtering than the generic queue provides.
- First B2C segment for real campaign targeting (asalariados vs informales) — still deferred to
  whenever Change F/real Meta dispatch is reachable, per the original plan; this change's
  `target_segment` field accepts free text and doesn't hardcode either option.
