# Project Log

## Current Session

Status: Recallant project-side repair is complete in commit 78783ad. Previous TTS long-form cleanup/documentation work remains in progress: useful generated audio was copied under datasets/voices/Aiden/Ready/builtin_quality_2026-06-23, datasets/voices/Ryan/Ready/builtin_quality_2026-06-23, and datasets/voices/Baritone/Ready/prosody_control_2026-06-23; docs record that Russian long-form with trained Baritone is not viable, built-in Aiden/Ryan English 02_quality_longer_chunks is the best current Qwen3TTS reading result, and the next Qwen3TTS test should use a native-English source speaker with the desired timbre.
Current focus: Qwen3TTS work can resume; Recallant project-side connection is repaired
Next step: Next agent should start with memory_start_session and memory_get_context_pack, then continue the original work by reviewing the existing docs/NEXT_TTS_STRATEGY_2026-06-23.md change and .supergoal/narrate-chapter-mag-edinstvo-skomorokh-w-WFIROk/. If live CLI proof is required, run recallant doctor --project-dir /ai/Qwen3TTS --require-capture --format json only with explicit live-host approval.

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
