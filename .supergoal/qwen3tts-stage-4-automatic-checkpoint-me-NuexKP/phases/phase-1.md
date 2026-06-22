SUPERGOAL_PHASE_START
Phase: 1 of 5 — Define Metric Contract
Task: Define the metrics schema, thresholds, backend modes, and tests for checkpoint scoring.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: unit test summary, schema/default threshold excerpt, command exit codes
Depends on phases: none

## Why

The metrics layer needs a stable row format before any signal extraction or scoring logic is added.

## Work

- Extend `tools/train_voice_candidates.py` or create `tools/checkpoint_metrics.py` for metric dataclasses/helpers.
- Define event names and JSONL row shapes for per-sample metrics and checkpoint scores.
- Define default thresholds and score weights.
- Define metric backend modes for safe stub/off behavior and real optional backends.
- Add standard-library unit tests under `tests/`.

## Acceptance criteria (all must pass — verify each in transcript)

- The code defines a stable metric event contract for `sample_metrics` and `checkpoint_score` rows.
- The metric schema includes fields for loss, duration ratio, pace, RMS/clipping, leading/trailing silence, whisper text match, optional speaker similarity, numeric score, and warnings.
- The score is numeric and normalized to a 0-100 range.
- Backend modes distinguish safe stub/off behavior from real Whisper and speaker-similarity backends.
- Importing `tools.train_voice_candidates` still does not import `torch`, `qwen_tts`, `soundfile`, `faster_whisper`, or any embedding model.
- Unit tests cover schema serialization and default thresholds.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

Command classes:

- All commands are `baseline-safe` because Stage 2/3 already created `tools/`, `tests/`, and the orchestrator CLI.

## Evidence required in transcript

- Unit test summary.
- Schema/default threshold excerpt.
- Command exit codes.

## Notes

- Do not import heavy runtime libraries at module import time.
- Do not run real Whisper, real speaker embedding, real Qwen inference, or GPU training in this phase.
- Preserve existing Stage 2/3 behavior while adding metric contracts.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-4-automatic-checkpoint-me-NuexKP/PROTOCOL.md without further
instruction needed here.
