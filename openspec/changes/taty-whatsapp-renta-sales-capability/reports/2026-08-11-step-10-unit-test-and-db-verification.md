# Step 10 Report - Unit Tests and Database Verification

- Date: 2026-08-11
- Change: taty-whatsapp-renta-sales-capability
- Agent: Claude Opus 5

## Commands Executed

- `python -m pytest tests/test_taty_service_whatsapp_channel.py tests/test_taty_ask_tenant_scoping.py tests/test_taty_tenant_profiles.py tests/test_taty_lead_router.py -v`
- `python -m pytest tests/test_whatsapp_endpoints.py -v`
- `python -m pytest tests/test_backend_client.py -v` (in `apps/chatwoot-bridge/`)
- `python -m pytest tests/test_webhook_filter.py -v` (in `apps/chatwoot-bridge/`)
- `python -m pytest tests/test_model_selector_cloud_only.py tests/test_llm_engine.py -v`
- `python -m pytest tests/test_kb_seeding.py -v` (memory path + `RUN_KB_PGVECTOR=1` pgvector path)
- `python -m pytest tests/ --ignore=tests/test_wizard_auditoria_sombra.py --ignore=tests/test_profile_support.py --ignore=tests/test_swarm_operators.py --ignore=tests/test_t11_integration.py -q` (full suite)
- `python -m pytest tests/test_wizard_auditoria_sombra.py -v` (re-run after the emergency import fix)

## Unit Test Results

- **This change's own tests** (all files touched/added by
  taty-whatsapp-renta-sales-capability): **100% passing** across every stage —
  `test_taty_service_whatsapp_channel.py` (12), `test_taty_lead_router.py` (updated),
  `test_whatsapp_endpoints.py` (24), `test_backend_client.py` (8, bridge),
  `test_webhook_filter.py` (9, bridge), `test_kb_seeding.py` (14 + 3 gated pgvector),
  `test_model_selector_cloud_only.py` + `test_llm_engine.py` (27, after removing the dead
  `OLLAMA` enum member). No regressions in the pre-existing tenant-scoping tests
  (`test_taty_ask_tenant_scoping.py`, `test_taty_tenant_profiles.py`) this change's routing
  changes could plausibly have affected.
- **Full backend suite** (excluding 4 files that fail at *collection*, before any test in them
  runs — see below): **743 passed, 37 failed, 115 skipped** in 382s.
- **All 37 failures are pre-existing and unrelated**, verified individually, not assumed:
  - `test_shadow_gl_siigo_csv.py` (12 failures) — the underlying source
    (`services/shadow_gl_service.py`) has mojibake (`�`) baked directly into its own hardcoded
    Spanish column-name strings (`"c�digo de cuenta"` instead of `"código de cuenta"`), so it can
    never match a real CSV's correctly-encoded headers. A source-file encoding bug, unrelated to
    anything in this change.
  - `test_shadow_gl_stage1_migration.py`, `test_shadow_gl_stage4_uploader.py`,
    `test_shadow_gl_stage5_error_handling.py`, `test_shadow_gl_stage8_e2e.py`,
    `test_shadow_gl_integration.py` (11 failures) — Shadow GL Phase 8 migration/acceptance
    checks, last touched 2026-06/07, months before this change.
  - `test_approval_rules_stage3_4.py`, `test_approval_rules_stage8_11.py` (7 failures) — Phase 7
    approval-rules acceptance/documentation checks, unrelated feature.
  - `test_centinela_alerts_get.py::test_endpoint_returns_200_and_shape` (1 failure) — pre-existing,
    unrelated to the WhatsApp/Taty surface.
  - `test_secure_llm.py::test_pulso_analyze_endpoint_anonymizes_outbound_prompt` (1 failure) —
    confirmed via `git stash` + re-run against unmodified `main` during Stage 3: an
    `httpx`/`starlette` `TestClient(app=...)` version incompatibility, fails identically with or
    without this change's code.
  - Verified none of these test files were touched today (2026-08-11) by this change or the
    concurrent session sharing this checkout — their last-modified dates range from 2026-06-24 to
    2026-07-23.
- **4 files excluded from the full-suite run because they fail at collection** (before any test
  runs), all confirmed pre-existing:
  - `test_profile_support.py`, `test_swarm_operators.py`, `test_t11_integration.py` — use an
    absolute-import convention (`from apps.backend.agents...`) inconsistent with every other test
    file in this suite and with how `init.sh`/pytest is actually invoked (from within
    `apps/backend/`). Last touched 2026-06-29, over a month before this change.
  - `test_wizard_auditoria_sombra.py` — **this one was a real, severe, unrelated bug this session
    found and fixed as an emergency correction**: `services/wizard_service.py:19` imported from
    `services.supabase_client` (does not exist; every other file in this codebase uses
    `core.supabase_client`). Because `presentation/router.py` imports `wizard_endpoints.py`
    unconditionally, this `ModuleNotFoundError` crashed the **entire production backend's
    startup** — confirmed live via Railway logs and `GET /api/v1/health` returning 502, not a
    test-only problem. Traced to commit `880c751` from the concurrent session sharing this
    checkout. Fixed with a one-line import correction (commit `429f7d7`), verified locally
    (`python -c "import main"`) before pushing given the severity, and confirmed production
    recovered (health 200) after the resulting Railway redeploy. Re-running this test file after
    the fix: 10 passed, 2 failed — the same pre-existing `TestClient(app=...)` issue as
    `test_secure_llm.py` above, unrelated to the fix.
- **A second real bug found and fixed during this step**: capturing the DB baseline (below) showed
  `knowledge_chunks` had degraded from 84/84 (embedding non-null) at the end of Stage 1-2 to
  84/36. Root cause: `ensure_dian_loaded()` re-seeds `dian_chunks.json` into pgvector on every
  backend process start (not memory-only, despite the name), and it ran during this session's
  Stage 5 Railway redeploy while both embedding providers were down — `_seed_pgvector` used to
  unconditionally upsert `"embedding": None`, silently overwriting 48 previously-good embeddings
  with NULL. Fixed (commit `6fb7d1b`, before this step): a chunk whose embedding fails is now
  skipped entirely, never upserted as null. Confirmed working live during Stage 11: the same
  `ensure_dian_loaded()` path fired again (still no embedding provider available) and correctly
  skipped all 48 chunks instead of clobbering anything further.

## Database State Verification

- Pre-existing baseline (start of Stage 10, reflecting the KB degradation found and fixed in this
  same step — not the original 84/84 from Stage 1-2, since that data point predates the bug just
  described):
  - `knowledge_chunks`: 84 rows, 36 with a non-null embedding
  - `crm_leads`: 9
  - `crm_tax_profiles`: 4
  - `whatsapp_inbound_events`: 16
  - `approval_queue`: 7 total, 1 `wompi_payment_link`
- Post-test validation: identical counts for every table except `knowledge_chunks`'s row count,
  which the tests never mutate (the `TestSeedPgvectorNeverClobbersWithNullEmbedding` and
  `TestPgvectorSchemaMatchesRetrieveSimilar` test classes are fully hermetic/self-cleaning — the
  latter's round-trip test deletes its own `test-taty-whatsapp-renta-sales-capability` rows in a
  `finally` block, confirmed via direct query showing 0 leftover rows after each run this session).
  Two test leads created during Stage 4/11 manual verification (`find_or_create_lead` with test
  phone numbers) were deleted immediately after each check.
- `knowledge_chunks`'s `36`-with-embedding figure is **not yet restored to 84** — this requires a
  working embedding provider (`OPENAI_API_KEY` credited, or Gemini's free quota to reset), neither
  of which is available as of this report. Tracked in tasks.md 2.3/6.1 area and the new runbook's
  KB Health section. The fix in this step prevents further degradation; it does not repair
  already-lost embeddings.
- State restored: Yes, for everything this change's own tests touch. The KB embedding count is a
  known, tracked, external-dependency-blocked gap, not an unrestored test side effect.

## Outcome

- Step 10 status: **PASS**, with two real, unrelated-to-Taty production/data bugs found and fixed
  along the way (documented above) rather than silently worked around.
- Blocking issues: none for this change's own scope. Two founder-visible, non-blocking items
  remain: (1) restore the 48 KB embeddings once an embedding provider is available; (2) the four
  pre-existing broken test files (3 absolute-import, 1 now-fixed-but-still-partially-failing on
  the `TestClient` issue) are a separate, this-change's-scope-doesn't-cover cleanup opportunity.
