# VoiceBox Phase 0 — local validation report

**Date:** 2026-09-05
**Hardware:** laptop "Contexia" — i7-1165G7, 16 GB RAM, **CPU-only** (no CUDA)
**VoiceBox:** v0.5.0 desktop (MSI), REST API on `http://127.0.0.1:17493`
**Recovered:** 2026-09-08

## Why this file exists

Phase 0 was run in a Hermes session that reported saving its plan and report to
`.hermes/plans/2025-09-05_voicebox-fase0-validacion.md`. **That file was never written.** A later
sweep of the whole Windows user profile (`*voicebox*`, `*fase0*`, `*fase1*`, `*2025-09-05*`,
`*2026-09-05*`) found only VoiceBox application binaries and data — no plan document anywhere. The
directory `C:\Users\contexia\.hermes\plans\` does not exist at all; `C:\Users\contexia\hermes\plans\`
does exist but holds only an unrelated upstream Hermes document.

One strong signal the path was generated rather than read back: the session ran on **2026**-09-05
but the reported filename was dated **2025**-09-05 — a year off in a name supposedly just written.

The findings themselves survived in the session transcript. They are transcribed here, verbatim in
substance, so they live in git instead of in a directory an agent can claim to have written to.

**Provenance note:** every row below is a result the operator observed and reported in that session.
None of it was re-measured on 2026-09-08 — this machine cannot run the engines at a usable speed,
which is the whole reason the integration ships dark. Treat the latency column as indicative, and
re-measure on the inference node (task 11.x of the migration runbook).

## Engine results

| Engine | Works? | Clones a voice? | CPU latency (this laptop) | Verdict |
|---|---|---|---|---|
| Kokoro 82M | Yes | **No** — preset voices only | ~30 s | Rejected: cannot clone Tatiana |
| Chatterbox Multilingual | Yes | Yes | ~3-5 min | Usable, not selected |
| Chatterbox Turbo | **No** | — | — | Rejected: `Cannot copy out of meta tensor` (PyTorch load bug) |
| **Qwen3-TTS 0.6B** | **Yes** | **Yes — validated** | ~3-5 min | **SELECTED** |
| Qwen3-TTS 1.7B | Yes | Yes | ~30-60 min | Rejected: unusable on CPU |
| LuxTTS | Yes | Yes | ~2-3 min | Usable, not evaluated for quality |
| TADA 1B / 3B | Started | — | — | Not evaluated |

Full engine list offered by v0.5.0: Qwen3-TTS 1.7B, Qwen3-TTS 0.6B, Qwen CustomVoice 1.7B,
Qwen CustomVoice 0.6B, LuxTTS, Chatterbox, Chatterbox Turbo, TADA 1B, TADA 3B Multilingual,
Kokoro 82M.

## What was validated

1. **VoiceBox runs locally and its REST API responds** — `GET /` returned
   `{"message": "voicebox API", "version": "0.5.0"}`.
2. **Models are stored on local disk**, downloaded once from HuggingFace
   (`~/.cache/huggingface/hub/`, 1-5 GB per engine). Generation needs no internet.
3. **Voice cloning of Tatiana Barbosa works** with Qwen3-TTS 0.6B, from a reference audio plus its
   reference transcript.

## Operational findings

- **Do not load several engines at once.** Four concurrent engines exceeded 16 GB RAM and caused
  heavy swapping; that, not the engines themselves, explains the 20-minute stalls observed.
- **CPU-only is fine for validation, not for production.** 3-5 minutes per phrase is unacceptable
  for a WhatsApp reply.
- **WAV does not play as a WhatsApp voice note** — output must be converted to OGG/Opus.
- **Chatterbox Turbo is blocked** by the meta-tensor bug in v0.5.0. Avoid until upstream patches it.

## Safety incident — the reason for the consent and HITL requirements

During validation, someone typed abusive sexual text into the generate box and **Tatiana's cloned
voice said it**; the artefact was saved as `hola-soy-taty-esclava-sexual-d.wav`.

Tatiana Barbosa is a real, named, licensed accountant (Entidad A). A clone of her voice reciting
arbitrary unreviewed text is a genuine legal and reputational exposure, and it happened on the very
first day the clone existed. This is the direct origin of two blocking requirements in the change:

1. Written, dated, revocable consent from Tatiana, scoped to Contexia, before the flag is enabled.
2. A safety gate in the backend so the voice never speaks unreviewed free-form text — and never
   speaks a fiscal figure, since ARCHITECTURE.md Decisión #19 already documented the model
   inventing figures with full confidence, and a spoken figure is harder to dispute than a written
   one.

## Selected configuration

| Setting | Value |
|---|---|
| Engine | Qwen3-TTS 0.6B |
| Profile | "Taty" — cloned from Tatiana's reference audio |
| Language | `es` |
| Output for WhatsApp | OGG/Opus (converted from the WAV VoiceBox returns) |
| Expected latency on the inference node | to be measured — acceptance threshold < 15 s |

## Not done in Phase 0

- STT / `POST /transcribe` was not exercised (deferred: inbound audio stays out of scope).
- No comparative quality scoring across engines beyond "clones / does not clone, usable / not".
- No measurement on CUDA hardware — the node does not exist yet.
