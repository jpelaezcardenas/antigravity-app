# Tasks — voicebox-local-voice-adoption

**Scope reminder:** this change ships the integration **switched off**. "Done" means merged, tested
and inert — not working voice. Enabling it is a migration-day action on the inference node.

## Stage 0. Feature branch and recovered ground truth

- [x] 0.1 Create and switch to `feat/voicebox-local-voice-adoption`
- [x] 0.2 Persist the Phase 0 findings recovered from the session transcript as
      `reports/2026-09-05-fase0-validacion.md` (the file the previous session reported writing
      never existed on disk)
- [ ] 0.3 Retry WSL and repeat the `*voicebox*` / `~/.hermes/plans` search there. **Blocked today:**
      `wsl -d Ubuntu` fails with `Wsl/Service/0x80072747`, and `wsl --shutdown` is not an acceptable
      workaround because Chatwoot runs in Docker Desktop on WSL. Document the outcome either way —
      do not record the path as "empty" without having looked
- [ ] 0.4 Repair the local VoiceBox clone — **diagnosed, deliberately not executed. Founder call.**
      `C:\Users\contexia\voicebox\` holds only a broken `.git`: 58 MB of objects, `HEAD` pointing at
      `refs/heads/.invalid`, no refs, no working tree, and a remote pointing at upstream
      (`jamiepine/voicebox`) rather than the private mirror. It is an aborted `git clone`.

      Not done here because **nothing in this change needs it**: VoiceBox is consumed as an
      installed binary over its REST API, not built from source. Executing it would mean a
      destructive delete plus a 111 MB download for no benefit to the dark launch. When the source
      is actually wanted (patching the meta-tensor bug, say), it is three commands:

      ```
      rm -rf "$USERPROFILE/voicebox"
      git clone https://github.com/jpelaezcardenas/voicebox.git "$USERPROFILE/voicebox"
      git -C "$USERPROFILE/voicebox" remote add upstream https://github.com/jamiepine/voicebox.git
      ```

      The third line matters: `jpelaezcardenas/voicebox` is **not a GitHub fork**
      (`isFork:false`, `parent:null`), so it inherits nothing from upstream automatically

## Stage 1. Decide the Hermes integration shape

- [x] 1.1 Capture the real API contract. **Done 2026-09-08** — the server was already running
      (`voicebox-server.exe`, PID 1152, 1.8 GB resident); pulled `GET /openapi.json` live. Recorded
      in `ai-specs/skills/contexia-voice-tts/references/api.md`. Three findings that invalidated
      assumptions made from the README: (a) `POST /generate` returns **JSON, not audio** — the audio
      is a second call to `GET /audio/{id}`; (b) `language` defaults to **`en`** and `model_size`
      defaults to **`1.7B`**, the model Phase 0 rejected, so both must always be sent explicitly;
      (c) the cloned **"Taty" profile still exists** (`voice_type: cloned`, es, 1 sample,
      8 generations) and `GET /profiles/{id}/export` + `POST /profiles/import` exist — so the
      migration should *export* the validated voice, not re-clone it. `POST /generate` was
      deliberately not called (3-5 min per phrase on this CPU); read-only endpoints only
- [ ] 1.2 Inspect `voicebox-mcp.exe` and the MCP surface. Note: `/openapi.json` lists
      `GET|PUT /mcp/bindings` but no bare `GET /mcp`, so the README's claim needs checking against
      the binary rather than assumed
- [ ] 1.3 Decide `type: command` provider vs MCP registration (design.md Decision 4) and record the
      decision with its reason in `design.md`. Do **not** change `tts.provider` — it stays `edge`

## Stage 2. Safety gate (TDD, backend)

- [x] 2.1 Failing tests in `tests/test_voice_safety.py`: a table of texts covering every rejection
      class (empty, over-length, `$`, `%`, `UVT`, `120 mil`, `28 de abril`, `15/04`) plus accepted
      short conversational replies. Pure function, no mocks, no network
- [x] 2.2 Implement `services/voice_safety.py::should_speak(text, max_chars)`
- [x] 2.3 Failing test asserting `should_speak` is judged on the sanitised text, then wire
      `voice_allowed` into `taty_lead_reply`'s response **after** `sanitize_for_whatsapp`
- [x] 2.4 Test asserting every pre-existing field of the `/leads/{id}/reply` response is unchanged
      (additive-only contract)

## Stage 3. Graph outbound audio (TDD, backend)

- [x] 3.1 Failing test for `upload_whatsapp_media`: asserts the multipart body carries
      `messaging_product=whatsapp` and the file, using `httpx.MockTransport`. **Do not patch the
      function under test** — Decisión #22's rule
- [x] 3.2 Implement `upload_whatsapp_media` in `channels/whatsapp.py`, mirroring
      `download_whatsapp_media`'s unconfigured-credentials contract (return `None`, no network call)
- [x] 3.3 Failing test for `send_whatsapp_audio`: asserts `type: "audio"` and `audio.id` in the JSON
- [x] 3.4 Implement `send_whatsapp_audio`
- [x] 3.5 Test: with `WHATSAPP_TOKEN` unset, neither function makes a network call

## Stage 4. Internal voice endpoint (TDD, backend)

- [x] 4.1 Failing tests in `tests/test_voice_endpoint_auth.py`: `INTERNAL_API_KEY` unset → 503;
      wrong header → 401; correct header → past auth
- [x] 4.2 Failing tests for the rest of the status table in `spec.md` §3.2: unknown lead → 404,
      `VOICE_ENABLED=False` → 503, oversize payload → 413, gate rejects → 422, wrong mime → 415,
      delivery failure → 200 with `sent: false`
- [x] 4.3 Implement `presentation/voice_endpoints.py`
- [x] 4.4 Add `VOICE_ENABLED`, `VOICE_MAX_CHARS`, `VOICE_MAX_AUDIO_BYTES` to `config.py`, all
      fail-closed
- [x] 4.5 **Make `main.py`'s internal-router registration fail loud** (removed the swallowing
      `try/except`) and mount the voice router. Guarded by
      `tests/test_internal_routers_registration.py`. **Deviation, deliberate:** that guard asserts
      at SOURCE level rather than by importing the app. Importing `main` costs ~5 minutes on this
      machine (module import triggers KB/pgvector seeding that waits out every embedding provider's
      timeout), and the property being protected — "this block is not wrapped in try/except" — is
      about how the code is written, not what it computes. Route behaviour is covered separately by
      `tests/test_voice_endpoint_auth.py`
- [x] 4.6 Dark-launch certification. **Landed in two places rather than the single
      `test_voice_flag_off.py` this task originally named**, because the property has two halves and
      they live in different processes:
      * `tests/test_whatsapp_reply_voice_allowed.py::test_voice_allowed_is_false_when_the_feature_is_off`
        — with `VOICE_ENABLED=False` the backend reports `voice_allowed: false` even for a reply the
        gate would allow, and the text reply is untouched.
      * `apps/chatwoot-bridge/tests/test_voice_reply_wiring.py::test_no_voice_work_happens_when_the_flag_is_off`
        — with the flag off the bridge never contacts VoiceBox at all.
      Design note that emerged while writing these: `VOICE_ENABLED` is folded into `voice_allowed`
      on the backend, so the backend is the single authoritative switch and a bridge running a stale
      config cannot burn GPU time on audio the endpoint would reject anyway

## Stage 5. Local bridge (TDD)

- [x] 5.1 Failing tests for `voicebox_client.synthesize` against a fake httpx transport: success
      returns bytes; empty `VOICEBOX_PROFILE_ID` makes no call; timeout and non-200 return `None`
- [x] 5.2 Implement `apps/chatwoot-bridge/voicebox_client.py`
- [x] 5.3 Failing tests for `audio_converter.wav_to_ogg_opus` using a **real small WAV fixture**
      (generated in the test, not an invalid inline blob that would force a mock — the aggravating
      factor Decisión #22 recorded); missing ffmpeg returns `None`
- [x] 5.4 Implement `apps/chatwoot-bridge/audio_converter.py`
- [x] 5.5 Implement `backend_client.send_voice_note` with fail-soft contract + its test
- [x] 5.6 Add the voice settings to the bridge's `config.py` and `.env.example` (names only, never
      values — Decisión #12)
- [x] 5.7 Wire the fire-and-forget voice step into `main.py::process_incoming_message`, mirroring
      `_auto_tag_chatwoot`; test that a raising voice path does not affect the text reply

## Stage 6. Hermes wiring (inert)

- [x] 6.1 Add `apps/hermes-voicebox/voicebox_tts.ps1` — builds the `/generate` JSON body, reads
      `VOICEBOX_PROFILE_ID` from the environment, writes to `{output_path}`
- [x] 6.2 Added the `tts.providers.voicebox` entry (`type: command`, `output_format: ogg`) to the
      live profile config at `AppData\Local\hermes\profiles\contexia\config.yaml`.
      **`tts.provider` left as `edge`** — a switch with no server running would fail every call.
      The MCP alternative stays open (task 1.2/1.3); the command provider does not preclude it
- [x] 6.3 Backed up to `config.yaml.bak_voicebox_20260909` before editing, and re-parsed the file
      afterwards: YAML valid, `tts.provider` still `edge`, `stt.provider` still `local`,
      `model.default` still `xiaomi/mimo-v2.5-pro`. Hermes was not running during the edit

## Stage 7. The `contexia-voice-tts` skill

- [x] 7.1 Create `ai-specs/skills/contexia-voice-tts/SKILL.md` — when it applies, the VoiceBox API,
      which engine and why (Qwen3-TTS 0.6B clones; Kokoro cannot; Chatterbox Turbo is blocked by
      the meta-tensor bug; Qwen 1.7B is unusable), the never-speak-a-fiscal-figure rule, and that
      the correct answer while the flag is off is "unavailable", not an improvisation
- [x] 7.2 Add `references/fase0-benchmark.md` and `references/api.md` (the latter captured live from
      the running server, not from the README)
- [x] 7.3 Add `scripts/sync_hermes_skills.ps1` — idempotent, content-hash based, with a `-Check`
      mode that exits 1 on drift. Deploys a **real directory, not a symlink**: every existing
      `contexia-*` skill in Hermes' profile is a real directory, and a symlink pointing outside the
      repo dangles exactly as CLAUDE.md §8 documents for `DEPLOYMENT_STAGE/`
- [x] 7.4 Run the sync and verify both copies exist. Done — deployed to
      `%LOCALAPPDATA%\hermes\profiles\contexia\skills\contexia-voice-tts`, second run reports
      `[ok] already in sync`
- [x] 7.5 Expose the skill to Claude Code. **Followed the repo's real pattern, not CLAUDE.md §6's
      stated one:** `.claude/skills/*` are tracked as regular files (`100644`), not symlinks
      (`120000`), and `diff` confirms they are byte-identical duplicates of their `ai-specs`
      sources; `.cursor/` does not exist in this repo at all. Copied the skill to
      `.claude/skills/contexia-voice-tts/` to match. Raised as doc drift in 12.7 rather than
      silently "fixing" CLAUDE.md or inventing a `.cursor` tree.
      **Note on tracking:** `.gitignore:114` ignores `.claude/*`, so this copy is local and
      untracked. The older `.claude/skills` entries are tracked only because they predate that rule;
      the most recent one (`new-thread`) is untracked too. Left untracked to match current practice
      — **not** force-added, since `git add -f` would silently re-open a directory the repo chose to
      stop tracking. `ai-specs/skills/contexia-voice-tts/` is the tracked canonical copy

## Stage 8. Review and update existing unit tests (MANDATORY)

- [x] 8.1 Reviewed. **Nothing needed updating** — no existing backend test asserts the exact key
      set of the `/leads/{id}/reply` response, so the additive `voice_allowed` field breaks none of
      them. Proven by the baseline diff in 9.1/9.3, not by reading alone
- [x] 8.2 Reviewed. Two bridge tests fail, and **both are pre-existing**: verified by stashing
      this change's `main.py` and re-running — they fail identically without it.
      `test_chatwoot_client.py::test_posts_an_incoming_message` (this change never touches
      `chatwoot_client.py`; `git diff` on it is empty) and
      `test_process_message.py::test_reply_comes_from_the_sales_router_not_hermes` (expects
      `send_reply(id, text)`, code passes `private=True`, which predates this change)
- [x] 8.3 Confirmed. The Graph tests drive real httpx through `MockTransport` rather than
      patching `upload_whatsapp_media`/`send_whatsapp_audio`; the gate tests call `should_speak`
      directly; the endpoint tests assert the endpoint uses the real `services.voice_safety`
      function object; the converter test builds a genuine WAV with `wave` and runs real ffmpeg
      (the one patch there replaces the resolved ffmpeg binary, i.e. the environment, not the
      function under test)

## Stage 9. Run unit tests and verify state (MANDATORY — agent executes)

- [x] 9.1 Baseline recorded on this branch by stashing the four tracked backend edits and
      re-running with the new test files excluded: **33 failed, 1029 passed, 120 skipped,
      3 errors**
- [x] 9.2 Targeted suites run: 89 new tests, all green (see the table in the test report)
- [x] 9.3 Full suites run and compared as SETS, not counts. Backend with this change:
      **33 failed, 1086 passed, 120 skipped, 3 errors**. `comm` on the two FAILED lists returns
      **empty in both directions** — zero new failures, zero resolved. The +57 passes are exactly
      this change's new backend tests. Bridge: 83 passed, 2 failed, both pre-existing (see 8.2)
- [x] 9.4 **Database state: N/A, stated rather than skipped.** This change adds no migration,
      table, column, bucket or row (spec.md §7); v1 streams audio and persists nothing. No DB
      indicator was captured because there is none to capture
- [x] 9.5 Test report written: `reports/2026-09-09-test-run.md`

## Stage 10. Manual endpoint testing (MANDATORY — agent executes)

- [x] 10.1 Backend booted locally on `127.0.0.1:8099` using **`apps/backend/.venv`** — the global
      interpreter cannot boot this app at all (see FU.4). Confirmed via `GET /openapi.json` that
      `/internal/whatsapp/voice-note` is genuinely **mounted in the assembled app**, next to the two
      pre-existing internal routes. The unset-key 503 path is covered by `test_voice_endpoint_auth`;
      the live run used a key set so the auth-ordering check below was possible
- [x] 10.2 Wrong header → **401**, absent header → **401**, both with
      `{"detail":"Invalid internal API key"}`. The unknown-lead 404 was NOT exercised live: with
      `VOICE_ENABLED=false` the request correctly stops at the flag before reaching the lead lookup,
      and turning voice on would have meant another ~5-minute boot for a case
      `test_voice_endpoint_auth` already covers
- [x] 10.3 Valid key + `VOICE_ENABLED=false` → **503** `{"detail":"Voice is disabled"}`. This is
      the production behaviour this whole change ships. Also confirmed **auth precedes the flag**:
      wrong key with the flag off returns 401, not 503, so an unauthenticated caller cannot probe
      whether voice is enabled
- [x] 10.4 Attempted and **did not produce the intended check** — recorded rather than quietly
      dropped. `POST /api/v1/channels/whatsapp/leads/fake/reply` returned **500**, for two reasons
      that are both about the environment and pre-existing code, not this change: locally
      `AUTH_ENFORCED=False` so nothing rejected the unauthenticated call, and `lead_exists()` then
      passed the non-UUID `"fake"` straight to Postgres
      (`22P02: invalid input syntax for type uuid`). Getting a real `voice_allowed` over HTTP needs a
      provisioned lead and a valid token — deferred to Stage 11.5 against production. The field's
      behaviour is covered by `test_whatsapp_reply_voice_allowed.py` (6 tests). Logged as FU.5
- [x] 10.5 **Playwright/E2E: not applicable** — this change touches no frontend surface. Marked
      with its reason rather than left blank
- [x] 10.6 Every command and its status code recorded in `reports/2026-09-09-test-run.md`,
      including the one that failed

## Stage 11. Deploy to Production (MANDATORY — CLOSES THE LOOP)

See: `DEPLOYMENT_STAGE/DEPLOYMENT_STAGE.md`

Project-specific details:
- Deploy branch: main
- Frontend URL: https://contexia.online/app/bunker
- Backend URL: https://antigravity-app-production-175a.up.railway.app

Tasks:
- [ ] 11.1 git commit + push to main
- [ ] 11.2 Vercel build complete (green) — no frontend change expected, confirm no regression
- [ ] 11.3 Railway deploy active (backend change: new router + config)
- [ ] 11.4 Production URL: verify `GET /api/v1/health` is up, and that
      `POST /internal/whatsapp/voice-note` returns **503** in production (because `VOICE_ENABLED`
      is false there). **A 503 is the expected, correct production result for this change** — it is
      what "shipped and switched off" looks like
- [ ] 11.5 Confirm the existing WhatsApp text path still works end to end — voice must be provably
      additive
- [ ] 11.6 Create report: `reports/2026-XX-XX-deployment.md`

## Stage 12. Documentation (MANDATORY)

- [x] 12.1 `ARCHITECTURE.md`: add the VoiceBox container row (local/on-prem, same sovereignty
      principle as Decisiones #1/#10/#20/#22)
- [x] 12.2 `ARCHITECTURE.md`: add settled Decision #24 — synthesis local, delivery via
      `/internal/*`, voice additive to text, one owner for the safety gate
- [x] 12.3 `ARCHITECTURE.md`: **correct Decisión #21** — the live Hermes config is
      `AppData\Local\hermes\profiles\contexia\config.yaml` (not `~/.hermes/config.yaml`) and its
      `fallback_providers` are gemini + openrouter, with no OmniRoute entry at `localhost:20128`
- [x] 12.4 `docs/integrations/voicebox.md` — install, real API contract from 1.1, the Phase 0
      engine table, and the migration-day runbook
- [x] 12.5 `apps/chatwoot-bridge/README.md` — voice section and the one-variable rollback
- [x] 12.6 `feature_list.json` — add to `pending_implementation` and to `features` with
      `status: pending`; `active` left as `pricing-quote-engine`. JSON validated after the edit
- [ ] 12.7 Raise the `.claude/skills` drift with the founder before editing CLAUDE.md §6. §6 says
      agent-specific paths reference `ai-specs` "through symlinks when possible", but in this
      checkout every `.claude/skills` entry is a git-tracked regular file that duplicates its
      `ai-specs` source byte for byte, and `.cursor/` does not exist. Either the doc should describe
      the copy-plus-drift-check reality (as `DEPLOYMENT_STAGE/` already does in §8), or the repo
      should genuinely move to symlinks — that is a founder decision, not a silent edit. Do **not**
      "fix" it by converting the tree to symlinks: Windows symlinks need elevated rights or
      Developer Mode, and would change what every collaborator's clone gets

## Known follow-ups (not fixed here, deliberately)

- [ ] FU.1 **Fire-and-forget tasks are not strongly referenced.** `asyncio.create_task(...)` keeps
      only a weak reference, so a task can in principle be garbage-collected mid-await. Both
      `_auto_tag_chatwoot` (pre-existing) and the new `_send_voice_reply` in
      `apps/chatwoot-bridge/main.py` have this shape. The new code copies the existing pattern on
      purpose — matching the surrounding code beats introducing a second idiom for the same
      concern — but the fix (a module-level `set` holding references, discarded on completion)
      should be applied to **both** at once, not just the new one. Low impact for voice (a dropped
      voice note is a non-event) and higher for tagging, which is the real reason to fix it.
- [ ] FU.2 **`TestClient` is broken repo-wide.** httpx 0.28.1 removed the `app=` shortcut that
      starlette 0.27.0's TestClient still passes, so every `TestClient(app)` raises
      `TypeError: Client.__init__() got an unexpected keyword argument 'app'`. Pre-existing and
      unrelated to this change; the voice tests await endpoint coroutines directly to sidestep it.
      Fixing it means bumping starlette (or pinning httpx < 0.28) and re-running everything.
- [ ] FU.5 **A non-UUID `lead_id` returns 500 instead of 404.** `lead_exists()` passes the value
      straight to Postgres, which raises `22P02: invalid input syntax for type uuid`. Found live
      during Stage 10 on the pre-existing `POST /channels/whatsapp/leads/{id}/reply`. The new voice
      endpoint calls the same `lead_exists()` and would behave identically. Left consistent with the
      existing endpoint rather than fixed in one of the two call sites — fix both together, by
      validating the UUID shape before the lookup. Low practical impact: the bridge only ever passes
      an id it received from `whatsapp-intake`.
- [ ] FU.4 **The backend's default test interpreter cannot boot the backend.** The global
      Python 3.11 has pydantic 2.13.4 against fastapi 0.104.1, and importing `main` dies at line 7
      with `AttributeError: 'FieldInfo' object has no attribute 'in_'`. `apps/backend/.venv` pins
      pydantic 2.5.0 and works; that is also what `requirements.txt` resolves for Railway, so
      production is fine. But it means a green `py -3.11 -m pytest` run is weaker evidence than it
      appears — it tests against a pydantic production never sees. Either pin the global env or make
      the venv the documented test interpreter. (This change's fast suites were re-run under the
      venv to compensate; the bridge already runs on the global interpreter in production, per
      `run_bridge.ps1:53`.)
- [ ] FU.3 **Importing the backend costs ~5 minutes.** Module import triggers KB/pgvector seeding
      that tries every embedding provider and waits out their timeouts
      (`KB[pgvector]: skipped 48/48 chunks ... all providers unavailable`). Import-time network I/O
      makes every endpoint test unusably slow and would slow cold starts in production too.
      Pre-existing; worth its own change.

## Founder prerequisites (non-code, blocking before the flag is ever enabled)

- [ ] F.1 **Written consent from Tatiana Barbosa** for the cloned voice — dated, revocable, scoped
      to Contexia, stored outside the repo. During Phase 0 her cloned voice was made to say abusive
      sexual text; she is a real, licensed professional
- [ ] F.2 Decide where the consent record lives (signed document + Bitwarden reference). No value,
      credential or PII goes into a versioned file
