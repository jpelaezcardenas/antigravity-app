# VoiceBox local API — verified contract

**Captured:** 2026-09-08, from a **live** VoiceBox v0.5.0 server on this machine
(`GET http://127.0.0.1:17493/openapi.json`). Everything below is read from the running server's own
OpenAPI document, not from the README.

Base URL: `http://127.0.0.1:17493` (local only — never exposed to the internet).

## The most important correction

**`POST /generate` does not return audio.** It returns a JSON `GenerationResponse`. The audio is a
separate fetch. Any code written on the assumption that `/generate` streams back a WAV is wrong.

```
POST /generate            -> GenerationResponse (JSON, has `id` + `status` + `audio_path`)
GET  /audio/{generation_id} -> the audio file
GET  /generate/{generation_id}/status -> generation status (for the async case)
```

## POST /generate — `GenerationRequest`

| Field | Type | Default | Notes |
|---|---|---|---|
| `profile_id` | string | **required** | Never guess it. See "Profiles" below. |
| `text` | string | **required** | |
| `language` | string | `en` | **Must be set to `es`** — the default is English. |
| `model_size` | string \| null | **`1.7B`** | **Must be set to `0.6B`.** The default is the model Phase 0 rejected as unusable (~30-60 min per phrase on CPU). |
| `engine` | string \| null | `qwen` | Correct for the selected engine. |
| `seed` | int \| null | — | For reproducible output. |
| `instruct` | string \| null | — | Delivery instruction (e.g. tone). |
| `personality` | bool | `false` | In-character rewrite. Leave off — rewriting the reply text would bypass the safety gate. |
| `max_chunk_chars` | int | `800` | |
| `crossfade_ms` | int | `50` | |
| `normalize` | bool | `true` | |
| `effects_chain` | array \| null | — | |

> The two defaults above are the trap: send a request without `language` and `model_size` and you
> get **English** speech from the **slowest** model.

## GenerationResponse

| Field | Type | Notes |
|---|---|---|
| `id` | string | **required** — use it to fetch the audio |
| `profile_id`, `text`, `language`, `created_at` | | required |
| `status` | string | default `completed` |
| `audio_path` | string \| null | server-side path |
| `duration` | number \| null | seconds |
| `error` | string \| null | populated on failure |
| `engine`, `model_size`, `seed`, `instruct` | | echo of the request |
| `versions`, `active_version_id`, `is_favorited`, `source` | | |

Check `status` and `error` before assuming success — a 200 with `error` set is a failed generation.

## Profiles

```
GET    /profiles                      list
POST   /profiles                      create
GET    /profiles/{id}                 read
GET    /profiles/{id}/export          export  <- use this to move a cloned voice between machines
POST   /profiles/import               import  <- ...and this to restore it
GET/POST /profiles/{id}/samples       reference audio for cloning
```

**The cloned "Taty" profile already exists on this machine** (verified live 2026-09-08):
`voice_type: cloned`, `language: es`, `default_engine: qwen`, 1 sample, 8 generations, created
2026-09-05. Its name carries a stray trailing space (`"Taty "`) — worth fixing.

**Migration consequence:** the profile lives in `AppData\Roaming\sh.voicebox.app\voicebox.db` on
this laptop. Moving to the inference node should use `GET /profiles/{id}/export` +
`POST /profiles/import`, **not** a re-clone from the reference audio. A re-clone produces a
different voice; an export preserves the one that was validated. The profile id will differ on the
new machine, which is exactly why it is an environment variable and never a constant.

## Models

```
GET  /models/status     what is downloaded and what is loaded in RAM
POST /models/load       load one
POST /models/unload     unload one
```

Verified live on this machine (2026-09-08):

| Model | Downloaded | Size | Loaded |
|---|---|---|---|
| `qwen-tts-1.7B` | yes | 4.3 GB | **yes** |
| `qwen-tts-0.6B` | yes | 2.4 GB | no |
| `qwen-custom-voice-1.7B` / `-0.6B` | no | — | no |

Note the machine currently has the **1.7B** model loaded — the one Phase 0 rejected. Unload it and
load `qwen-tts-0.6B` before any latency measurement, or the numbers will be meaningless.

## Other endpoints worth knowing

| Endpoint | Use |
|---|---|
| `GET /health`, `GET /health/filesystem` | liveness |
| `POST /speak` | `SpeakRequest` in, `GenerationResponse` out — the agent-oriented variant |
| `POST /generate/stream` | streaming variant; likely better for latency, unevaluated |
| `POST /generate/{id}/cancel` | cancel a running generation |
| `POST /transcribe` | multipart in, `TranscriptionResponse` out — **STT, out of scope for now** |
| `GET /mcp/bindings`, `PUT /mcp/bindings` | MCP client bindings |
| `GET /tasks/active` | what the server is currently working on |
| `POST /shutdown` | stops the server — do not call it casually |

## Not verified

- The exact content type and body of `GET /audio/{generation_id}` — the OpenAPI document declares
  `application/json` with an untyped schema, which usually means a `FileResponse` the generator
  could not describe. Confirm the real `Content-Type` at implementation time.
- `SpeakRequest` and `TranscriptionResponse` field lists.
- Any latency figure on GPU hardware.
- `POST /generate` was deliberately **not** called during this capture: on this CPU-only laptop it
  costs 3-5 minutes per phrase. Only read-only endpoints were exercised.
