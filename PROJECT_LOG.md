# Project Log

## Current Session

Status: Cleanup and docs are ready to commit. Useful generated audio was copied into datasets/voices/Aiden/Ready/builtin_quality_2026-06-23, datasets/voices/Ryan/Ready/builtin_quality_2026-06-23, and datasets/voices/Baritone/Ready/prosody_control_2026-06-23. Ignored generated artifacts under experiments/qwen3_ru_en_speaker_v1 were removed, leaving only tracked scaffolds/templates. Docs now record that Russian long-form with the trained Baritone voice is not viable, built-in Aiden/Ryan English 02_quality_longer_chunks is the best current Qwen3TTS reading result, and the next Qwen3TTS test should use a native-English source speaker with desired timbre.
Current focus: Qwen3TTS long-form cleanup/documentation after built-in Aiden/Ryan samples showed better English reading than the trained Russian Baritone voice.
Next step: Commit the cleanup/docs/scripts/scaffolds, then wait for the owner to provide native-English speaker audio under datasets/voices/<NewVoice>/Input for the next training experiment.

## Active Constraints

- Recallant is the main source of truth for durable memory.
- This file is a compact fallback/checkpoint, not the full project history.
- If Recallant is unavailable, record only minimal fallback state here and sync it later.

## Open Questions

- Which native-English speaker/timbre should be used as the next target voice?
- Should the next experiment train a new Qwen3TTS voice first, or also test a TTS-plus-voice-conversion pipeline?

## Recallant

- Project: Qwen3TTS
- Project id: f6ead963-0af2-4d00-bfda-01d5e124e4d8
- Attach mode: autopilot
- Production-sensitive: false
