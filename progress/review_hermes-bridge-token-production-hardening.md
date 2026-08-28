# Review — task hermes-bridge-token-production-hardening

**Verdict:** CHANGES_REQUESTED

## Summary

The core security fix is sound: apps/hermes-manus-poller/backend_client.py and config.py were
correctly rewritten to send Authorization: Bearer <HERMES_BRIDGE_TOKEN> instead of the dead
self-signed JWT, python-jose was dropped from requirements.txt, the backend's
require_hermes_bridge_token guard (apps/backend/presentation/sell_machine_endpoints.py:44-56)
was correctly left untouched (matches design.md Decision 1, already timing-safe via
hmac.compare_digest), no secret values leaked into any repo file, and live verification
(401/200/401, real poller tick) is credible and consistent with the code. All poller tests (47/47)
and the relevant backend tests (test_operator_task_endpoints.py 23/23,
test_sell_machine_endpoints.py 9/9) pass; init.sh is green.

However, one of the change's own completion claims in tasks.md is factually false, and it points
to a real, user-facing gap directly on the security surface this change is about. That must be
fixed before commit.

## Findings

### 1. BLOCKING - apps/hermes-manus-poller/.env.example still documents the dead CONTEXIA_JWT_SECRET and never mentions HERMES_BRIDGE_TOKEN

apps/hermes-manus-poller/.env.example line 17 reads:

    # Only needed if /api/v1/sell-machine/tasks/* ever gets auth-gated (open today).
    CONTEXIA_JWT_SECRET=

git status/git diff confirm this file was NOT touched by this change (still at commit 6a278c4,
pre-dating this work). Two problems:

- It directly contradicts tasks.md task 7.1, which is checked [x] and claims: "Confirm no
  remaining references to CONTEXIA_JWT_SECRET or sign_tenant_jwt exist anywhere in
  apps/hermes-manus-poller/ (grep to verify). (Zero matches, confirmed clean.)" - this is false;
  grep -rn "CONTEXIA_JWT_SECRET" apps/hermes-manus-poller/ returns this exact line. The task's
  own inline notes on what was actually done/verified (which I was explicitly asked to treat as
  claims to verify, not facts) do not hold up here.
- It is a real functional gap, not just a stale comment: apps/hermes-manus-poller/README.md's
  documented setup flow ("Install (founder, one time)") is literally "copy .env.example .env"
  then fill in values. A fresh poller setup following that instruction (i) has no field to fill in
  HERMES_BRIDGE_TOKEN at all, and (ii) is told by the remaining comment that the bridge is
  "open today" - which AGENTES.md's own corrected text (this same change, lines 348-350) now
  says is false: the token is "live and enforced in production as of 2026-08-28." This is exactly
  the class of stale-onboarding-doc problem this change exists to close.

Required fix: update apps/hermes-manus-poller/.env.example to remove CONTEXIA_JWT_SECRET
and add a HERMES_BRIDGE_TOKEN= placeholder with an accurate comment (token is required in
production; empty is fine for local dev against a backend with the guard unset). Then correct
task 7.1's claim in tasks.md to reflect what was actually found.

### 2. Process gap - no progress/impl_hermes-bridge-token-production-hardening.md

HARNESS.md requires the implementer to write progress/impl_<id>.md ("no en el chat"); the
reviewer protocol explicitly expects to read it. No such file exists for this change (confirmed via
glob across progress/) - only feature_list.json's "active" pointer and the inline notes baked
into tasks.md document what happened this session. This isn't a functional defect (everything was
reconstructed and verified directly from git diff + tasks.md), but it's a real deviation from the
documented loop and should be added before archiving, so a future reader isn't left re-deriving
the trail from task-list prose the way this review had to.

### 3. Non-blocking observation - stale comment in apps/backend/config.py

apps/backend/config.py lines 93-96's comment on HERMES_BRIDGE_TOKEN still reads "Unset (None) by
default: routes remain open exactly as before this change... Activation requires coordinating the
Hermes-side poller first." This is now stale (production has the token set), but this file was
NOT modified by this change (the diff present on this file belongs to a different, parallel
LLM-cascade session - confirmed via git diff apps/backend/config.py, which only touches the
GROQ_API_KEY/OPENROUTER/CEREBRAS/NVIDIA block). Per design.md Decision 1, backend code was
correctly left untouched by this change. Flagging for awareness only - not this change's
responsibility to fix, and not blocking.

## Checkpoints (DEPLOYMENT_STAGE/CHECKPOINTS.md)

- Stage 0 (Setup): N/A - no feature-branch model in use here; working tree scoped correctly (see
  Scope check below).
- Stage 1 (Propuesta): [x] proposal.md exists, Why/What/Impact all concrete and verifiable.
- Stage 2 (Diseno): [x] design.md exists, 3 decisions with rationale, trade-offs, migration plan,
  rollback documented.
- Stage 3 (Spec): [x] specs/hermes-manus-execution-bridge/spec.md updated with concrete scenarios
  matching the implemented behavior.
- Stage 4 (Tasks): [x] tasks.md has all sections including Stage 11; each task is small; but see
  Finding 1 - task 7.1's completion note is inaccurate.
- Stage 5 (Implementacion):
  - [x] Code compiles / no syntax errors (tests import and run cleanly).
  - [x] Existing tests pass (poller 47/47, backend test_operator_task_endpoints.py 23/23,
        test_sell_machine_endpoints.py 9/9).
  - [x] New tests pass and assert real outcomes (TestBackendClientHeaders in
        apps/hermes-manus-poller/tests/test_poller.py asserts the actual Authorization header
        value/absence, not just "no exception").
  - [x] Linting/type-checking: no type-checking disabled, no fabricated stubs found.
  - [ ] Docs: apps/hermes-manus-poller/.env.example NOT updated - Finding 1. AGENTES.md correction
        (lines 345-355) is accurate and doesn't contradict surrounding text.
  - [x] Docs-sync (canon vivo): ARCHITECTURE.md correctly left unmodified - no container or
        external dependency changed at the architecture-decision level (removing python-jose is
        an internal poller dependency, not a new container/integration); this repo's current diff
        to ARCHITECTURE.md / apps/backend/config.py / apps/backend/agents/llm_engine.py /
        apps/backend/tests/test_profile_support.py / progress/current.md is confirmed to come from
        a DIFFERENT, parallel session (LLM free-tier cascade work), not this change - verified via
        git diff on each file's actual content.
  - Database: N/A, no migrations in this change.
- Stage 6 (Review - this review): code review completed above; no hardcoded secrets found in
  openspec/changes/hermes-bridge-token-production-hardening/ or
  docs/runbooks/hermes-bridge-token-rotation.md (grepped for high-entropy strings and
  "Bearer <token>" patterns - only variable/function names, no values, consistent with
  ARCHITECTURE.md Decision #12).
- Stage 7 (Deploy): substance already done and live-verified per tasks.md Section 4/5 (Railway
  HERMES_BRIDGE_TOKEN set, redeployed d7eeeed3, 401/200/401 confirmed, real poller tick
  succeeded) - but git status shows the poller code itself is still UNCOMMITTED, and no
  reports/YYYY-MM-DD-deployment.md exists yet. Per this review's scope (gate before commit), this
  is expected sequencing, not a defect - flagging so Section 10/11 aren't skipped afterward.
- Stage 8 (Cierre): not yet applicable - change is not being archived in this pass.

## Scope check (git status)

git status --porcelain shows this change's own files are surgical and match the proposal's
declared Impact section exactly:
- apps/hermes-manus-poller/backend_client.py, config.py, requirements.txt, tests/test_poller.py
  (modified) - all reviewed line-by-line via git diff, match tasks.md Section 1 exactly.
- AGENTES.md (modified) - only the Hermes-bridge exception paragraph (lines 345-355) plus one
  unrelated WhatsApp-inbound-only addition from a prior session; confirmed via git diff this
  change only touches the bridge paragraph.
- docs/runbooks/hermes-bridge-token-rotation.md, openspec/changes/hermes-bridge-token-production-hardening/
  (untracked, new) - belong to this change.
- feature_list.json (modified) - sets "active" pointer to this change, correct per HARNESS.md's
  "puntero fino" convention.

Confirmed NOT this change's doing (diffed independently, content unrelated to bridge auth):
ARCHITECTURE.md, apps/backend/config.py, apps/backend/agents/llm_engine.py,
apps/backend/tests/test_profile_support.py, progress/current.md - all belong to a parallel
LLM-routing-cascade session per their actual diff content. Not held against this change.

## Required changes (before commit)

1. Update apps/hermes-manus-poller/.env.example: remove the CONTEXIA_JWT_SECRET= line and its
   stale "open today" comment; add HERMES_BRIDGE_TOKEN= with a comment reflecting that production
   requires it (per AGENTES.md's own updated text) while empty is still fine for local dev
   against a backend with the guard unset.
2. Correct tasks.md task 7.1's note - it currently claims zero matches for CONTEXIA_JWT_SECRET
   in apps/hermes-manus-poller/, which is false. Fix the file, then re-verify the claim, then
   update the note to reflect what was actually found and fixed.
3. (Recommended, not blocking re-review) Add progress/impl_hermes-bridge-token-production-hardening.md
   documenting what the implementer changed, per HARNESS.md's convention - currently missing.

Once (1) and (2) are done, re-run:
  grep -rn "CONTEXIA_JWT_SECRET\|sign_tenant_jwt" apps/hermes-manus-poller/
to confirm zero matches for real, then this change is ready for another review pass.

---

# Follow-up review — task hermes-bridge-token-production-hardening (re-review)

**Verdict:** PASS (ready to commit)

## What was re-verified independently (not just re-reading the implementer's summary)

1. **`.env.example` fix (Finding 1)** — read `apps/hermes-manus-poller/.env.example` directly.
   Line 6 (old `CONTEXIA_JWT_SECRET=` + "open today" comment) is gone. Lines 16-20 now read:
   ```
   # Shared bearer secret for /api/v1/sell-machine/tasks/* — must match the backend's
   # HERMES_BRIDGE_TOKEN on the canonical Railway service (-175a). Required in production as of
   # hermes-bridge-token-production-hardening; leave empty only for local dev against a backend
   # where the token is also unset (see docs/runbooks/hermes-bridge-token-rotation.md).
   HERMES_BRIDGE_TOKEN=
   ```
   Accurate, references the real runbook (`docs/runbooks/hermes-bridge-token-rotation.md`, confirmed
   it exists), and matches the backend's actual setting name. Also re-checked
   `apps/hermes-manus-poller/README.md` (the "copy .env.example .env" onboarding flow this finding
   was about) — no remaining reference to `CONTEXIA_JWT_SECRET` or "open today" there either.

   Ran the grep myself, unscoped (no `--include`), directly against the poller directory:
   `grep -rn "CONTEXIA_JWT_SECRET\|sign_tenant_jwt" apps/hermes-manus-poller/` → **zero matches**
   (exit code 1). Confirmed clean for real, not just per the implementer's claim.

   Note: a repo-wide (non-scoped) grep for the same pattern still hits 20 files, but every one of
   them is either (a) this change's own OpenSpec/progress artifacts (expected — they discuss the
   fix), or (b) `apps/chatwoot-bridge/*` and its archived OpenSpec changes — a genuinely different
   app with its own JWT-based auth, explicitly out of scope per this change's proposal.md ("Impact"
   section only lists `apps/hermes-manus-poller/` and `apps/backend/presentation/sell_machine_endpoints.py`).
   Not a defect in this change.

2. **`tasks.md` task 7.1 correction** — read `openspec/changes/hermes-bridge-token-production-hardening/tasks.md:87-92`.
   It now accurately narrates the reviewer's finding (grep wrongly scoped to `*.py`, missed
   `.env.example:17`), the fix applied, and the re-verification with an unscoped grep. This is a
   truthful completion note now, not a false one.

3. **`progress/impl_hermes-bridge-token-production-hardening.md`** — confirmed it exists and covers
   all 8 implementation sections (poller bearer-auth switch, backend guard confirmation, inert
   deploy verification, secret generation/Railway/local `.env` configuration, live verification
   curls, living-docs updates, the Section 7 cleanup correction itself, and testing), plus a
   "Files touched" list and an honest "Next step" note. Satisfies HARNESS.md's implementer
   paper-trail requirement; the process gap from Finding 2 is closed.

## Sanity check — nothing else regressed since the first pass

- `git status --porcelain`: same file set as the first review's Scope-check section, no new scope
  creep from this change (`.env.example`, `backend_client.py`, `config.py`, `requirements.txt`,
  `tests/test_poller.py`, `AGENTES.md`, `feature_list.json`, plus the new `docs/runbooks/...`,
  `openspec/changes/hermes-bridge-token-production-hardening/`, and the two `progress/*.md` files).
  `ARCHITECTURE.md`, `apps/backend/config.py`, `apps/backend/agents/llm_engine.py`,
  `apps/backend/tests/test_profile_support.py`, `progress/current.md` are still dirty from the
  parallel LLM-cascade session, confirmed again via `git diff apps/backend/config.py` — content is
  100% about the Groq/OpenRouter/Cerebras/NVIDIA provider cascade, nothing touching
  `HERMES_BRIDGE_TOKEN`. Not this change's doing, as already established in the first pass.
  (New, unrelated: `ai-specs/references/registro-mercantil-contexia.md`, untracked — unrelated
  content from some other track, not referenced anywhere in this change's tasks.md/impl file, not
  blocking.)
- Poller suite: `python -m pytest tests/test_poller.py -q` → **47/47 passed**.
- Backend suite (run from `apps/backend/` — the two test files use a cwd-relative path internally,
  which is why running them from the repo root gives a spurious `FileNotFoundError` unrelated to
  this change): `python -m pytest tests/test_operator_task_endpoints.py tests/test_sell_machine_endpoints.py -q`
  → **32/32 passed** (23 + 9), matching the first review's count.
- `bash init.sh` → green (canon docs present, harness structure present, `feature_list.json`
  correctly points `active` at this change, one-change-at-a-time invariant holds).
- All findings from the first pass that were already marked `[x]`/non-blocking (core bearer-token
  rewrite, backend guard left untouched, no secret values leaked, live 401/200/401 verification,
  ARCHITECTURE.md correctly left unmodified) were not re-litigated in full — only spot-checked via
  the git-status/diff pass above — per this task's instruction not to redo the whole first review.

## Updated checkpoints (deltas from the first pass only)

- Stage 4 (Tasks): [x] — task 7.1's note is now accurate (was `[x] but inaccurate` in the first pass).
- Stage 5 Docs: [x] — `.env.example` now updated (was `[ ]` — Finding 1 — in the first pass).
- HARNESS.md implementer paper trail: [x] — `progress/impl_hermes-bridge-token-production-hardening.md`
  now exists (was missing — Finding 2 — in the first pass).
- All other Stage 0-8 checkpoints from the first pass stand unchanged (see above) and remain `[x]`
  or correctly `N/A`.

## Remaining non-blocking observation (carried over, still not this change's responsibility)

- Finding 3 from the first pass (`apps/backend/config.py`'s stale `HERMES_BRIDGE_TOKEN` comment
  claiming "routes remain open... exactly as before this change") still stands as-is — that file is
  not part of this change's diff (confirmed again above), so it's not a gate here. Flagging again
  only so it isn't lost before the next session that does touch `apps/backend/config.py`.

## Verdict

Both required changes from the first pass are done and independently verified against the actual
file contents and a fresh, unscoped grep — not just the implementer's summary. No regressions found
in the surrounding scope. Tests green (poller 47/47, backend 32/32), `init.sh` green.

**APPROVED — ready to commit** (Section 10.1), then proceed to Stage 11 (deploy report) per
tasks.md Section 11, which is still open and expected to remain so until after commit/push.
