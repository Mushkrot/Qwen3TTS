SUPERGOAL_PHASE_START
Phase: 3 of 5 - Wire Smoke Coverage
Task: Make the no-GPU smoke prove candidate review export end to end.
Type: brownfield, Python, ML workflow
Mandatory commands: bash scripts/run_train_voice_candidates_smoke.sh; python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 7
Evidence required: smoke output summary, candidate review tree listing, ranking excerpt, command exit codes
Depends on phases: 1, 2

## Why

The normal smoke command must show that a user can listen to only exported candidates.

## Work

- Update `scripts/run_train_voice_candidates_smoke.sh` to assert the candidate review directory exists.
- Assert candidate folders, copied WAVs, copied metrics, and `ranking.md`.
- Print candidate review path and export summary.
- Add/adjust tests for rejected high-score non-export and limited candidate packs.

## Acceptance Criteria

- Smoke exits 0 and prints candidate review directory, exported candidate count, ranking path, and copied metrics path.
- Smoke exports more than one candidate and fewer than or equal to `top_candidates`.
- Smoke review folders are named `candidate_A_epoch0`, `candidate_B_epoch1`, etc. for selected candidates.
- Smoke `ranking.md` contains checkpoint path, selected reason, risk text, and audio filenames.
- Smoke copied `metrics.jsonl` exists under candidate review and is byte-identical to the run metrics.
- Unit tests prove a rejected high-score checkpoint is not exported.
- Unit tests prove limited candidate count is reflected in ranking/report text.

## Mandatory Commands

- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Smoke output summary.
- Candidate review tree listing.
- `ranking.md` excerpt.
- Command exit codes.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
