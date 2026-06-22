SUPERGOAL_PHASE_START
Phase: 1 of 5 — Define Gate Contract
Task: Define hard reject thresholds, events, parser options, and schema tests.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: unit test summary, help excerpt, schema/default threshold excerpt, command exit codes
Depends on phases: none

## Why

The hard reject layer needs a stable JSONL and manifest contract before behavior is added.

## Work

- Add hard reject event constants for `checkpoint_gate` and `candidate_selection`.
- Add threshold/config dataclasses for text mismatch, pace acceleration, clipping, duration, suspected cut, and score drop.
- Add serializable dataclasses or helpers for gate decisions and candidate selection summaries.
- Add parser options for candidate count and hard reject overrides.
- Add unit tests for schemas, defaults, parser help, and import-safety.

## Acceptance Criteria

- The code defines stable event names for `checkpoint_gate` and `candidate_selection`.
- The code defines thresholds for ASR mismatch, pace acceleration, clipping, duration ratio, suspected cut, and score drop.
- Gate decision rows serialize `epoch`, `checkpoint_path`, `hard_rejected`, `reject_reasons`, `warning_reasons`, `score`, and `metric_summary`.
- Candidate selection rows serialize selected epochs and rejected epochs.
- Parser help exposes candidate count and hard-reject threshold options.
- Importing `tools.train_voice_candidates` still does not import `torch`, `qwen_tts`, `soundfile`, `faster_whisper`, or embedding models.

## Mandatory Commands

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Unit test summary.
- Help excerpt for new options.
- Schema/default threshold excerpt.
- Command exit codes.

## Notes

- Keep all new structures standard-library only.
- Do not implement candidate filtering in this phase.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.

