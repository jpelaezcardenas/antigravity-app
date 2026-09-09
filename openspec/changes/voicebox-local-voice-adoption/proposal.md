# VoiceBox — local voice adoption (dark launch)

## Why

Contexia has no voice. Taty answers in text on every surface, and the two places where voice would
matter most are both closed today:

1. **Outbound.** `channels/whatsapp.py::send_whatsapp_message` hardcodes `"type": "text"`. There is
   no media upload and no `type: audio` send, so Taty cannot send a WhatsApp voice note at all.
2. **Hermes agents.** Hermes already ships a full TTS/STT subsystem (`tts:`/`stt:` config blocks,
   `tts`/`stt` built-in toolsets), but it has never been used — both `audio_cache/` directories are
   empty. Its default is `provider: edge` with the voice `en-US-AriaNeural`: a **cloud** provider
   speaking **English** for a Colombian-Spanish product. The moment Taty speaks a client's cash
   figure through it, that text leaves the machine — contradicting the data-sovereignty decisions
   (ARCHITECTURE.md #1/#10/#20/#22) that keep Hermes, GBrain, the HubSpot poller and the ingestion
   pollers local.

VoiceBox (MIT, upstream `jamiepine/voicebox`) closes both: it is a local-first voice studio with a
REST API on `:17493`, an MCP server, voice cloning, and CUDA/CPU backends. Phase 0 validated on
2026-09-05 that Qwen3-TTS 0.6B clones Tatiana Barbosa's voice successfully
(`reports/2026-09-05-fase0-validacion.md`).

**The constraint that shapes this whole change:** the current laptop (i7-1165G7, 16 GB, CPU-only)
takes 3-5 minutes per phrase. VoiceBox cannot run in production here. The inference node
(Ryzen 7 + RTX 4070 Ti Super) does not exist yet. So the goal is **not** to ship working voice — it
is to ship the complete integration **switched off**, so that enabling it on the new node is a
configuration change, not a development project.

## What changes

1. **A shared local VoiceBox node, two consumers.** Hermes gains voice through a `type: command`
   TTS provider (or its MCP server — decided in Stage 1 with the binary in hand), which needs zero
   Python. The Taty WhatsApp path gains an outbound voice note.

2. **Voice synthesis stays local; only finished audio crosses to Railway.** The backend runs on
   Railway and cannot reach a local `127.0.0.1:17493`, and Chatwoot cannot deliver to WhatsApp at
   all (its channel believes the 24-hour window is permanently closed —
   `apps/chatwoot-bridge/backend_client.py:85-101`, found live 2026-08-12). So the local bridge
   synthesises, and a new `POST /internal/whatsapp/voice-note` — same `INTERNAL_API_KEY`
   fail-closed pattern as the Siigo and Gmail pollers (Decisión #22) — performs the Graph API send.
   No tunnel: a local GPU service is not going on the internet.

3. **Voice is additive, never a replacement.** The text reply is always sent and always mirrored
   into Chatwoot as a private note. A voice-only reply would erase the quotable trail the human
   operator audits, which matters precisely because Decisión #19 documented the model inventing
   fiscal figures with full confidence.

4. **A safety gate with a single owner.** `services/voice_safety.py::should_speak(text)` lives in
   the backend and its verdict travels to the bridge as an additive `voice_allowed` field on the
   existing `/leads/{lead_id}/reply` response. The bridge never re-derives the rule, cannot bypass
   it, and does not spend GPU time on a reply that will be discarded.

5. **Everything ships behind `VOICE_ENABLED`, default `False`**, on both the backend and the
   bridge. Rollback is one environment variable.

6. **The `contexia-voice-tts` skill is created** — canonical source in `ai-specs/skills/`, deployed
   as a real directory into Hermes' profile skills folder. A prior session reported creating and
   updating this skill; it does not exist.

7. **Two canon documents are corrected.** `ARCHITECTURE.md` gains a VoiceBox container row and a
   new settled decision; and Decisión #21 is fixed — it names `~/.hermes/config.yaml` and an
   OmniRoute fallback at `localhost:20128`, but the live config is
   `AppData\Local\hermes\profiles\contexia\config.yaml` and its `fallback_providers` are
   gemini + openrouter, with no OmniRoute entry.

## Success signals

- With `VOICE_ENABLED=False`, the WhatsApp reply path is byte-identical to today and makes zero
  calls to VoiceBox — proven by a dedicated test, not by inspection.
- `POST /internal/whatsapp/voice-note` returns 503 when `INTERNAL_API_KEY` is unset (fail closed).
- The Graph two-step (media upload → `type: audio` send) is verified against a fake HTTP transport,
  never by patching the function under test.
- `ai-specs/skills/contexia-voice-tts/SKILL.md` and its deployed copy in Hermes both exist on disk.
- Enabling voice on the new node touches only environment variables and one Hermes config key — no
  code change, no migration, no database row.

## Non-goals

- **Inbound audio / STT.** Customers' voice notes stay rejected (`AUDIO_FALLBACK_REPLY`), and
  `channels/whatsapp.py` keeps ignoring `audio` message types. `LOCAL_WHISPER_URL` in the bridge's
  config remains the documented, unused placeholder it already is.
- **The Búnker microphone.** `hermes-jarvis-contexia:144` deferred a "VoiceBox proxy script" to its
  own Fase 2; that surface stays its own. The Hermes-CLI and Taty-WhatsApp paths here do not depend
  on it (that change is at 0/28 tasks and blocks nothing).
- **Telegram voice.** Same brain, different channel — a later change once WhatsApp is proven.
- **Persisting audio.** v1 streams bytes and stores nothing. If persistence is ever needed, the
  pattern to copy is `services/document_storage_service.py` (private bucket, signed URLs on demand).
- **Any paid or cloud TTS provider.** Local only.
- **Turning voice on.** This change ends with the integration merged and switched off.

## Blocking prerequisite (non-code, founder)

**Written consent from Tatiana Barbosa for the voice clone** — dated, revocable, scoped to
Contexia, stored outside the repository. During Phase 0 her cloned voice was made to say abusive
sexual text (`reports/2026-09-05-fase0-validacion.md`). She is a real, licensed professional; the
flag does not get enabled without her consent on file. No credential or PII value is ever written
into a versioned file (Decisión #12).
