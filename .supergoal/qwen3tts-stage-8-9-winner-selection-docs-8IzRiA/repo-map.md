# Repo map

Generated: 2026-06-22T19:07:29+00:00

## Top-level layout

- `tools/`: project-local Python orchestration tools.
- `scripts/`: dataset/training/inference/smoke shell scripts and docs.
- `tests/`: Python `unittest` coverage for orchestration contracts.
- `docs/`: protocol, runbook, project status, evaluation, artifact policy, and templates.
- `experiments/`: ignored run/sample workspace with tracked scaffolds.
- `datasets/voices/<Voice>/{Input,Ready}`: local raw/processed data scaffolds.

## Relevant files

- `tools/train_voice_candidates.py`: training orchestration, candidate manifest, candidate review export.
- `tests/test_train_voice_candidates.py`: contract/unit coverage for training orchestration and review export.
- `scripts/run_train_voice_candidates_smoke.sh`: no-GPU smoke for training through candidate review export.
- `docs/CHECKPOINT_SELECTION_PROTOCOL.md`: canonical checkpoint selection protocol.
- `docs/RUNBOOK.md`: operator procedure.
- `docs/templates/CANDIDATE_REVIEW_REPORT.md`: human review report template.
- `docs/ARTIFACT_POLICY.md`: commit/artifact boundaries.

## Stage 8/9 target files

- New `tools/select_voice_candidate.py`
- New or updated tests in `tests/test_train_voice_candidates.py` or `tests/test_select_voice_candidate.py`
- New `scripts/run_select_voice_candidate_smoke.sh`
- Docs in `docs/`, `scripts/README.md`, and `README.md` as needed.
