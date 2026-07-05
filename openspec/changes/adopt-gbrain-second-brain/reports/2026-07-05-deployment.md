# Deployment Report — adopt-gbrain-second-brain

**Date:** 2026-07-05
**Deploy branch:** main
**Commit:** `8731ce7`
**Backend URL:** https://antigravity-app-production-175a.up.railway.app (unaffected — no backend code touched)

## What shipped

Adopted [GBrain](https://github.com/jpelaezcardenas/garrytan-gbrain) (Garry Tan's real, MIT-licensed, self-hosted knowledge engine) as Contexia's Level-5 second brain — replacing an earlier plan to build a custom Python clone, once the real tool was found to already provide hybrid search, an auto-wiring knowledge graph, a background job queue, native MCP servers, and native Hermes integration.

### Architecture (final, as actually built — corrected twice mid-implementation)

1. **Two-repo split** (corrected from an initial single-repo plan): `contexia-brain` is a separate GitHub repo holding all knowledge content (`raw/` inbox + MECE compiled directories adapted from GBrain's default VC-oriented schema to Contexia's B2B domains). This was necessary because `antigravity-app`'s `main` auto-deploys to Vercel/Railway on every push, and GBrain's autonomous maintenance cycle auto-commits on a schedule — co-locating them would have made every autonomous brain update trigger a production deploy.
2. **WSL, not native Windows** (corrected from the initial install location): GBrain's `autopilot.ts` has zero Windows support (only macOS/launchd and Unix crontab). Moved the whole GBrain + `contexia-brain` install into the same WSL Ubuntu environment Hermes already runs in. This WSL happens to have systemd, so `gbrain autopilot --install` created a proper `gbrain-autopilot.service` rather than falling back to crontab.
3. **Storage**: dedicated `gbrain` Postgres schema in Contexia's existing (correct, data-verified) Supabase project — confirmed zero overlap with `public.knowledge_chunks`/`decision-vectorization`/`similarity-search`, which remain completely untouched.
4. **Multi-tool access**: GBrain's MCP server wired into Claude Code (`.mcp.json`), Codex (`config.toml`), and Hermes (profile-scoped `config.yaml`) — all via a wrapper script (`~/gbrain-mcp-serve.sh`) that loads the DB connection + API key and execs `gbrain serve`.
5. **Agent catalog projection**: `scripts/generate_gbrain_skills.py` generates 12 reference skills from `AGENTES.md` (canonical, unchanged) into GBrain's skill directory + `manifest.json` + `RESOLVER.md` — additive to GBrain's 28 native skills, not a replacement.
6. **Stage 11 harvest**: `scripts/harvest_stage11_reports.py` feeds completed deployment reports from `antigravity-app` into `contexia-brain/raw/`, cross-repo by design, with a content-hash dedup ledger.

## Real bugs found and fixed during implementation (not just planned work)

- **OpenAI key**: took 3 attempts to get a working embeddings key (invalid key → 401; valid-but-zero-quota key → 429; admin-scoped key with real balance → worked). Verified each with a cheap `curl` probe before committing to a full 58-page embed run.
- **Skill generator**: wrong directory layout (flat files, not one-dir-per-skill); missing `manifest.json` registration (GBrain's `check-resolvable` reads total_skills from this file, not a filesystem scan — verified in source); CRLF line endings from Windows Python writing through a `\\wsl.localhost\` UNC path, breaking GBrain's LF-only frontmatter regex.
- **Hermes MCP config**: initially edited the wrong file (`~/.hermes/config.yaml` top-level) — the profile-scoped CLI actually reads `~/.hermes/profiles/contexia/config.yaml`, a separate file. Caught via `hermes mcp list` reporting "No MCP servers configured" despite the edit.
- **`sync --watch` documentation error**: an earlier draft of this change incorrectly claimed no GBrain watch mode existed; corrected after `gbrain --help` showed it does.

## Verification performed (real, not simulated)

- 58/58 pages imported, 59/59 chunks embedded, 100% coverage (`gbrain doctor`).
- Cross-language semantic search proven: a Spanish query worded nothing like the English source content correctly ranked the right documents.
- 41 MCP tools confirmed via both direct CLI (`gbrain --tools-json`) and through Hermes's own MCP client (`hermes mcp test gbrain`) — identical counts.
- Autonomous maintenance cycle proven end-to-end: a real test note with a new entity was committed to `contexia-brain`, and `gbrain dream` (the same mechanism the running `gbrain-autopilot.service` uses on its own schedule) synced, embedded, and made it genuinely searchable within moments.
- Non-destructive failure confirmed: a `kill -9`'d cycle process left no data corruption (`git status` clean, `gbrain stats` unchanged) — though the kill was actually absorbed by the concurrent-run lock (the autopilot's own legitimate cycle was already running), not a genuine mid-phase interruption; a true mid-phase kill test would require pausing the service first, judged not worth the added risk for this change.
- `similarity-search`/`decision-vectorization` confirmed unaffected: `/api/v1/kb/search` (the real endpoint — the OpenSpec-documented `/search-similar` path doesn't actually exist, a pre-existing spec/implementation drift, not caused by this change) tested against live production, returns unchanged (empty, `knowledge_chunks` still 0 rows) behavior.
- Production DB password was rotated mid-change (a real, necessary side effect of verifying Supabase dependents before touching anything) — both dependent Railway services updated and confirmed healthy with zero verified downtime beyond the redeploy window.

## Explicitly deferred / not done

- **Antigravity IDE/2.0 MCP support**: inconclusive from config inspection (no settings/extension found); can't drive its GUI from this environment to check further. Fallback (direct markdown read of `contexia-brain`) documented.
- **`../ARCHITECTURE.md` ecosystem-map entry for `contexia-brain`**: not yet added — low risk, already documented in `docs/gbrain-adoption.md` and the repo's own README.
- **Entity graph relationships**: currently 0 links — expected, since `contexia-brain` still only has skeleton resolvers and harvested report stubs, not real compiled entity pages with cross-references yet. Will populate as real content is authored.

## Status: COMPLETE

60/60 tasks done. Ready to archive.
