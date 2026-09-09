# VoiceBox — local voice for Contexia

**Status: shipped and switched OFF.** Every piece below is merged and tested; nothing is enabled.
`VOICE_ENABLED` defaults to `false` on both the backend and the local bridge. Turning voice on is
a configuration change on the inference node, not a development task.

Change record: `openspec/changes/voicebox-local-voice-adoption/`.

## What it is

[VoiceBox](https://github.com/jamiepine/voicebox) (MIT) is a local-first voice studio: TTS with
voice cloning, STT, a REST API on `:17493`, and an MCP server. Contexia uses it as the **only**
voice provider, entirely on-premise — the model, the cloned voice profile and the customer's text
never leave the machine, the same sovereignty principle that keeps Hermes, GBrain and the
Siigo/Gmail pollers local (ARCHITECTURE.md Decisiones #1/#10/#20/#22).

The founder's copy is `jpelaezcardenas/voicebox` — **private, and not a GitHub fork**
(`isFork:false`, `parent:null`). It inherits no upstream updates automatically; add
`jamiepine/voicebox` as a second remote to track them.

## Why the bridge synthesises and the backend delivers

Two constraints meet, and only one arrangement satisfies both:

1. The backend runs on **Railway** and cannot reach a VoiceBox listening on the inference node's
   `127.0.0.1:17493`. Synthesis cannot happen there.
2. **Chatwoot cannot deliver to WhatsApp.** Its channel never sees a genuine customer inbound — the
   durable-inbox poller mirrors messages in as *private notes*, because a real `incoming` is
   rejected 422 on a real-provider inbox — so its 24-hour-window bookkeeping always believes the
   window is closed and Meta rejects everything it tries to send. Found live 2026-08-12; see
   `apps/chatwoot-bridge/backend_client.py:85-101`. Delivery cannot happen locally.

```
Meta webhook --> Railway /api/v1/channels/whatsapp/webhook --> durable inbox
                                                                    | pull
                    local bridge (inbox_poller) <-------------------+
                              |
                              +--> POST /leads/{id}/reply  (deliver=True)
                              |       +--> TEXT to the phone (Graph, unchanged)
                              |       +--> response carries `voice_allowed: bool`
                              |
                              +--> if VOICE_ENABLED and voice_allowed:
                              |       VoiceBox /generate --> /audio/{id} --> WAV
                              |       ffmpeg --> OGG/Opus                  [100% LOCAL]
                              |
                              +--> POST /internal/whatsapp/voice-note  (INTERNAL_API_KEY)
                                      +--> Railway: Graph media upload --> type:audio send
                                              +--> VOICE NOTE to the phone
```

No tunnel: a Cloudflare tunnel was already evaluated and rejected for WhatsApp ingress, and
exposing a local GPU service to the internet would be worse. Only the finished audio crosses to
Railway — the same trust boundary the text reply already crosses, and Railway already holds
`WHATSAPP_TOKEN`.

## Two rules that are not negotiable

**Voice never replaces text.** The text reply is always sent and always mirrored into Chatwoot as a
private note. Decisión #19 documented the model inventing fiscal figures with total confidence; a
spoken figure is harder to dispute and leaves the human operator nothing to quote back.

**Voice never speaks a fiscal figure.** `apps/backend/services/voice_safety.py::should_speak()` is
the single owner of that decision and rejects any text containing a currency marker, a percentage,
a UVT reference, a spelled magnitude (`mil`/`millones`) or a day/month deadline — plus anything
over `VOICE_MAX_CHARS`. Its verdict reaches the bridge as an additive `voice_allowed` field on the
reply response, so the rule lives in exactly one place and the bridge cannot drift from it or spend
GPU time on a reply that would be discarded. The voice-note endpoint re-applies the same gate as
defence in depth.

## The API — verified contract

Captured 2026-09-08 from the running server's own `GET /openapi.json`, not from the README. Full
detail in `ai-specs/skills/contexia-voice-tts/references/api.md`.

**`POST /generate` does not return audio.** It returns a JSON `GenerationResponse` with `id`,
`status` and `error`; the bytes come from `GET /audio/{id}`. A 200 carrying a non-empty `error` is a
failed generation.

Two request defaults are traps — omit them and you get **English** speech from the **slowest**
model:

| Field | VoiceBox default | Contexia must send |
|---|---|---|
| `language` | `en` | `es` |
| `model_size` | `1.7B` | `0.6B` |

`personality` stays `false`: an in-character rewrite would change text the safety gate already
judged.

## Engines

Measured 2026-09-05 on an i7-1165G7, 16 GB, **CPU-only**. Full table in
`ai-specs/skills/contexia-voice-tts/references/fase0-benchmark.md`.

| Engine | Clones? | CPU latency | Verdict |
|---|---|---|---|
| **Qwen3-TTS 0.6B** | **yes, validated on Tatiana** | ~3-5 min | **selected** |
| Kokoro 82M | no | ~30 s | cannot be Taty |
| Chatterbox Multilingual | yes | ~3-5 min | works, not selected |
| Chatterbox Turbo | — | — | **blocked**: `Cannot copy out of meta tensor` |
| Qwen3-TTS 1.7B | yes | ~30-60 min | unusable on CPU |
| LuxTTS | yes | ~2-3 min | works, quality unevaluated |

Do not load several engines at once — four concurrent engines exceeded 16 GB RAM, and that swapping
is what looked like a hang during Phase 0.

## Configuration

**Backend** (`apps/backend/config.py`): `VOICE_ENABLED=false`, `VOICE_MAX_CHARS=320`,
`VOICE_MAX_AUDIO_BYTES=16777216`. `INTERNAL_API_KEY` is read from the environment by the endpoint
and fails closed with a 503.

**Bridge** (`apps/chatwoot-bridge/.env`, see `.env.example`): `VOICE_ENABLED=false`,
`VOICEBOX_URL`, `VOICEBOX_PROFILE_ID` (empty = unavailable, never guessed), `VOICEBOX_ENGINE=qwen`,
`VOICEBOX_MODEL_SIZE=0.6B`, `VOICEBOX_LANGUAGE=es`, `VOICEBOX_TIMEOUT_SECONDS=120`,
`INTERNAL_API_KEY`.

**Hermes** (`%LOCALAPPDATA%\hermes\profiles\contexia\config.yaml`) — add the provider, leave
`tts.provider` alone:

```yaml
tts:
  provider: edge            # migration day: voicebox
  providers:
    voicebox:
      type: command
      command: 'powershell -NoProfile -ExecutionPolicy Bypass -File C:/Users/contexia/Projects/antigravity-app/apps/hermes-voicebox/voicebox_tts.ps1 -InputPath {input_path} -OutputPath {output_path}'
      output_format: ogg
```

Requires `ffmpeg` on the bridge host for WAV to OGG/Opus. Without it the bridge degrades to
text-only and logs; it never crashes.

> **Note on Hermes' current defaults.** `tts.provider` is `edge` with the voice `en-US-AriaNeural`:
> a **cloud** provider speaking **English**, with `privacy.redact_pii: false`. Hermes' TTS has never
> actually been used (both `audio_cache/` directories are empty), so nothing is leaking today — but
> do not "fix" the language by picking a Spanish Edge voice as a stopgap. That would send client
> text to Microsoft, which is the exact problem this integration exists to avoid.

## Migration-day runbook

1. Install VoiceBox on the inference node and start it with CUDA (`voicebox-server.exe`, or
   `docker compose up`).
2. **Verify Tatiana's written consent is on file.** Dated, revocable, scoped to Contexia. If it is
   not, stop here — see below.
3. **Export the validated voice, do not re-clone it:** `GET /profiles/{id}/export` on the old
   machine, `POST /profiles/import` on the new one. A re-clone from the reference audio produces a
   *different* voice than the one Phase 0 approved. Record the new `profile_id` — it differs per
   machine, which is why it is an environment variable.
4. Unload `qwen-tts-1.7B` and load `qwen-tts-0.6B` (`POST /models/load`) before measuring anything,
   or the numbers describe the wrong model.
5. Measure real latency. **Acceptance threshold: < 15 s per reply.** Above that a voice note arrives
   late enough to annoy — do not enable.
6. Hermes: set `tts.provider: voicebox`.
7. Bridge `.env`: `VOICE_ENABLED=true`, `VOICEBOX_PROFILE_ID=<new id>`, `INTERNAL_API_KEY=<...>`.
8. Railway: `VOICE_ENABLED=true`, `INTERNAL_API_KEY` if not already set.
9. End-to-end test against **your own** number before any customer.

Rollback at any point: `VOICE_ENABLED=false`, restart. No migration, no table, no persisted audio —
nothing to undo.

## Blocking prerequisite

**Written consent from Tatiana Barbosa for the cloned voice** — dated, revocable, scoped to
Contexia, stored outside this repository. She is a real, licensed accountant (Entidad A), and
during Phase 0 validation her cloned voice was made to say abusive sexual text. The flag does not
get enabled without her consent on file. No credential or PII value is ever written into a
versioned file (Decisión #12).

## Out of scope

Inbound audio (customers' voice notes are still refused; `LOCAL_WHISPER_URL` remains a documented,
unused placeholder), the Búnker microphone (`hermes-jarvis-contexia` Fase 2), Telegram voice, and
persisting audio — v1 streams bytes and stores nothing.
