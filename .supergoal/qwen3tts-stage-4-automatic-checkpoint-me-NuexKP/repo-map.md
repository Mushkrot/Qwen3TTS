# Repo map

_Generated 2026-06-22 13:46:13_

## Top-level layout
- AGENTS.md
- PROJECT_LOG.md
- README.md
- datasets
- docs
- experiments
- external
- patches
- requirements.lock.txt
- requirements.txt
- scripts
- tests
- tools

## Source directories (depth 2)
## File counts (top extensions)
- `.md`: 21 files
- `.py`: 4 files
- `.sh`: 3 files
- `.txt`: 2 files
- `.toml`: 1 files
- `.patch`: 1 files
- `.jsonl`: 1 files

## Largest source files (top 15 by line count)
- `scripts/build_dataset_from_audio.py` (1134 lines)
- `scripts/voice_filter.py` (508 lines)
- `scripts/run_voice_filter_smoke.sh` (317 lines)
- `.gitignore` (222 lines)
- `requirements.lock.txt` (110 lines)
- `scripts/validate_manifest.py` (90 lines)
- `scripts/run_infer_sample.py` (56 lines)
- `patches/qwen3-tts-sft-runtime-local-model.patch` (33 lines)
- `scripts/run_sft_0_6b.sh` (31 lines)
- `scripts/run_prepare_data.sh` (26 lines)
- `.codex/config.toml` (14 lines)
- `.env.example` (8 lines)
- `requirements.txt` (3 lines)
- `experiments/qwen3_ru_en_speaker_v1/manifests/train_raw.template.jsonl` (2 lines)
- `datasets/voices/Dima/Ready/.gitkeep` (1 lines)

## Test surface
- Directories named `test`: 3
- Directories named `tests`: 188
- Directories named `specs`: 1
- Test files (by name pattern): 3156

## Notable config / infra

## Recent activity (last 10 commits)
- `77112f7` 2026-06-22 docs: record intro-window cleanup checkpoint
- `936d7fe` 2026-06-22 fix: reject intro-window dataset chunks
- `e9be477` 2026-06-22 docs: record voice filter audit checkpoint
- `56dc731` 2026-06-22 fix: enforce real voice filtering smoke
- `34a0ba5` 2026-06-22 chore: freeze restored Qwen3TTS state
- `bd1730b` 2026-06-22 chore: restore project dataset structure
- `90d6a4b` 2026-06-22 docs: finalize rollout handoff with full smoke verification status
- `dc64091` 2026-06-22 ci: add deterministic smoke offline override and docs
- `583bbe8` 2026-06-22 fix: make smoke filter-only path handle non-voice files
- `d65f0c4` 2026-06-22 ci: make smoke filter check runnable without ASR dependency

## Files churned in last 20 commits (top 10)
- `scripts/README.md` (13×)
- `scripts/build_dataset_from_audio.py` (9×)
- `docs/VOICE_FILTERING_POLICY.md` (7×)
- `docs/DATASET_CONTRACT.md` (7×)
- `scripts/run_voice_filter_smoke.sh` (6×)
- `docs/VOICE_FILTERING_ROLLOUT_NOTES.md` (6×)
- `scripts/voice_filter.py` (4×)
- `PROJECT_LOG.md` (4×)
- `docs/RUNBOOK.md` (3×)
- `scripts/run_infer_sample.py` (2×)

_End repo map._
