SUPERGOAL_PHASE_START
Phase: 4 of 5 - Update Docs
Task: Update project docs so candidate review export is documented as implemented.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; git diff --check
Acceptance criteria: 6
Evidence required: documentation grep output, smoke output summary, unit test summary, command exit codes
Depends on phases: 1, 2, 3

## Why

Docs must no longer describe copied candidate WAV export as future-only once Stage 7 ships.

## Work

- Update `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- Update `docs/RUNBOOK.md`.
- Update `scripts/README.md`.
- Update `docs/templates/CANDIDATE_REVIEW_REPORT.md`.
- Update `README.md` and `docs/PROJECT_STATUS.md` if needed.
- Preserve artifact policy boundaries.

## Acceptance Criteria

- Docs state Stage 7 exports a candidate review pack after semi-auto stopping.
- Docs list the review pack shape including candidate folders, `ranking.md`, and copied `metrics.jsonl`.
- Docs explain that the owner listens only to exported candidates, not every epoch.
- Docs state final winner remains human-selected and selected-checkpoint persistence is still out of scope.
- Docs keep generated review WAVs, copied metrics, checkpoints, generated manifests, and raw `Input/` audio out of commit scope.
- Docs mention the optional review-root override or deterministic default path.

## Mandatory Commands

- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`

## Evidence Required

- Documentation grep output.
- Smoke output summary.
- Unit test summary.
- Command exit codes.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
