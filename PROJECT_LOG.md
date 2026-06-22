# Project Log

## Current Session

Status: Committed 936d7fe. Added --voice_filter_reject_initial_seconds and initial_window_rejected so audiobook/title intro speech-over-music can be excluded from manifests. Trial Ready outputs and /tmp preview inputs were deleted. Tracked tree was clean after commit except ignored raw Input audio and local env artifacts.
Current focus: Qwen3TTS dataset cleanup after intro music was found in first accepted chunk
Next step: For the next real Baritone dataset build, use --voice_filter_mode silero --strict_mode --voice_filter_reject_initial_seconds 30, then inspect quality_report for initial_window_rejected and spot-check accepted chunks before training.

## Active Constraints

- Recallant is the main source of truth for durable memory.
- This file is a compact fallback/checkpoint, not the full project history.
- If Recallant is unavailable, record only minimal fallback state here and sync it later.

## Open Questions

- Whether a stronger music-under-speech detector/source-separation dependency should be added later for non-intro background music cases.

## Recallant

- Project: Qwen3TTS
- Project id: f6ead963-0af2-4d00-bfda-01d5e124e4d8
- Attach mode: autopilot
- Production-sensitive: false
