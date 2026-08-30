## Context

`agents/brand_rubric.py` is the single tracked source for both the Content Critic
(`agents/content_evaluator.py`) and the Copywriter (`services/copywriter_service.py`). Manus
independently discovered and fixed the fail-open bug while porting the positioning correction —
both changes touch the same three files, so they ship together rather than as two changes.

## Goals / Non-Goals

**Goals:**
- Apply the vetted positioning/hook-mix prompt changes to the real canonical modules.
- Make the LLM-unavailable path in `evaluate_hook()` fail-closed, matching Modo A.
- Keep the Claim Ledger and hard-ban gates untouched — they already work correctly.

**Non-Goals:**
- Not touching the n8n "Contexia Content OS" system — that path is abandoned per
  `AGENTES.md` Regla 4 and was already deleted from Manus's sandbox.
- Not building differentiated Growth/Enterprise prompt behavior — out of scope here, tracked
  separately in the GTM master plan's Fase 3.
- Not changing the Approval Queue, HITL gate, or `operator_tasks` state machine.

## Decisions

- **Adopt Manus's file contents directly rather than re-deriving them.** They were independently
  validated (41 passing tests reported) and reviewed here line-by-line against the live repo
  versions before being applied — see the diff review already performed in this session (grep
  confirmed no test asserted brittle prompt substrings that would break, and the
  `_build_grounding_query`/fail-closed test renames were confirmed intentional and matching).
- **Ship the positioning fix and the fail-closed fix together, not as separate changes.** Both
  land in the same three files from the same source; splitting them would mean re-diffing the
  same files twice for no isolation benefit.

## Risks / Trade-offs

- [Risk] `evaluate_hook()` going fail-closed means an LLM outage now blocks ALL hooks (previously
  only hard-ban/Claim-Ledger-violating hooks were blocked, everything else passed through).
  → Mitigation: this is the intended Modo A behavior — a Content Critic that can silently
  fail-open is a bigger risk (unreviewed content reaching the Approval Queue) than a temporary
  generation freeze during an LLM outage. Accepted per `manus-gate-hitl-decision`.
- [Trade-off] The niche/value default grounding query removes DIAN/Renta-Natural as the cold-start
  default for hook generation. Renta Natural (Campaña 1, B2C) content already comes primarily from
  Manus's own research drafts (`get_latest_manus_draft()`), not from `copywriter_service.py`'s
  internal generation path, so this mainly affects Campaña 2 (B2B freemium/SaaS) content, which is
  exactly the intended shift.

## Migration Plan

1. Copy the 5 file contents (3 source + 2 test) from Manus's vetted output into the repo paths.
2. Run the affected test files locally to confirm the reported 41-pass count.
3. Commit (held locally per founder's standing "hold until plan close" instruction from this
   session — do not push/deploy without explicit confirmation, since this changes live
   Content-Critic behavior).
4. Stage 11 (Railway redeploy) happens only when the founder confirms it's time to push.

Rollback: revert the 3 source files to their pre-change content (previous git commit) — no data
or schema involved, a plain code revert is sufficient.
