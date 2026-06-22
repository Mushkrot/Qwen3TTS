SUPERGOAL_PHASE_START
Phase: 4 of 5 — Update Docs
Task: Make the runbook, protocol, script docs, and templates describe implemented semi-auto stopping accurately.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; git diff --check
Acceptance criteria: 7
Evidence required: documentation grep output, smoke output summary, unit test summary, command exit codes
Depends on phases: 1, 2, 3

## Why

The docs must stop saying early stopping is future-only once Stage 6 is implemented, while still avoiding overclaiming full automatic voice selection.

## Work

- Update `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- Update `docs/RUNBOOK.md`.
- Update `scripts/README.md`.
- Update `docs/templates/CANDIDATE_REVIEW_REPORT.md` if stop summary fields belong in reports.
- Update `README.md`, `docs/PROJECT_STATUS.md`, or `PROJECT_LOG.md` if they still describe early stopping as future-only.

## Acceptance Criteria

- Docs state Stage 6 implements semi-auto early stopping in project-local orchestration.
- Docs list defaults: `min_epochs=2`, `max_epochs=6`, `patience=2`, `top_candidates=4`.
- Docs explain stop reasons: `min_epochs_pending`, `patience_exhausted`, `quality_degradation`, `max_epochs_reached`, and hard failure.
- Docs state the system no longer requires listening after every epoch.
- Docs state final winner remains human-selected from top candidates.
- Docs keep copied candidate WAV export and selected-checkpoint persistence out of scope unless implemented.
- Docs keep generated metrics/manifests/checkpoints/eval WAVs and raw `Input/` audio out of commit scope.

## Mandatory Commands

- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`

## Evidence Required

- Documentation grep output.
- Smoke output summary.
- Unit test summary.
- Command exit codes.

## Notes

- Be explicit that "naturalness" is currently represented by proxy metrics/gates, not a learned perceptual model.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
