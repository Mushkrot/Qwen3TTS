SUPERGOAL_PHASE_START
Phase: 4 of 5 — Wire Smoke Docs
Task: Make hard reject decisions visible in smoke output and documentation.
Type: brownfield, Python, ML workflow
Mandatory commands: bash scripts/run_train_voice_candidates_smoke.sh; python -m unittest discover -s tests; git diff --check
Acceptance criteria: 5
Evidence required: smoke output summary, manifest/gate row excerpt, documentation grep output, command exit codes
Depends on phases: 1, 2, 3

## Why

Hard reject behavior must be verifiable without running real training.

## Work

- Update smoke script assertions for `checkpoint_gate`, `candidate_selection`, and `candidate_manifest.json`.
- Print selected/rejected counts in smoke output.
- Update protocol/runbook/scripts docs with reject reasons, manifest semantics, and artifact policy.
- Update candidate review template if needed.

## Acceptance Criteria

- Smoke exits 0 and verifies `checkpoint_gate`, `candidate_selection`, and `candidate_manifest.json`.
- Smoke output prints selected candidate count and rejected checkpoint count.
- Documentation lists every hard reject reason requested by the user.
- Documentation states rejected checkpoints remain auditable but do not enter final candidates.
- Documentation keeps generated candidate manifests/metrics/checkpoints/eval WAVs and raw `Input/` audio out of commit scope.

## Mandatory Commands

- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `git diff --check`

## Evidence Required

- Smoke output summary.
- Manifest/gate row excerpt.
- Documentation grep output.
- Command exit codes.

## Notes

- Do not run real GPU training.
- Keep smoke output under `/tmp/qwen3tts_train_voice_candidates_smoke`.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.

