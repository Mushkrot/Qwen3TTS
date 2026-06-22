SUPERGOAL_PHASE_START
Phase: 3 of 5 — Wire Manifest Smoke
Task: Expose automatic stop metadata in candidate manifests and smoke output.
Type: brownfield, Python, ML workflow
Mandatory commands: bash scripts/run_train_voice_candidates_smoke.sh; python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: smoke output summary, run_stop JSONL excerpt, candidate_manifest excerpt, command exit codes
Depends on phases: 1, 2

## Why

The stop behavior must be observable without real training and without manual log archaeology.

## Work

- Include stop summary and candidate floor in `candidate_manifest.json`.
- Mark manifest status `limited` when viable candidates are fewer than `candidate_floor`.
- Update smoke script assertions for `early_stop_decision`, `run_stop`, stop summary, and candidate/rejected separation.
- Let smoke run enough stub epochs to prove automatic stopping while remaining no-GPU and fast.
- Add/adjust tests for candidate selection after early stop.

## Acceptance Criteria

- Smoke exits 0 and prints stop reason, epochs completed, selected candidate count, and rejected checkpoint count.
- Smoke produces more than one checkpoint but fewer than default `max_epochs=6`.
- Smoke `metrics.jsonl` contains `early_stop_decision`, `run_stop`, and `candidate_selection`.
- `candidate_manifest.json` records stop reason, best epoch/score, epochs completed, `candidate_floor`, and limited status.
- Manifest candidates do not include rejected checkpoints.
- Unit tests prove a rejected high-score checkpoint cannot become a final candidate after early stop.

## Mandatory Commands

- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Smoke output summary.
- `run_stop` JSONL excerpt.
- `candidate_manifest.json` excerpt.
- Command exit codes.

## Notes

- Smoke artifacts stay under `/tmp/qwen3tts_train_voice_candidates_smoke`.
- Generated manifests are run artifacts, not commit targets.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
