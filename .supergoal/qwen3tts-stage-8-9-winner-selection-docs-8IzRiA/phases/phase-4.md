SUPERGOAL_PHASE_START
Phase: 4 of 5 - Document Winner Workflow
Task: Update docs for the full training-to-review-to-winner procedure.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; bash scripts/run_select_voice_candidate_smoke.sh; git diff --check
Acceptance criteria: 7
Evidence required: documentation grep output, smoke output summary, unit test summary, command exit codes
Depends on phases: 1, 2, 3

## Why

The project should be runnable by one clear procedure without hidden manual steps.

## Work

- Update `docs/RUNBOOK.md`.
- Update `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- Update `scripts/README.md`.
- Update `docs/templates/CANDIDATE_REVIEW_REPORT.md`.
- Update `README.md` and `docs/PROJECT_STATUS.md` if needed.
- Document the current MVP versus future improvements.
- Preserve artifact policy boundaries.

## Acceptance Criteria

- Docs show how to run semi-auto training.
- Docs show where candidates, `ranking.md`, copied metrics, and `selected_checkpoint.json` live.
- Docs show how to run `python tools/select_voice_candidate.py --candidate B`.
- Docs explain that the owner still verifies and chooses the final voice.
- Docs state the MVP includes epoch-by-epoch training, eval audio, simple metrics, hard rejects, top-4 export, and human winner selection.
- Docs list future improvements as speaker similarity, smarter scoring, richer report, and automatic recommended candidate.
- Docs keep generated audio/checkpoints/metrics out of commit scope while allowing intentional small selection metadata preservation.

## Mandatory Commands

- `python -m unittest discover -s tests`
- `bash scripts/run_select_voice_candidate_smoke.sh`
- `git diff --check`

## Evidence Required

- Documentation grep output.
- Smoke output summary.
- Unit test summary.
- Command exit codes.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
