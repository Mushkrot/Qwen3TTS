# Repo Map

## Top-level layout

- `AGENTS.md`
- `PROJECT_LOG.md`
- `README.md`
- `datasets/`
- `docs/`
- `experiments/`
- `external/`
- `patches/`
- `requirements.txt`
- `requirements.lock.txt`
- `scripts/`

## Files likely touched by this run

- `tools/train_voice_candidates.py` (new)
- `tools/__init__.py` (new, if useful for tests)
- `tests/test_train_voice_candidates.py` (new)
- `tests/fixtures/...` (small text/json fixtures only)
- `scripts/run_train_voice_candidates_smoke.sh` (new)
- `scripts/README.md`
- `docs/RUNBOOK.md`
- `docs/CHECKPOINT_SELECTION_PROTOCOL.md`
- `docs/EVAL_PHRASE_SET.md` if phrase definitions need a link to the orchestrator
- `.gitignore` only if smoke outputs need a new ignored path; prefer `/tmp` smoke output instead

## Generated runtime paths

- Real run output defaults should be under `experiments/qwen3_ru_en_speaker_v1/`.
- Smoke output should be under `/tmp/qwen3tts_train_voice_candidates_smoke` to avoid accidental commits.
- Real candidate WAVs/checkpoints remain ignored by existing `experiments/**/samples/` and `experiments/**/runs/` ignore rules.
