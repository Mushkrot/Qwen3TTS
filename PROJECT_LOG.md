# Project Log

## Current Session

Status: ready_for_next_step.
Current focus: Stage 5 hard-reject checkpoint gates and candidate manifests are implemented and audited.
Next step: Use a real cleaned dataset for training, then decide whether to add copied candidate audio export and automatic stopping.
Last updated: 2026-06-22T15:40:00Z.
## Active Constraints

- Recallant is the main source of truth for durable memory.
- This file is a compact fallback/checkpoint, not the full project history.
- If Recallant is unavailable, record only minimal fallback state here and sync it later.

## Open Questions

- Which real training run should enable `--text_match_backend faster-whisper`.
- Which speaker embedding backend should provide real `speaker_similarity`.
- Whether to implement copied candidate WAV review packs before full automatic stopping.

## Recallant

- Project: Qwen3TTS
- Project id: f6ead963-0af2-4d00-bfda-01d5e124e4d8
- Attach mode: autopilot
- Production-sensitive: false
