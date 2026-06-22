SUPERGOAL_PHASE_START
Phase: 2 of 5 — Evaluate Hard Rejects
Task: Add per-checkpoint hard reject decisions from metrics and checkpoint history.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 8
Evidence required: unit test summary, clean gate row, rejected gate fixture row, command exit codes
Depends on phases: 1

## Why

The system must explicitly classify bad checkpoints before candidate selection can safely ignore them.

## Work

- Add a hard reject evaluator that consumes `checkpoint_score`, `sample_metrics`, and previous gate rows.
- Append exactly one `checkpoint_gate` row after each `checkpoint_score`.
- Implement user-requested reject reasons:
  - ASR/text mismatch.
  - Pace materially faster than previous non-rejected checkpoint.
  - Audio clipping.
  - Too-short or too-long duration.
  - Suspected cut from silence/duration anomalies.
  - Sharp score drop from previous viable/best checkpoint.
- Add focused unit tests with synthetic metrics histories.

## Acceptance Criteria

- Each checkpoint receives exactly one `checkpoint_gate` row after its `checkpoint_score`.
- Low `whisper_text_match` produces an ASR/text reject reason.
- Material pace acceleration versus a previous non-rejected checkpoint produces a reject reason.
- Clipping above threshold produces a reject reason.
- Too-short or too-long duration ratio produces a reject reason.
- Suspected cut from duration/silence anomalies produces a reject reason.
- Score drop beyond threshold versus previous viable/best checkpoint produces a reject reason.
- A clean stub checkpoint is not hard rejected.

## Mandatory Commands

- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Unit test summary.
- Example clean `checkpoint_gate` row.
- Example synthetic rejected gate row from tests or fixture.
- Command exit codes.

## Notes

- Rejected checkpoints remain in metrics for audit.
- Do not select final candidates in this phase.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.

