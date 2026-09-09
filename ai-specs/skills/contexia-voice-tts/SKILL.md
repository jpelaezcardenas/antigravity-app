---
name: contexia-voice-tts
description: Use when generating speech for Contexia — Taty's WhatsApp voice notes, Hermes agent voice output, or any text-to-speech task in this ecosystem. Covers which VoiceBox engine to use, the local API contract, and the rules that govern what Taty's cloned voice is allowed to say.
author: Contexia
version: 1.0.0
---

# contexia-voice-tts Skill

Contexia's voice provider is **VoiceBox**, running **locally**. This skill tells you which engine
to use, how to call it, and — most importantly — what the voice is not allowed to say.

## Status: shipped, switched OFF

The integration is merged behind `VOICE_ENABLED`, which defaults to `false` on both the backend and
the local Chatwoot bridge. VoiceBox is **not running** on the current laptop (i7-1165G7, 16 GB,
CPU-only: 3-5 minutes per phrase). It is intended for the future inference node
(Ryzen 7 + RTX 4070 Ti Super).

**If asked to produce voice while the flag is off, say it is unavailable and why.** Do not improvise
a substitute — do not reach for a cloud TTS provider, do not fake an audio file, do not claim to
have generated something you did not. A previous session in this project reported writing plan files
and creating this very skill; neither existed on disk. Report what you actually did.

## Hard rules

1. **The voice never states a fiscal figure.** No amounts, percentages, UVT values, or filing
   deadlines. ARCHITECTURE.md Decisión #19 documented — twice, in synthetic A/B and in real
   production — that without KB grounding the model invents fiscal figures with total confidence.
   A spoken figure is harder to dispute than a written one and leaves the human operator nothing to
   quote back. Figures go in the text reply, which is always sent.

2. **Voice is additive, never a replacement.** The text reply is always sent and always mirrored
   into Chatwoot as a private note. A voice-only reply destroys the audit trail.

3. **The safety gate has one owner.** `apps/backend/services/voice_safety.py::should_speak()` decides,
   and its verdict travels as `voice_allowed` on the `/leads/{lead_id}/reply` response. Do not
   re-implement the rule anywhere else, and do not bypass it.

4. **Tatiana's cloned voice requires consent on file.** Tatiana Barbosa is a real, licensed
   accountant (Entidad A). Written, dated, revocable consent scoped to Contexia is a blocking
   prerequisite before the flag is enabled. During Phase 0 validation her cloned voice was made to
   say abusive sexual text — this rule exists because it already failed once.

5. **Local only.** No cloud TTS provider. Client financial text does not leave the machine. Same
   sovereignty principle as ARCHITECTURE.md Decisiones #1/#10/#20/#22.

## Which engine

Measured on 2026-09-05 — full table in `references/fase0-benchmark.md`.

| Engine | Clones a voice? | Verdict |
|---|---|---|
| **Qwen3-TTS 0.6B** | **Yes — validated on Tatiana** | **Use this one** |
| Kokoro 82M | No (preset voices only) | Fast, but cannot be Taty |
| Chatterbox Multilingual | Yes | Works; not selected |
| Chatterbox Turbo | — | **Broken** in v0.5.0: `Cannot copy out of meta tensor` |
| Qwen3-TTS 1.7B | Yes | Unusable on CPU (~30-60 min/phrase) |
| LuxTTS | Yes | Works; unevaluated for quality |

**Do not load several engines at once.** Four concurrent engines exceeded 16 GB RAM and caused the
heavy swapping that looked like a hang during Phase 0.

## How to call it

Full contract in `references/api.md`, captured from the live server's own OpenAPI document.

**`POST /generate` does not return audio.** It returns JSON (`GenerationResponse`) carrying an `id`,
a `status` and an `error`. The audio is a second call: `GET /audio/{generation_id}`. Code written on
the assumption that `/generate` streams back a WAV is wrong.

Two request defaults are traps — send a request without overriding them and you get **English**
speech from the **slowest** model:

- `language` defaults to `en` → **must set `es`**
- `model_size` defaults to `1.7B` → **must set `0.6B`** (1.7B is the model Phase 0 rejected)

**WhatsApp will not play a WAV as a voice note** — convert to OGG/Opus with ffmpeg first
(`apps/chatwoot-bridge/audio_converter.py`).

**Never guess a `profile_id`.** If `VOICEBOX_PROFILE_ID` is empty, voice is unavailable; say so.
To move the cloned voice to another machine use `GET /profiles/{id}/export` +
`POST /profiles/import` — a re-clone from the reference audio produces a *different* voice than the
one that was validated.

## Where the code lives

| Concern | File |
|---|---|
| Safety gate (authoritative) | `apps/backend/services/voice_safety.py` |
| Graph media upload + audio send | `apps/backend/channels/whatsapp.py` |
| Internal delivery endpoint | `apps/backend/presentation/voice_endpoints.py` |
| Local synthesis client | `apps/chatwoot-bridge/voicebox_client.py` |
| WAV to OGG/Opus | `apps/chatwoot-bridge/audio_converter.py` |
| Hermes TTS wrapper | `apps/hermes-voicebox/voicebox_tts.ps1` |
| Change record | `openspec/changes/voicebox-local-voice-adoption/` |

## Why the bridge synthesises and the backend delivers

The backend runs on Railway and cannot reach a local `127.0.0.1:17493`. Chatwoot cannot deliver
either: its WhatsApp channel never sees a genuine customer inbound, so its 24-hour-window
bookkeeping always believes the window is closed and Meta rejects every message it tries to send
(`apps/chatwoot-bridge/backend_client.py:85-101`, found live 2026-08-12).

So: the **local** bridge synthesises, and `POST /internal/whatsapp/voice-note` on Railway performs
the Graph send. If you are ever asked to "just have Chatwoot send the audio", that is the design
that was already tried and does not work.

## Inbound audio is out of scope

Customers' voice notes are still refused (`AUDIO_FALLBACK_REPLY`), and `channels/whatsapp.py` still
ignores `audio` message types. `LOCAL_WHISPER_URL` in the bridge config is a documented, unused
placeholder for a future change. Do not wire STT without a change that specs it.
