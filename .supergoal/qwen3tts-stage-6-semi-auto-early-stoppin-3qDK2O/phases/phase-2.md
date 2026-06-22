SUPERGOAL_PHASE_START
Phase: 2 of 5 — Implement Stop Decisions
Task: Make the epoch loop stop itself from score, patience, max epoch, and degradation evidence.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 7
Evidence required: unit test summary, patience stop row, degradation stop row, command exit codes
Depends on phases: 1

## Why

The core user request is that training reaches a concrete stopping point without listening after every epoch.

## Work

- Add stop-decision helper over prior `checkpoint_gate` rows.
- Append one `early_stop_decision` after each `checkpoint_gate`.
- Break the epoch loop when the decision says stop.
- Append one `run_stop` summary before `run_end`.
- Base no-improvement patience on non-rejected checkpoints only.
- Treat degradation stop as a hard-reject signal such as `pace_accelerated`, `suspected_cut`, `duration_too_short`, `duration_too_long`, or `score_drop` after `min_epochs` is reached.
- Add deterministic synthetic tests for all stop paths.

## Acceptance Criteria

- The loop always runs at least `min_epochs` unless training/eval raises a hard failure.
- With stable stub scores, default policy stops before epoch 6 via `patience_exhausted`.
- `max_epochs_reached` stops exactly at `max_epochs` when patience/degradation do not stop earlier.
- A degradation hard reject after `min_epochs` stops before the next epoch.
- Rejected checkpoints do not reset the no-improvement patience counter.
- Every completed checkpoint has exactly one `early_stop_decision` row after its `checkpoint_gate`.
- `run_stop` records `reason`, `epoch`, `best_epoch`, `best_score`, and `epochs_completed`.

## Mandatory Commands

- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Unit test summary.
- Example patience stop row.
- Example degradation stop row.
- Command exit codes.

## Notes

- Do not run real GPU training.
- Do not remove existing hard-reject or candidate-selection behavior.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
