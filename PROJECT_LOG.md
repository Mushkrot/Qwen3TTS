# Project Log

## Current Session

Status: Remediation complete: runtime .venv restored, input audio ignored, docs updated, code smoke/hardening fixes verified, ready to stage and commit code/docs/config/patches only
Current focus: Qwen3TTS restored-state freeze and commit preparation
Next step: Stage code/docs/.codex config/patches/lock/scaffolds; ensure raw Input audio remains ignored; commit current safe project state before new measurement work

## Active Constraints

- Recallant is the main source of truth for durable memory.
- This file is a compact fallback/checkpoint, not the full project history.
- If Recallant is unavailable, record only minimal fallback state here and sync it later.

## Open Questions

- Should historical checkpoint/sample artifacts be restored from backup or regenerated from the current Baritone dataset?
- Should full ASR smoke get a tiny tracked synthetic/known-good speech fixture, or stay fixture-explicit?
- Should .git tmp_pack garbage be cleaned in a separate maintenance step after explicit owner approval?

## Recallant

- Project: Qwen3TTS
- Project id: f6ead963-0af2-4d00-bfda-01d5e124e4d8
- Attach mode: autopilot
- Production-sensitive: false
