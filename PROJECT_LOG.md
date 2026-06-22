# Project Log

## Current Session

Status: Implemented and committed 56dc731. Default voice_filter_mode silero now loads local Silero VAD from /ai/models/torch_cache/hub/snakers4_silero-vad_master using project ffmpeg PCM decoding; ffmpeg silencedetect fallback is conservative; smoke uses .venv/bin/python and explicitly asserts speech accepted, music rejected, silence rejected, mixed rejected. Tracked tree is clean except ignored local artifacts/raw Baritone Input audio.
Current focus: Qwen3TTS dataset voice-filtering audit and external ASR inventory after recovery
Next step: If continuing dataset work, build a real Ready dataset with --voice_filter_mode silero --strict_mode and inspect quality_report plus filtered_out quarantine before training.

## Active Constraints

- Recallant is the main source of truth for durable memory.
- This file is a compact fallback/checkpoint, not the full project history.
- If Recallant is unavailable, record only minimal fallback state here and sync it later.

## Open Questions

- Whether to install WhisperX into the Qwen3TTS .venv for better word boundary alignment before production dataset builds.

## Recallant

- Project: Qwen3TTS
- Project id: f6ead963-0af2-4d00-bfda-01d5e124e4d8
- Attach mode: autopilot
- Production-sensitive: false
