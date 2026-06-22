SUPERGOAL_PHASE_START
Phase: 2 of 5 — Compute Signal Metrics
Task: Compute loss and audio signal metrics for generated eval samples.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: unit test summary, sample_metrics rows, smoke output, command exit codes
Depends on phases: 1

## Why

The score must be grounded in measurable training/audio evidence, not only in checkpoint existence.

## Work

- Parse train logs or known metrics rows for loss values when available.
- Compute audio metrics for each eval sample: duration, duration ratio, pace, RMS, clipping, leading silence, trailing silence.
- Ensure safe smoke produces deterministic metric evidence without real model execution.
- Add tests with generated local WAV fixtures and missing-loss fixtures.

## Acceptance criteria (all must pass — verify each in transcript)

- Each generated eval sample produces a `sample_metrics` JSONL row.
- Every `sample_metrics` row includes `duration_seconds`, `expected_duration_seconds`, `duration_ratio`, `pace_chars_per_sec`, `pace_words_per_sec`, `rms_dbfs`, `clipping_ratio`, `leading_silence_ms`, and `trailing_silence_ms`.
- Training loss is parsed from train logs when present and recorded as numeric `loss_last` and `loss_min` fields for the checkpoint.
- Missing loss data produces a warning, not a crash.
- Stub smoke generates deterministic metric values without real Qwen/GPU execution.
- Unit tests cover normal audio, clipping, silence boundaries, pace/duration calculation, and missing-loss behavior.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`

Command classes:

- All commands are `baseline-safe`; real audio/model work remains `external/env`.

## Evidence required in transcript

- Unit test summary.
- Example `sample_metrics` rows from smoke.
- Smoke output excerpt.
- Command exit codes.

## Notes

- Prefer standard-library WAV fixture generation in tests.
- If real eval files are not valid WAV, report a warning and keep the run inspectable.
- Do not add raw/generated artifacts inside the repo except tracked code/docs/tests.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-4-automatic-checkpoint-me-NuexKP/PROTOCOL.md without further
instruction needed here.
