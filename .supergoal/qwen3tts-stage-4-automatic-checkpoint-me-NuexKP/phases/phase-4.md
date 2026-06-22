SUPERGOAL_PHASE_START
Phase: 4 of 5 — Wire Smoke Docs
Task: Make automatic checkpoint metrics visible in smoke output and documentation.
Type: brownfield, Python, ML workflow
Mandatory commands: bash scripts/run_train_voice_candidates_smoke.sh; python -m unittest discover -s tests; git diff --check
Acceptance criteria: 5
Evidence required: smoke output summary, metrics rows, documentation grep output, command exit codes
Depends on phases: 1, 2, 3

## Why

The metrics must be easy to verify safely before real training runs are launched.

## Work

- Update `scripts/run_train_voice_candidates_smoke.sh` to assert metric rows and checkpoint score exist.
- Update docs for metric names, backend modes, score, warnings, and artifact policy.
- Keep smoke output under `/tmp/qwen3tts_train_voice_candidates_smoke`.

## Acceptance criteria (all must pass — verify each in transcript)

- Smoke exits 0 and verifies at least five `sample_metrics` rows and one `checkpoint_score` row.
- Smoke output prints the metric file path and the checkpoint score.
- Documentation lists all Stage 4 metrics requested by the user.
- Documentation states which metrics are always computed, which are optional, and what warnings mean.
- Documentation warns that generated metric artifacts, checkpoints, eval WAVs, and raw input audio must not be committed.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `git diff --check`

Command classes:

- All commands are `baseline-safe`; docs grep is phase-local evidence.

## Evidence required in transcript

- Smoke output summary.
- Metrics rows from smoke.
- Documentation grep output.
- Command exit codes.

## Notes

- Do not launch real training.
- Do not introduce generated artifacts under tracked repo paths.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-4-automatic-checkpoint-me-NuexKP/PROTOCOL.md without further
instruction needed here.
