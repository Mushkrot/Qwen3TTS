SUPERGOAL_PHASE_START
Phase: 3 of 5 — Score Checkpoints
Task: Aggregate sample metrics into checkpoint scores and warnings, including text match and optional speaker similarity.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: unit test summary, checkpoint_score row, command exit codes
Depends on phases: 1, 2

## Why

The user's readiness criterion is that every checkpoint has a numeric score and warnings list.

## Work

- Add checkpoint-level aggregation after eval metrics are written.
- Add Whisper text-match abstraction with safe stub/off behavior and real-backend-ready boundaries.
- Add optional speaker-similarity abstraction with warning fallback when no backend is configured.
- Add scoring weights and hard warning conditions.
- Write `checkpoint_score` rows after every checkpoint.

## Acceptance criteria (all must pass — verify each in transcript)

- Every checkpoint gets one `checkpoint_score` JSONL row.
- Each `checkpoint_score` row contains numeric `score`, `epoch`, `checkpoint_path`, `sample_count`, `metric_summary`, and `warnings`.
- `whisper_text_match` is numeric in stub mode and real-backend-ready without importing Faster-Whisper at module import time.
- `speaker_similarity` is numeric when a backend result is available; otherwise it is absent/null with a warning and scoring still produces a numeric score.
- Hard warning conditions include duration/pace out of band, clipping, too-quiet audio, leading/trailing silence problems, text mismatch, missing loss, and unavailable speaker backend.
- Unit tests verify score bounds, warning generation, text-match behavior, and optional speaker-similarity fallback.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`

Command classes:

- All commands are `baseline-safe`; real Whisper and real speaker embedding checks are `external/env`.

## Evidence required in transcript

- Unit test summary.
- Example `checkpoint_score` row with numeric score and warnings list.
- Command exit codes.

## Notes

- A missing optional speaker backend must not fail smoke.
- Scoring should be transparent: keep `metric_summary` and warnings next to the score.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-4-automatic-checkpoint-me-NuexKP/PROTOCOL.md without further
instruction needed here.
