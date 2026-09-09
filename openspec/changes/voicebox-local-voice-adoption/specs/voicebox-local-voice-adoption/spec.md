# Spec — voicebox-local-voice-adoption

## 1. Configuration

### 1.1 Backend (`apps/backend/config.py`)

| Variable | Type | Default | Meaning |
|---|---|---|---|
| `VOICE_ENABLED` | bool | `False` | Master switch for the outbound voice-note path. Fails closed. |
| `VOICE_MAX_CHARS` | int | `320` | Longest reply the safety gate will allow to be spoken. |
| `VOICE_MAX_AUDIO_BYTES` | int | `16777216` | Hard cap on an accepted voice-note payload (16 MB, WhatsApp's audio limit). |

`INTERNAL_API_KEY` is read from the environment by the endpoint itself, matching
`presentation/ingest_file_endpoints.py` — it is not added to `Settings`.

### 1.2 Bridge (`apps/chatwoot-bridge/config.py`)

| Variable | Type | Default | Meaning |
|---|---|---|---|
| `VOICE_ENABLED` | bool | `False` | Master switch on the local side. Both switches must be on. |
| `VOICEBOX_URL` | str | `http://127.0.0.1:17493` | Local VoiceBox REST base. |
| `VOICEBOX_PROFILE_ID` | str | `""` | Cloned-voice profile id. Empty means voice is unavailable — never guessed. |
| `VOICEBOX_ENGINE` | str | `qwen` | VoiceBox's `engine` field. Verified against the live API — it is `qwen`, not an engine slug. |
| `VOICEBOX_MODEL_SIZE` | str | `0.6B` | VoiceBox's `model_size` field. **The API default is `1.7B`**, the model Phase 0 rejected as unusable, so this must always be sent explicitly. |
| `VOICEBOX_LANGUAGE` | str | `es` | **The API default is `en`** — must always be sent explicitly. |
| `VOICEBOX_TIMEOUT_SECONDS` | int | `120` | Matches Hermes' own command-TTS default. |
| `INTERNAL_API_KEY` | str | `""` | Sent to the backend's `/internal/*` surface. |

`LOCAL_WHISPER_URL` is left untouched — it stays the documented, unused inbound-STT placeholder.

## 2. Safety gate — `apps/backend/services/voice_safety.py`

```python
def should_speak(text: str, max_chars: int) -> bool
```

Pure function, no I/O, no network.

Returns `False` when any of the following holds; `True` otherwise:

| Rule | Rejects |
|---|---|
| Empty or whitespace-only | `""`, `"   "` |
| Longer than `max_chars` | any reply over the limit |
| Currency symbol | text containing `$` |
| Percentage | text containing `%` |
| UVT reference | `UVT` in any casing |
| Spelled magnitude | digits followed by `mil` / `millon` / `millones` |
| Deadline-shaped date | `dd/mm`, `dd-mm`, or `<day> de <month-name>` |

Rationale for each rejection class is one thing: ARCHITECTURE.md Decisión #19 established that the
model fabricates fiscal figures confidently. Text keeps a quotable record; speech does not.

**Non-requirement:** this gate is not a content-safety classifier. It does not attempt to detect
abusive input. Abuse is prevented upstream — voice only ever speaks a reply Taty generated for a
real lead, never operator free-text — and by the consent and HITL requirements in `proposal.md`.

## 3. Backend — outbound WhatsApp audio

### 3.1 `channels/whatsapp.py`

```python
async def upload_whatsapp_media(content: bytes, mime_type: str) -> Optional[str]
```

`POST {GRAPH_API_BASE}/{WHATSAPP_PHONE_NUMBER_ID}/media`, multipart with
`messaging_product=whatsapp`, `type=<mime_type>`, `file=<content>`.

- Returns the Graph `id` on 200.
- Returns `None` when `WHATSAPP_TOKEN` / `WHATSAPP_PHONE_NUMBER_ID` are unset — logs
  "not configured" and makes **no** network call, exactly like `send_whatsapp_message`.
- Returns `None` and logs on any non-200 or exception. Never raises.

```python
async def send_whatsapp_audio(to: str, media_id: str) -> bool
```

`POST {GRAPH_API_BASE}/{phone_number_id}/messages` with body
`{"messaging_product": "whatsapp", "to": to, "type": "audio", "audio": {"id": media_id}}`.

Same contract: `False` when unconfigured or failed, never raises.

### 3.2 `presentation/voice_endpoints.py` (new)

```
POST /internal/whatsapp/voice-note
```

Not under `/api/v1`, therefore not exposed by `vercel.json`'s rewrite.

**Auth:** `X-Internal-Api-Key` header compared against the `INTERNAL_API_KEY` environment variable,
copying `ingest_file_endpoints.py:28-34`.

Checks run in this exact order, and the order is part of the contract:

| # | Condition | Status |
|---|---|---|
| 1 | `INTERNAL_API_KEY` unset in the environment | **503** — "Internal API key not configured" (fail closed) |
| 2 | Header missing or mismatched | **401** |
| 3 | `VOICE_ENABLED` is `False` | **503** — "Voice is disabled" |
| 4 | `mime_type` is not `audio/ogg` | **415** |
| 5 | `audio_base64` does not decode, or decodes to nothing | **400** |
| 6 | Payload larger than `VOICE_MAX_AUDIO_BYTES` | **413** |
| 7 | `should_speak(text)` is `False` | **422** — the bridge should not have asked |
| 8 | `lead_id` unknown (`lead_exists` is False) | **404** |
| 9 | Lead has no phone, or upload/send fails | **200** with `{"sent": false, "reason": ...}` |
| 10 | Sent | **200** with `{"sent": true}` |

Two ordering choices worth stating:

* **Auth precedes the feature flag**, so an unauthenticated caller cannot probe whether voice is
  enabled by telling 401 from 503.
* **The lead lookup is last.** It is the only database call on this path, so every cheap rejection
  runs first; it also means a caller sending a malformed or unspeakable payload never learns
  whether a lead id exists.

Request body: `{"lead_id": str, "text": str, "audio_base64": str, "mime_type": str}`.
`mime_type` must be `audio/ogg` — anything else is **415**.

The delivery failure returning 200 rather than 5xx is deliberate and matches
`taty_lead_reply`'s existing stance: a failed voice delivery is not the request's failure, and the
bridge must not retry a send that already reached Meta.

### 3.3 `presentation/whatsapp_endpoints.py`

`taty_lead_reply` adds exactly one field to its response dict:

```python
result["voice_allowed"] = should_speak(result.get("reply") or "", settings.VOICE_MAX_CHARS)
```

Computed **after** `sanitize_for_whatsapp`, so the gate judges the text that will actually be
spoken. Additive: every existing caller and field is unchanged.

### 3.4 `main.py`

Internal-router registration stops swallowing exceptions. The `voice_endpoints` router joins
`siigo_sync` and `ingest_file` under `/internal`. An import or registration failure must abort
startup, not log and continue (Decisión #22).

## 4. Bridge — local synthesis

### 4.1 `voicebox_client.py` (new)

```python
async def synthesize(text: str) -> Optional[bytes]
```

**Two calls, not one.** Verified against the live server's OpenAPI on 2026-09-08: `POST /generate`
returns a JSON `GenerationResponse`, **not audio**.

1. `POST {VOICEBOX_URL}/generate` with the full body — `profile_id` and `text` are required, and
   `language`, `model_size` and `engine` must all be sent explicitly because the API defaults
   (`en`, `1.7B`) are both wrong for Contexia:
   ```json
   {"profile_id": "...", "text": "...", "language": "es",
    "engine": "qwen", "model_size": "0.6B", "personality": false}
   ```
   `personality` stays `false`: an in-character rewrite would change the text after the safety gate
   judged it.
2. Read `id`, `status` and `error` from the response. A 200 carrying a non-empty `error` is a
   **failed** generation, not a success.
3. `GET {VOICEBOX_URL}/audio/{id}` for the bytes.

- Returns audio bytes on success.
- Returns `None` when `VOICEBOX_PROFILE_ID` is empty — never calls with a guessed profile.
- Returns `None` and logs on timeout, non-200, a non-empty `error`, or any exception. Never raises —
  same fail-soft contract as `backend_client.whatsapp_intake`.

**Unverified at spec time:** the exact `Content-Type` of `GET /audio/{id}` (the OpenAPI document
declares an untyped `application/json`, which usually indicates a `FileResponse`). Confirm it in
task 5.1 rather than assuming WAV.

### 4.2 `audio_converter.py` (new)

```python
def wav_to_ogg_opus(wav_bytes: bytes) -> Optional[bytes]
```

Runs `ffmpeg -i <in> -c:a libopus -b:a 32k -ar 48000 -ac 1 <out>` through temporary files.

- Returns `None` and logs when ffmpeg is absent or exits non-zero. Never raises.
- OGG/Opus is required: WhatsApp does not play a WAV as a voice note.

### 4.3 `backend_client.py`

```python
async def send_voice_note(lead_id: str, text: str, audio: bytes) -> bool
```

`POST {CONTEXIA_API_URL_ROOT}/internal/whatsapp/voice-note` with the `X-Internal-Api-Key` header.
Note the path is **not** under `/api/v1`, so it derives its base from the API URL's origin rather
than reusing `CONTEXIA_API_URL` directly. Fail-soft: returns `False`, never raises.

### 4.4 `main.py`

At the end of `process_incoming_message`, after the private-note mirror:

```python
if settings.VOICE_ENABLED and (taty_result or {}).get("voice_allowed"):
    asyncio.create_task(_send_voice_reply(lead_id, reply_text))
```

Fire-and-forget, matching `_auto_tag_chatwoot`. `_send_voice_reply` wraps everything in
`try/except` and logs; a voice failure never delays, blocks, or alters the text reply that has
already been delivered.

## 5. Hermes configuration (not applied in this change)

Added to `AppData\Local\hermes\profiles\contexia\config.yaml` as an inert entry:

```yaml
tts:
  providers:
    voicebox:
      type: command
      command: 'pwsh -File <repo>/apps/hermes-voicebox/voicebox_tts.ps1 -InputPath {input_path} -OutputPath {output_path}'
      output_format: ogg
```

`tts.provider` stays `edge` until migration day. The wrapper script is versioned in the repo and
reads `VOICEBOX_PROFILE_ID` from the environment.

The MCP alternative (`voicebox-mcp.exe` / `GET /mcp` registered under `mcp_servers:`) is evaluated
in Stage 1 and may replace this; see `design.md` Decision 4.

## 6. Error cases summary

| Failure | Behaviour |
|---|---|
| VoiceBox not running | `synthesize` returns `None`; no voice; text already delivered |
| ffmpeg missing | conversion returns `None`; no voice; logged once per call |
| `VOICEBOX_PROFILE_ID` empty | no call attempted; no voice |
| `INTERNAL_API_KEY` unset on backend | endpoint returns 503; bridge logs and drops |
| `VOICE_ENABLED=False` anywhere | no VoiceBox call at all; path identical to today |
| Graph upload or send fails | 200 with `sent: false`; no retry |
| Gate rejects the text | no synthesis attempted (bridge saw `voice_allowed: false`) |

## 7. Database

No migration. No new table, column, bucket, or row.
