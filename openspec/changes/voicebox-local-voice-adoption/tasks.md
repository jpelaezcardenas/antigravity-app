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
- [ ] 0.4 Repair the local VoiceBox clone: `C:\Users\contexia\voicebox\` holds only a broken `.git`
      (`HEAD` at `refs/heads/.invalid`, no working tree) pointing at upstream. Remove it and clone
      `jpelaezcardenas/voicebox`. Note in the report that it is not a GitHub fork, so upstream must
      be added as a second remote to track updates

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

- [ ] 2.1 Failing tests in `tests/test_voice_safety.py`: a table of texts covering every rejection
      class (empty, over-length, `$`, `%`, `UVT`, `120 mil`, `28 de abril`, `15/04`) plus accepted
      short conversational replies. Pure function, no mocks, no network
- [ ] 2.2 Implement `services/voice_safety.py::should_speak(text, max_chars)`
- [ ] 2.3 Failing test asserting `should_speak` is judged on the sanitised text, then wire
      `voice_allowed` into `taty_lead_reply`'s response **after** `sanitize_for_whatsapp`
- [ ] 2.4 Test asserting every pre-existing field of the `/leads/{id}/reply` response is unchanged
      (additive-only contract)

## Stage 3. Graph outbound audio (TDD, backend)

- [ ] 3.1 Failing test for `upload_whatsapp_media`: asserts the multipart body carries
      `messaging_product=whatsapp` and the file, using `httpx.MockTransport`. **Do not patch the
      function under test** — Decisión #22's rule
- [ ] 3.2 Implement `upload_whatsapp_media` in `channels/whatsapp.py`, mirroring
      `download_whatsapp_media`'s unconfigured-credentials contract (return `None`, no network call)
- [ ] 3.3 Failing test for `send_whatsapp_audio`: asserts `type: "audio"` and `audio.id` in the JSON
- [ ] 3.4 Implement `send_whatsapp_audio`
- [ ] 3.5 Test: with `WHATSAPP_TOKEN` unset, neither function makes a network call

## Stage 4. Internal voice endpoint (TDD, backend)

- [ ] 4.1 Failing tests in `tests/test_voice_endpoint_auth.py`: `INTERNAL_API_KEY` unset → 503;
      wrong header → 401; correct header → past auth
- [ ] 4.2 Failing tests for the rest of the status table in `spec.md` §3.2: unknown lead → 404,
      `VOICE_ENABLED=False` → 503, oversize payload → 413, gate rejects → 422, wrong mime → 415,
      delivery failure → 200 with `sent: false`
- [ ] 4.3 Implement `presentation/voice_endpoints.py`
- [ ] 4.4 Add `VOICE_ENABLED`, `VOICE_MAX_CHARS`, `VOICE_MAX_AUDIO_BYTES` to `config.py`, all
      fail-closed
- [ ] 4.5 **Make `main.py`'s internal-router registration fail loud** (remove the swallowing
      `try/except` at lines 252-263) and mount the voice router. Add a test asserting the app
      exposes all three `/internal/*` routes after startup
- [ ] 4.6 `tests/test_voice_flag_off.py`: with `VOICE_ENABLED=False`, the WhatsApp reply path makes
      **zero** VoiceBox-related calls and returns the same payload as before this change. This is
      the test that certifies the dark launch

## Stage 5. Local bridge (TDD)

- [ ] 5.1 Failing tests for `voicebox_client.synthesize` against a fake httpx transport: success
      returns bytes; empty `VOICEBOX_PROFILE_ID` makes no call; timeout and non-200 return `None`
- [ ] 5.2 Implement `apps/chatwoot-bridge/voicebox_client.py`
- [ ] 5.3 Failing tests for `audio_converter.wav_to_ogg_opus` using a **real small WAV fixture**
      (generated in the test, not an invalid inline blob that would force a mock — the aggravating
      factor Decisión #22 recorded); missing ffmpeg returns `None`
- [ ] 5.4 Implement `apps/chatwoot-bridge/audio_converter.py`
- [ ] 5.5 Implement `backend_client.send_voice_note` with fail-soft contract + its test
- [ ] 5.6 Add the voice settings to the bridge's `config.py` and `.env.example` (names only, never
      values — Decisión #12)
- [ ] 5.7 Wire the fire-and-forget voice step into `main.py::process_incoming_message`, mirroring
      `_auto_tag_chatwoot`; test that a raising voice path does not affect the text reply

## Stage 6. Hermes wiring (inert)

- [ ] 6.1 Add `apps/hermes-voicebox/voicebox_tts.ps1` — builds the `/generate` JSON body, reads
      `VOICEBOX_PROFILE_ID` from the environment, writes to `{output_path}`
- [ ] 6.2 Add the `tts.providers.voicebox` entry (or the `mcp_servers` entry, per Stage 1) to the
      live Hermes profile config. **Leave `tts.provider: edge`** — a switch with no server running
      would fail every call
- [ ] 6.3 Back up the config before editing and verify Hermes still starts afterwards

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

- [ ] 8.1 Review `tests/test_whatsapp_endpoints.py` and `tests/test_whatsapp_channel.py` for
      assertions that break on the additive `voice_allowed` field; update only what genuinely
      changed
- [ ] 8.2 Review `apps/chatwoot-bridge/tests/` for the same
- [ ] 8.3 Confirm no test mocks the boundary it claims to verify (Decisión #22)

## Stage 9. Run unit tests and verify state (MANDATORY — agent executes)

- [ ] 9.1 Record the pre-change baseline on this branch so pre-existing failures are not
      misattributed (main's known baseline is 25F/28E — memory note
      `project_pytest_interpreter_py311`; only py311 has pytest)
- [ ] 9.2 Run the targeted suites: `test_voice_safety`, `test_whatsapp_voice_send`,
      `test_voice_endpoint_auth`, `test_voice_flag_off`
- [ ] 9.3 Run the full backend suite and the bridge suite; compare against 9.1 and record the delta
- [ ] 9.4 **Database state: N/A and stated as such.** This change adds no migration, table, column,
      bucket or row (spec.md §7). Record that no DB indicator was captured *because there is nothing
      to capture*, rather than silently skipping the step
- [ ] 9.5 Write the test report to `reports/2026-XX-XX-test-run.md`

## Stage 10. Manual endpoint testing (MANDATORY — agent executes)

- [ ] 10.1 Start the backend locally with `INTERNAL_API_KEY` unset; `curl` the voice endpoint and
      confirm **503**
- [ ] 10.2 Set the key; `curl` with a wrong header and confirm **401**; with the right header and an
      unknown lead confirm **404**
- [ ] 10.3 With `VOICE_ENABLED=False`, confirm **503** even with valid auth
- [ ] 10.4 `curl` `/leads/{id}/reply` and confirm `voice_allowed` is present and correct for a
      figure-bearing reply vs a plain one
- [ ] 10.5 **Playwright/E2E: not applicable** — this change touches no frontend surface. State the
      reason rather than leaving the step unmarked
- [ ] 10.6 Record every command and its output in the test report

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

- [ ] 12.1 `ARCHITECTURE.md`: add the VoiceBox container row (local/on-prem, same sovereignty
      principle as Decisiones #1/#10/#20/#22)
- [ ] 12.2 `ARCHITECTURE.md`: add settled Decision #24 — synthesis local, delivery via
      `/internal/*`, voice additive to text, one owner for the safety gate
- [ ] 12.3 `ARCHITECTURE.md`: **correct Decisión #21** — the live Hermes config is
      `AppData\Local\hermes\profiles\contexia\config.yaml` (not `~/.hermes/config.yaml`) and its
      `fallback_providers` are gemini + openrouter, with no OmniRoute entry at `localhost:20128`
- [ ] 12.4 `docs/integrations/voicebox.md` — install, real API contract from 1.1, the Phase 0
      engine table, and the migration-day runbook
- [ ] 12.5 `apps/chatwoot-bridge/README.md` — voice section and the one-variable rollback
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

## Founder prerequisites (non-code, blocking before the flag is ever enabled)

- [ ] F.1 **Written consent from Tatiana Barbosa** for the cloned voice — dated, revocable, scoped
      to Contexia, stored outside the repo. During Phase 0 her cloned voice was made to say abusive
      sexual text; she is a real, licensed professional
- [ ] F.2 Decide where the consent record lives (signed document + Bitwarden reference). No value,
      credential or PII goes into a versioned file
