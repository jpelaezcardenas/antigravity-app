# Phase 0 engine benchmark — VoiceBox v0.5.0

**Measured:** 2026-09-05
**Hardware:** laptop "Contexia" — i7-1165G7, 16 GB RAM, **CPU-only, no CUDA**
**Source of record:** `openspec/changes/voicebox-local-voice-adoption/reports/2026-09-05-fase0-validacion.md`

> These numbers are from CPU-only inference on a laptop and are **indicative, not a target**.
> Re-measure on the inference node before enabling anything. The acceptance threshold for a
> WhatsApp voice note is **< 15 s per reply** — above that the note arrives late enough to annoy.

## Results

| Engine | Works? | Clones a voice? | CPU latency | Verdict |
|---|---|---|---|---|
| Kokoro 82M | Yes | **No** — preset voices only | ~30 s | Rejected: cannot be Taty |
| Chatterbox Multilingual | Yes | Yes | ~3-5 min | Usable, not selected |
| Chatterbox Turbo | **No** | — | — | **Blocked**: `Cannot copy out of meta tensor` |
| **Qwen3-TTS 0.6B** | **Yes** | **Yes — validated on Tatiana** | ~3-5 min | **SELECTED** |
| Qwen3-TTS 1.7B | Yes | Yes | ~30-60 min | Rejected: unusable on CPU |
| LuxTTS | Yes | Yes | ~2-3 min | Usable, quality unevaluated |
| TADA 1B / 3B Multilingual | Started | — | — | Not evaluated |

Full engine list in v0.5.0: Qwen3-TTS 1.7B, Qwen3-TTS 0.6B, Qwen CustomVoice 1.7B,
Qwen CustomVoice 0.6B, LuxTTS, Chatterbox, Chatterbox Turbo, TADA 1B, TADA 3B Multilingual,
Kokoro 82M.

## Operational findings

- **Never load several engines at once.** Four concurrent engines exceeded 16 GB RAM and caused
  heavy swapping. The 20-minute "hangs" observed during Phase 0 were swap, not model time.
- **Models are local.** Downloaded once from HuggingFace into `~/.cache/huggingface/hub/`
  (1-5 GB per engine). Generation needs no internet.
- **WAV does not play as a WhatsApp voice note.** Convert to OGG/Opus.
- **Chatterbox Turbo is a PyTorch model-loading bug in v0.5.0**, not a configuration mistake.
  Avoid it until upstream patches it; do not spend time re-diagnosing it.

## What was NOT measured

- Any CUDA/GPU figure. The inference node does not exist yet — every latency above is CPU-only.
- STT (`POST /transcribe`). Inbound audio is out of scope for the current change.
- Comparative audio quality beyond "clones / does not clone, usable / not usable". No MOS scoring,
  no blind comparison. If quality between Qwen3-TTS 0.6B, LuxTTS and Chatterbox Multilingual ever
  matters, it still needs to be measured.
