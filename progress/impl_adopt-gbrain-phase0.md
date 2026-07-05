# impl — adopt-gbrain-second-brain — Layer 0 + real GBrain install (session 2)

**Change:** `adopt-gbrain-second-brain`
**Date:** session of 2026-07-04 (continued).

## Session 2: real local-machine work (not simulated)

User said "hazlo por mí" — did real, verifiable work on the local machine rather than
continuing to describe what a human would need to do.

### Critical correction discovered mid-implementation

Reading GBrain's own `docs/guides/repo-architecture.md` (its documented two-repo rule: "Never
write knowledge to the agent repo... GBrain indexes the brain repo only") against
`antigravity-app/ARCHITECTURE.md` (main auto-deploys to Vercel/Railway on every push) surfaced a
real risk: the original plan's `raw/`/`brain/` folders inside `antigravity-app` would have made
every autonomous GBrain maintenance-cycle commit trigger a production deploy. **Corrected by
spinning out a separate sibling repo `C:\Users\contexia\Projects\contexia-brain`** with a
Contexia-adapted MECE structure (not GBrain's default VC-oriented 20-directory schema).
Documented as Design Decisions 10-11 in `design.md`, new requirements in both specs, and a
rewritten `tasks.md` (Group 1 retitled, new task 1.0/1.9). Re-validated: `openspec validate` ok.

### Real actions taken (verifiable, not fabricated)

1. **Bun installed natively** — `npm install -g bun` was tried first (safer-seeming) but caused a
   PATH/shim conflict with GBrain's compiled binary launcher; removed and reinstalled via the
   documented native installer (`irm bun.sh/install.ps1 | iex`). Verified: `bun --version` →
   `1.3.14`. Persisted to `~/.bashrc`.
2. **GBrain cloned for real** — `git clone https://github.com/jpelaezcardenas/garrytan-gbrain.git`
   to `C:\Users\contexia\Projects\gbrain-contexia`. Caught and avoided a real hazard: npm's
   `gbrain` package is an unrelated "GPU ML library" by a different author — installing it would
   have been a name-collision mistake.
3. **`bun install && bun link`** per GBrain's own `INSTALL_FOR_AGENTS.md` (NOT
   `bun install -g github:...`, a documented-broken path, issue #218). Verified: `gbrain --version`
   → `0.16.4`.
4. **`contexia-brain` repo created** (git init) with:
   - `README.md`, `RESOLVER.md` (Contexia-adapted decision tree)
   - MECE dirs: `people/`, `companies/`, `deals/`, `meetings/`, `concepts/`, `ideas/`, `media/`,
     `sources/`, `archive/`, each with a resolver `README.md`
   - `templates/compiled-page.md` (moved from the old flat `brain/_TEMPLATE.md`)
   - `raw/` (moved from `antigravity-app`)
   - Deliberately excluded (documented): `projects/`, `prompts/` (antigravity-app already has
     these), `civic/`/`household/`/`personal/`/`hiring/`/`diligence/` (not Contexia's domain)
5. **Harvest script re-pointed cross-repo** — `harvest_stage11_reports.py` now reads Stage 11
   reports from `antigravity-app` and writes into `contexia-brain/raw/` (sibling repo, default
   `--brain-dir ../contexia-brain`). **Ran for real, not dry-run**: 45 reports harvested;
   re-run confirmed idempotency (0 harvested, 45 skipped — dedup ledger works).
6. **`contexia-brain` committed** — initial commit with all of the above.
7. **`antigravity-app`'s `CLAUDE.md`/`AGENTS.md`, `docs/gbrain-adoption.md` updated** to point at
   the separate repo — NOT yet committed (Stage 11 commit is task 11.1, deliberately deferred
   until the rest of the change is verified, per this repo's own Stage 11 discipline).
8. **`.claude/settings.json`** — model self-correction per CLAUDE.md §5 was already applied
   earlier this session (still present, unrelated to this correction).

### Real blockers — genuinely need the founder, not more agent effort

- **Task 2.1**: which Supabase project/dev schema to point GBrain at — needs an actual decision
  + credentials, not something to invent.
- **Task 2.4**: `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` for GBrain's own use (separate from the
  backend's keys) — must come from the founder via Bitwarden, cannot be fabricated.
- **Task 1.9**: whether/where to push `contexia-brain` to a remote (GitHub private repo?) —
  founder decision.
- **Groups 3-8, 10, 11**: depend on 2.1/2.4 being resolved first.

### Harness bookkeeping

`init.sh` re-run: still green. `openspec validate adopt-gbrain-second-brain`: valid.
Progress: 11/60 tasks complete (up from 7/56 before this session's real corrections + work).

## Session 3: founder answers applied, real infra work continues

Founder answered the three blockers directly:
1. **Supabase project** — confirmed data-backed via Supabase MCP: `kpynymwghfwshvcvevxq`
   (dashboard-labeled "contexia-content-os" but verified by actual table contents —
   `erp_journal_entries`, `centinela_alerts`, `approval_queue` with real rows — to be the true
   active production DB matching `ARCHITECTURE.md`'s stated ID). The other candidate, literally
   named "Contexia" (`wzqymuzpjbagnbgsiqig`), is stale/empty with **8 RLS-disabled tables**
   (critical security exposure flagged to founder, not remediated without explicit instruction).
   First migration attempt was correctly blocked by the auto-mode permission classifier (project
   choice was tool-derived, not founder-named) — re-confirmed explicitly via AskUserQuestion,
   then applied: `CREATE SCHEMA gbrain; CREATE EXTENSION vector;` on `kpynymwghfwshvcvevxq`.
   Verified `public.knowledge_chunks` unchanged afterward.
2. **API keys** — founder unlocked Bitwarden and pasted values directly. Caught a real problem:
   the item labeled "Claude Haiku multi-query expansion" actually contained an OpenAI-format key
   (`sk-proj-...`), not Anthropic's (`sk-ant-api03-...`). Flagged explicitly rather than silently
   writing a broken key; founder chose to skip `ANTHROPIC_API_KEY` for now (GBrain runs fully
   functional without it, per its own docs — only query expansion is skipped). `OPENAI_API_KEY`
   written to `gbrain-contexia/.env` (verified gitignored via `git check-ignore`).
3. **GitHub remote for contexia-brain** — founder will run `gh auth login` themselves, then signal
   to proceed with `gh repo create` + push. Not yet done — waiting on that signal.

### Real GBrain usage, this session (not simulated)

- `gbrain init` ran for real (accidental — `--help` wasn't a recognized flag and it executed
  init instead; harmless, PGLite-only, zero Supabase risk, and it was the next planned step
  anyway). Created `~/.gbrain/brain.pglite`. `gbrain doctor` confirmed healthy (warnings only
  expected for an empty brain).
- `gbrain import contexia-brain --no-embed`: **58 pages imported, 59 chunks created**, 0 errors.
- `gbrain embed --stale`: first attempt hit the 2-minute tool timeout (genuinely still working,
  not stuck — `gbrain doctor` afterward confirmed 58 pages present, embeddings still pending).
  Re-launched in the background (task ID `b3ee4m6k5`) to avoid the timeout; awaiting completion
  notification, not polling.
- **Corrected an earlier spec/doc inaccuracy while idle-waiting**: `gbrain --help` shows
  `sync --watch [--interval N]` (continuous) DOES exist alongside `sync --install-cron`
  (periodic daemon) — an earlier draft of this change incorrectly claimed no watch mode existed.
  Fixed in `specs/gbrain-adoption/spec.md`, `tasks.md` 5.1, and `docs/gbrain-adoption.md`.

### Updated task completion

Tasks 2.1 and 2.4 now marked `[x]` in `tasks.md` with the real outcomes above (including the
deliberate ANTHROPIC_API_KEY omission). Progress: 13/60.

## Session 4: GitHub push done; embedding blocked on real OpenAI billing issue

- **Task 1.9 done for real**: `gh auth login` confirmed complete; created
  `github.com/jpelaezcardenas/contexia-brain` (private) via `gh repo create --source=. --remote=origin`,
  pushed `main`. Verified via `gh auth status` before attempting (didn't assume).
- **First `gbrain embed --stale` run**: all 58/58 pages failed with a genuine `401 Incorrect API
  key provided` from OpenAI's real API — the original Bitwarden key was invalid/revoked, not a
  bug on this end (verified the `.env` value matched what was pasted). Founder provided a
  replacement key.
- **Verified the replacement key before burning a full run**: `curl .../v1/models` → `200`, so
  the key authenticates. Re-ran `gbrain embed --stale` (background, task `b9lffn7pr`).
- **Second run: all 58/58 failed again, but with a different, more specific error**:
  `429 You exceeded your current quota, please check your plan and billing details.` — from the
  very first embed call (not mid-run depletion). The key is valid; the OpenAI account behind it
  has **no usable billing/credits**. This is a real, founder-only blocker — cannot be worked
  around from here (no ability to add billing to someone else's OpenAI account).
- Asked the founder how to proceed (add billing / different key / pause). **Founder dismissed
  the question — explicit instruction: do not proceed, wait for next instruction.** Stopping
  here per that instruction, not attempting further embed runs or guessing at a resolution.

### Real state right now

- `contexia-brain`: pushed to GitHub, 58 pages imported into local PGLite brain, **0 pages have
  embeddings** (blocked on OpenAI billing).
- `gbrain` schema exists on Supabase project `kpynymwghfwshvcvevxq`, empty (GBrain hasn't been
  migrated there yet — that step depends on local validation succeeding first, which depends on
  embeddings working).
- Tasks 1.0-1.9 all `[x]` (10/10 in Group 1). Task 2.0-2.1, 2.4 `[x]`. Tasks 2.2, 2.3, 2.5-2.8 and
  all of Groups 3-11 blocked, directly or indirectly, on this OpenAI billing issue.

## Session 5: OpenAI quota resolved, real embeddings + hybrid search proven, Supabase migration done

Founder explained the cost model was unclear ("thought this was free") — clarified GBrain (tool)
is free/MIT, but OpenAI embeddings + optional Claude Haiku expansion are paid API calls;
provided a realistic budget ($5-15/mo at Contexia's scale). Founder asked about swapping to GLM
5.2 (existing subscription) — checked the actual source (`src/core/embedding.ts`,
`src/core/search/expansion.ts`): both are hardcoded to OpenAI/Anthropic SDKs respectively, no
provider-swap config exists. Swapping would mean forking GBrain, contradicting the
no-fork design decision. Founder chose to fund OpenAI instead.

- **Key attempt 3 of 3 worked**: verified with a direct `curl .../v1/embeddings` probe before
  committing to a full run (this `sk-admin-...` key is an OpenAI **Admin API** key — 403 on
  `/v1/models` but 200 on the actual embeddings endpoint GBrain uses; real distinction worth
  remembering). Full `gbrain embed --stale`: **58/58 pages, 59/59 chunks, 0 errors.**
  `gbrain doctor`: embeddings 100% coverage.
- **`gbrain extract links/timeline --source db`**: ran clean, honestly 0 links/0 timeline
  (correct given content is still skeleton resolvers, not real entity pages — not a failure).
- **Hybrid search validated for real**: `gbrain query` with a Spanish query worded nothing like
  the English source content correctly ranked the right Stage 11 reports at the top — genuine
  semantic match proof, not a scripted demo.
- **MCP tool count verified**: `gbrain --tools-json` → 41 tools, exceeds the ≥30 spec requirement.

### Bitwarden master-password exposure — flagged, not fixed inline

While checking what depends on the Supabase DB password (per founder's caution before
resetting it), found `BW_MASTER_PASSWORD`/`BW_CLIENT_ID`/`BW_CLIENT_SECRET` stored in plaintext
as Railway env vars on the `enthusiastic-youthfulness` project (service `antigravity-app`).
Confirmed via code (`apps/backend/core/secrets_provider.py:278-294`) this is load-bearing, not
accidental clutter — so it can't just be deleted. Correct fix (migrate to Bitwarden Secrets
Manager machine-account tokens) is a real architecture change, out of scope for this OpenSpec
change — flagged as a separate background task (`task_d1ec7639`) rather than fixed here.

### Production DB password rotated — real, high-stakes operational work, done carefully

Founder confirmed proceeding. Before resetting anything, checked Railway for dependents (not
assumed): **two** Railway projects' `antigravity-app` services both had `DATABASE_URL` pointing
at this exact DB with the same password — `elegant-success` (`-175a`, the documented production
per `ARCHITECTURE.md`) and `enthusiastic-youthfulness` (`-dc78`, **undocumented** — flagged to
founder as a follow-up question: is this still meant to be live?). Sequence:
1. Founder reset the password via Supabase dashboard (took a few tries — dashboard UI changed,
   first attempts returned the unfilled `[YOUR-PASSWORD]` placeholder, not a real value).
2. Verified new password with `psql` before touching anything downstream — first attempt via
   "Direct connection" timed out (IPv6-only from this network, a real Supabase platform
   constraint, not a bug); switched to "Session pooler" (IPv4-compatible) and confirmed
   connectivity + that the `gbrain` schema is reachable via `search_path`.
3. Updated `DATABASE_URL` in **both** Railway services (minimal diff — kept the same Direct
   connection format the backend already used, since Railway's own infra reaches IPv6 fine;
   only swapped the password) via `railway_set_variable` with `skip_deploys=false` so both
   redeployed immediately (the old password was already invalid at this point — real downtime
   risk if left unaddressed).
4. Waited for both deploys, then verified via actual health-check HTTP calls (not just deploy
   status): both returned `{"status":"healthy","service":"Contexia API"}`. Zero verified downtime
   window beyond the ~90s redeploy itself.

### GBrain migrated from local PGLite to Supabase — verified isolated

`gbrain migrate --to supabase` (pointed at the `gbrain` schema via the Session pooler
connection string). Verified via Supabase MCP `list_tables`, not just GBrain's own output:
`gbrain.pages` = 58, `gbrain.content_chunks` = 59 — exact match to the PGLite source; zero
table-name overlap with `public.*`; `public.knowledge_chunks` unchanged (0 rows, RLS enabled,
untouched). **New finding, flagged not auto-fixed**: 10 of GBrain's own tables lack RLS
(internal plumbing — job queue, audit logs — not user data, but still anon-key-reachable).
Remediation SQL given to founder; awaiting their decision on whether to apply it.

Tasks 2.2, 2.3, 2.5, 2.8, 3.1, 3.5 now `[x]`. Progress: 20/60.

## Session 6: closed the three open items, corrected a wrong assumption along the way

- **RLS on `gbrain.*` internal tables**: founder approved. Applied via migration
  `enable_rls_gbrain_internal_tables`. Verified GBrain still fully functional after (`gbrain
  stats` unchanged: 58/59/59) — the `postgres` role bypasses RLS regardless, so this was
  zero-risk. **Closed.**
- **`-dc78` decommission question — corrected, not closed as originally framed**: my earlier
  claim that `-dc78` was "undocumented/possibly stale" was wrong, based on an incomplete grep
  (only checked `ARCHITECTURE.md`). Full search of `openspec/changes/` and `docs/archive/` found
  it's **known, already-tracked technical debt**: it holds `TELEGRAM_BOT_TOKEN` (which `-175a`
  does NOT have), was the real deploy target for `keeper-migration-2026-06-15`, and appears as
  "Backend" in multiple testing reports. A founder decision from the archived
  `agentic-performance-management-phase4` change explicitly kept both alive "for now," with a
  follow-up ("reconcile the two Railway projects... update CLAUDE.md") that was never turned
  into an actual OpenSpec change. **Retracted the decommission suggestion** — real risk of
  breaking Telegram bot functionality. Flagged the reconciliation properly this time as
  `task_983c64b0`, since it's a real, non-trivial piece of work (webhook target verification,
  env var diff, migration plan), not a today decision.
- **Bitwarden Secrets Manager migration**: already flagged (`task_d1ec7639`), nothing further
  needed here — confirmed still pending, not dismissed/superseded.

## Session 7: WSL move (founder chose option B), autopilot running for real, skill generator built and debugged

- **GBrain moved to WSL** (Ubuntu, colocated with Hermes) — `gbrain autopilot --install` has
  zero Windows support (source only handles macOS/launchd, falls through to Unix `crontab`
  otherwise). Fresh install: Bun (native installer; needed `sudo apt-get install unzip` first,
  founder ran it), GBrain cloned to `~/gbrain`, `contexia-brain` cloned to `~/contexia-brain`
  (private repo — no `gh` in WSL, so cloned via a token derived from the Windows `gh auth
  token`, then `git config credential.helper store` for future syncs). Reconnected to the
  **same** Supabase brain, not a fresh one — verified via `gbrain doctor` (58 pages, 100%
  embeddings, matches exactly).
- **Autopilot genuinely running**: this WSL has systemd (not just crontab), so
  `gbrain autopilot --install` created `gbrain-autopilot.service` — confirmed
  `Active: active (running)` with real child processes. Fixed two real bugs in the
  auto-generated setup: (1) the wrapper script's dotfile-sourcing never applied in systemd's
  non-interactive context, (2) needed an explicit `EnvironmentFile=` under `[Service]` (first
  attempt misplaced it under `[Unit]`) supplying `PATH`/`GBRAIN_DATABASE_URL`/`OPENAI_API_KEY`.
  `loginctl` confirms `Linger=yes` (from Hermes's own setup) — survives logout/session
  boundaries.
- **Skill generator built and genuinely debugged, not just written and assumed correct**:
  `scripts/generate_gbrain_skills.py` parses `AGENTES.md`'s 12 real agent sections and
  generates `contexia-agent-<slug>/SKILL.md` files. Three real bugs found and fixed in
  sequence: (a) wrong directory layout (flat files instead of one-dir-per-skill — checked
  `skills/query/SKILL.md` to confirm the real convention), (b) `manifest.json` registration
  required — GBrain's `check-resolvable`/`skill_conformance` reads `total_skills` from this
  manifest file, not a filesystem scan (verified in `check-resolvable.ts` source, not
  assumed), (c) CRLF line endings (Windows Python writing through a `\\wsl.localhost\` UNC
  path) broke GBrain's LF-only frontmatter regex — fixed with explicit `newline="\n"` on all
  `write_text()` calls. Final verification: `gbrain check-resolvable` →
  `{total_skills: 40, reachable: 40, gaps: 0}`; `gbrain doctor` → `skill_conformance: 40/40
  skills pass`. Documented the one real "exception to no-forking" this required: extending
  upstream's tracked `manifest.json` means a future `git pull` on the GBrain clone will hit a
  merge conflict there (not silent data loss, but real reconciliation work) — noted in
  design.md Decision 12 and the script's own docstring.

Tasks 4.1, 4.2, 6.1-6.5 now `[x]`. Progress: 27/60.

## Next handoff

Continuing to Group 7 (MCP wiring into Claude Code, Codex, Hermes) — the natural next step and
highest remaining value, now that GBrain is fully running (Supabase-backed, autopilot
scheduled, 40 skills conformant). Group 3 tasks 3.2-3.4, 3.6 (RRF dedup check, baseline query
set, per-category tool smoke test) and Group 8 (Antigravity MCP spike) remain after that.
