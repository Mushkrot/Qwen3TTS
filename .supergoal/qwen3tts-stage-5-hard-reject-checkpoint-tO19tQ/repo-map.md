# Repo Map

Generated: 2026-06-22T15:16:06+00:00

## Relevant Files

- `tools/train_voice_candidates.py` — project-local prepare/train/eval orchestrator, Stage 4 metric and score layer.
- `tests/test_train_voice_candidates.py` — standard-library unit contract tests.
- `scripts/run_train_voice_candidates_smoke.sh` — no-GPU smoke run under `/tmp/qwen3tts_train_voice_candidates_smoke`.
- `docs/CHECKPOINT_SELECTION_PROTOCOL.md` — canonical checkpoint selection protocol.
- `docs/RUNBOOK.md` — operator workflow and artifact policy.
- `scripts/README.md` — command reference.
- `docs/templates/CANDIDATE_REVIEW_REPORT.md` — human candidate review template.

## Existing Metric Contract

- `sample_metrics` rows: per eval WAV duration/pace/RMS/clipping/silence/text/speaker warnings.
- `checkpoint_score` rows: per checkpoint `score`, `sample_count`, `metric_summary`, and `warnings`.
- No hard reject decision row yet.
- No candidate manifest or final candidate selection event yet.

## Existing Policy

- Bad checkpoints should not reach the listening set.
- Raw `datasets/voices/**/Input/*` audio must remain ignored and never become commit candidates.
- Generated metrics, eval WAVs, checkpoints, logs, run directories, and dataset chunks are working artifacts.

