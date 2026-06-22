# Repo map

_Generated 2026-06-22 17:01:36_

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
- `.md`: 98 files
- `.sh`: 9 files
- `.py`: 7 files
- `.txt`: 2 files
- `.toml`: 1 files
- `.patch`: 1 files
- `.jsonl`: 1 files

## Largest source files (top 15 by line count)
- `tools/train_voice_candidates.py` (1874 lines)
- `scripts/build_dataset_from_audio.py` (1134 lines)
- `tests/test_train_voice_candidates.py` (1063 lines)
- `scripts/voice_filter.py` (508 lines)
- `scripts/run_voice_filter_smoke.sh` (317 lines)
- `.gitignore` (222 lines)
- `scripts/run_train_voice_candidates_smoke.sh` (203 lines)
- `.supergoal/qwen3tts-stage-6-semi-auto-early-stoppin-3qDK2O/repo-state.sh` (149 lines)
- `.supergoal/qwen3tts-stage-5-hard-reject-checkpoint-tO19tQ/repo-state.sh` (149 lines)
- `.supergoal/qwen3tts-stage-4-automatic-checkpoint-me-NuexKP/repo-state.sh` (149 lines)
- `.supergoal/qwen3tts-stage-2-3-training-orchestrator-YjbP5r/repo-state.sh` (149 lines)
- `.supergoal/qwen3tts-stage-1-checkpoint-selection-pr-KHbXIj/repo-state.sh` (149 lines)
- `requirements.lock.txt` (110 lines)
- `scripts/validate_manifest.py` (90 lines)
- `scripts/run_infer_sample.py` (56 lines)

## Test surface
- Directories named `test`: 3
- Directories named `tests`: 188
- Directories named `specs`: 1
- Test files (by name pattern): 3156

## Notable config / infra

## Recent activity (last 10 commits)
- `72b3b29` 2026-06-22 Add semi-auto voice training early stopping
- `91a7fc9` 2026-06-22 Add voice training candidate hard reject workflow
- `77112f7` 2026-06-22 docs: record intro-window cleanup checkpoint
- `936d7fe` 2026-06-22 fix: reject intro-window dataset chunks
- `e9be477` 2026-06-22 docs: record voice filter audit checkpoint
- `56dc731` 2026-06-22 fix: enforce real voice filtering smoke
- `34a0ba5` 2026-06-22 chore: freeze restored Qwen3TTS state
- `bd1730b` 2026-06-22 chore: restore project dataset structure
- `90d6a4b` 2026-06-22 docs: finalize rollout handoff with full smoke verification status
- `dc64091` 2026-06-22 ci: add deterministic smoke offline override and docs

## Files churned in last 20 commits (top 10)
- `scripts/README.md` (13×)
- `scripts/build_dataset_from_audio.py` (7×)
- `docs/VOICE_FILTERING_POLICY.md` (7×)
- `docs/DATASET_CONTRACT.md` (7×)
- `scripts/run_voice_filter_smoke.sh` (6×)
- `docs/VOICE_FILTERING_ROLLOUT_NOTES.md` (6×)
- `docs/RUNBOOK.md` (5×)
- `PROJECT_LOG.md` (5×)
- `scripts/voice_filter.py` (4×)
- `docs/PROJECT_STATUS.md` (4×)

_End repo map._
