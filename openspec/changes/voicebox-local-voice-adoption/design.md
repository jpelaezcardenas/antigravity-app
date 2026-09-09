# Design — voicebox-local-voice-adoption

## Verified starting state (2026-09-08)

Everything below was read off disk, not assumed.

### VoiceBox

| Fact | Value |
|---|---|
| Installed at | `C:\Program Files\Voicebox\` — `voicebox.exe`, `voicebox-server.exe` (513 MB), `voicebox-mcp.exe` (21 MB) |
| Upstream / licence | `jamiepine/voicebox`, MIT |
| Founder's repo | `jpelaezcardenas/voicebox` — private, real content (created 2026-09-01, 111 MB, branch `main`), but **not a GitHub fork** (`isFork:false`, `parent:null`), so it inherits no upstream updates |
| Local clone | `C:\Users\contexia\voicebox\` is a **broken clone**: 58 MB of objects, `HEAD` pointing at `refs/heads/.invalid`, no refs, no working tree, and a remote pointing at upstream instead of the private mirror |
| API | `:17493` — full contract captured live on 2026-09-08 from `GET /openapi.json`; recorded in `ai-specs/skills/contexia-voice-tts/references/api.md` |
| Backends | MLX, CUDA, ROCm, DirectML, Intel IPEX, CPU fallback. Docker and headless modes exist. |
| Server state right now | **Running** — `voicebox-server.exe` PID 1152, 1.8 GB resident, `qwen-tts-1.7B` loaded (the rejected model), `qwen-tts-0.6B` downloaded but not loaded |
| Cloned voice | The **"Taty" profile survives** — `voice_type: cloned`, `language: es`, `default_engine: qwen`, 1 sample, 8 generations, created 2026-09-05. Name has a stray trailing space (`"Taty "`) |

**Three API facts that invalidate assumptions taken from the README.** They are the reason Stage 1
exists before any code:

1. **`POST /generate` returns JSON, not audio.** It answers with a `GenerationResponse` carrying
   `id`, `status` and `error`; the bytes come from a second call, `GET /audio/{id}`. A 200 with a
   non-empty `error` is a failed generation.
2. **Both important request defaults are wrong for Contexia.** `language` defaults to `en` and
   `model_size` defaults to `1.7B` — the model Phase 0 measured at 30-60 minutes per phrase. A
   request that omits them produces English speech from the slowest model.
3. **`GET /profiles/{id}/export` and `POST /profiles/import` exist.** The migration to the inference
   node must therefore *export the validated clone*, not re-clone from the reference audio — a
   re-clone yields a different voice than the one Phase 0 approved. The profile id will differ per
   machine, which is why it is an environment variable and never a constant.

### Hermes

- **Live config:** `C:\Users\contexia\AppData\Local\hermes\profiles\contexia\config.yaml`
  (`active_profile` = `contexia`). **Not** `~/.hermes/config.yaml` — that directory holds only a
  stale `.txt`, an empty venv and three old profiles.
- `tts:` block with 11 built-in providers; `stt:` block with `enabled: true`, `provider: local`,
  `model: base`, `language: español`. `tts` and `stt` are built-in agent toolsets.
- Never used: both `audio_cache/` directories are empty, `voice.auto_tts: false`.
- Current defaults are wrong for this product: `tts.provider: edge` (cloud) with voice
  `en-US-AriaNeural` (English), and `privacy.redact_pii: false`.
- **Extension point:** `tools/tts_tool.py:750-800` documents
  `tts.providers.<name>: {type: command}` with placeholders `{input_path}`, `{output_path}`,
  `{format}`, `{voice}`, `{model}`, `{speed}`; output formats include `ogg`/`opus`; default timeout
  120 s. Built-in names always win, and `voicebox` collides with none of them.
- `mcp_servers:` currently holds `context7` and `supabase`.

### The voice path in this repo

- Outbound is text-only: `channels/whatsapp.py:132` hardcodes `"type": "text"`.
- Reusable in mirror image: `channels/whatsapp.py:165 download_whatsapp_media()` already implements
  the Graph two-step (metadata then bytes); sending is the same shape reversed.
- Inbound audio is deliberately refused: `apps/chatwoot-bridge/main.py:51,170`, and
  `channels/whatsapp.py:98` normalises only `document`/`image`.
- `/internal/*` precedent: `main.py:252-263` mounts machine-to-machine routers authenticated by
  `INTERNAL_API_KEY`, which fails closed with 503 when unset
  (`presentation/ingest_file_endpoints.py:28-34`), outside `vercel.json`'s rewrite.

## Decision 1 — Where synthesis runs, and who delivers

**Problem.** The backend runs on Railway (cloud). VoiceBox will run on the local inference node.
Railway cannot reach `http://127.0.0.1:17493`. And Chatwoot cannot deliver to WhatsApp: its channel
never sees a genuine customer inbound (the durable-inbox poller mirrors messages as *private notes*,
because a real `incoming` is rejected 422 on a real-provider inbox), so its 24-hour-window
bookkeeping always believes the window is closed and Meta rejects every outgoing message it tries.
This is documented from a live finding on 2026-08-12 in `backend_client.py:85-101`.

**Options considered.**

| Option | Verdict |
|---|---|
| Railway calls VoiceBox directly | Impossible — no route to a local service |
| Expose VoiceBox through a tunnel | Rejected. A Cloudflare tunnel was already evaluated and rejected for WhatsApp ingress; putting a local GPU service on the internet is strictly worse |
| Bridge synthesises, Chatwoot delivers | **This was the previous session's plan and it does not work** — Chatwoot's send is rejected by Meta, as above |
| **Bridge synthesises locally, backend delivers via Graph** | **Chosen** |

**Chosen flow.**

```
Meta webhook --> Railway /api/v1/channels/whatsapp/webhook --> durable inbox
                                                                    | pull
                    local bridge (inbox_poller) <-------------------+
                              |
                              +--> POST /leads/{id}/reply  (deliver=True)
                              |       +--> TEXT to the phone (Graph, unchanged)
                              |       +--> response now also carries `voice_allowed: bool`
                              |
                              +--> if VOICE_ENABLED and voice_allowed:
                              |       VoiceBox 127.0.0.1:17493 /generate --> WAV
                              |       ffmpeg --> OGG/Opus                     [100% LOCAL]
                              |
                              +--> POST /internal/whatsapp/voice-note   (INTERNAL_API_KEY)
                                      +--> Railway: Graph media upload --> type:audio send
                                              +--> VOICE NOTE to the phone
```

Trade-off accepted: the finished audio does transit Railway. That is the same trust boundary the
text reply already crosses, and Railway already holds `WHATSAPP_TOKEN`. What stays local is the
thing that matters — the model, the cloned voice profile, and the synthesis itself.

## Decision 2 — Voice is additive, never a replacement

The text reply is always sent and always mirrored into Chatwoot as a private note. Voice is an
extra artefact on top.

Rationale: Decisión #19 recorded, twice, that without KB grounding the model invents fiscal figures
and contact details with total confidence. A spoken figure is harder to dispute than a written one
and leaves nothing for the human operator to quote back. Removing the text would remove the audit
trail exactly where it is most needed.

## Decision 3 — One owner for the safety gate

`services/voice_safety.py::should_speak(text) -> bool` lives in the backend. Its verdict reaches the
bridge as an additive `voice_allowed` field on the existing `/leads/{lead_id}/reply` response.

Why not in the bridge: the bridge is local and modifiable, and duplicating the rule in two places of
the same system is exactly the repeated-pattern smell CLAUDE.md §1 asks us to flag. Why not a second
round trip: the reply call already exists and already returns a dict; extending it follows the same
additive convention as `conversation_history`/`lead_context` in Decisión #19. Consequence: the
bridge spends no GPU time on a reply that would be discarded.

`should_speak` returns `False` when the text:

- exceeds `VOICE_MAX_CHARS` (default 320 — a voice note should be short);
- contains a numeric fiscal claim: `$`, `%`, `UVT`, or digits followed by `mil`/`millones`;
- contains a deadline-shaped date.

The endpoint re-runs `should_speak` on the accompanying text before sending, as defence in depth
against a modified or stale bridge.

## Decision 4 — Hermes integration: `type: command` vs MCP

Two viable paths, decided in Stage 1 with the binary in hand rather than prejudged here:

- **`tts.providers.voicebox: {type: command}`** — zero Python, uses the documented extension point,
  slots into the existing `tts` toolset. Needs a small wrapper script because the command has to
  build VoiceBox's JSON body (`text`, `language`, `profile_id`), which a raw one-liner does badly.
- **MCP server** — `voicebox-mcp.exe` and `GET /mcp` already exist; registering it under
  `mcp_servers:` alongside `context7`/`supabase` would give Hermes agents native voice tools rather
  than a TTS backend. Likely the better fit for "daily agent use", but it changes the tool surface
  the agents see, so it deserves a real look before committing.

Either way `tts.provider` is **not** switched to `voicebox` in this change: with no server running,
every call would fail. The switch is a migration-day action.

## Decision 5 — No persistence in v1

Audio bytes are generated, sent, and dropped. Nothing is written to Supabase Storage and no table is
added. Less PII at rest, no migration, and rollback stays a single environment variable. If
persistence is ever justified, the pattern to copy is `services/document_storage_service.py`
(private bucket, stable path, signed URLs generated on demand and never persisted).

## Decision 6 — Fix the router-registration `try/except` first

`main.py:252-263` wraps internal-router registration in a `try/except` that logs and continues.
Decisión #22 already classified this exact construct as **a failure, not a warning**, after it
swallowed a `NameError` and left both `/internal/*` routes unregistered while the app started
normally. This change mounts a third router there. Making it fail loud is a precondition, not a
side quest — otherwise a broken voice router would silently produce a backend that looks healthy
and drops every voice note.

## Dependencies

- **ffmpeg** on the local bridge host, for WAV to OGG/Opus. WhatsApp will not play a WAV as a voice
  note. Absence is handled as a soft failure (log and skip voice), never an exception.
- **VoiceBox server** on the inference node. Absent today; that is the point.
- No new Python dependency in the backend — `httpx` is already used throughout.

## Out of scope (explicitly)

- Inbound STT, the Búnker microphone, Telegram voice, audio persistence, any cloud TTS provider,
  and actually enabling the feature. See `proposal.md` § Non-goals.
- Reconciling Hermes' `tts.provider: edge` default to a Spanish voice as a stopgap. It would work
  on this laptop today, but it sends client text to Microsoft — the exact sovereignty problem this
  change exists to avoid. Flagged in the docs, deliberately not done.
