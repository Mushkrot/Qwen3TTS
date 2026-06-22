# Repo Map

Generated 2026-06-22.

## Top-level layout

- `AGENTS.md`
- `PROJECT_LOG.md`
- `README.md`
- `datasets/`
- `docs/`
- `experiments/`
- `external/`
- `patches/`
- `requirements.lock.txt`
- `requirements.txt`
- `scripts/`

## Key Documentation

- `docs/PROJECT_STATUS.md`: live project state and current training policy.
- `docs/EVAL_PHRASE_SET.md`: existing fixed phrase set and manual scoring checklist.
- `docs/DATASET_CONTRACT.md`: dataset purity and manifest requirements.
- `docs/VOICE_FILTERING_POLICY.md`: non-voice rejection policy and report fields.
- `docs/RUNBOOK.md`: operational checks and dataset build commands.
- `docs/ARCHITECTURE.md`: repository data flow and main surfaces.
- `docs/ARTIFACT_POLICY.md`: what may and may not be committed.

## Key Scripts

- `scripts/build_dataset_from_audio.py`: dataset builder with voice filtering.
- `scripts/voice_filter.py`: speech/non-speech detection helpers.
- `scripts/validate_manifest.py`: manifest validation.
- `scripts/run_prepare_data.sh`: wrapper for upstream `prepare_data.py`.
- `scripts/run_sft_0_6b.sh`: fixed-epoch SFT wrapper.
- `scripts/run_infer_sample.py`: single-sample inference helper.

## Recent Relevant Activity

- `936d7fe fix: reject intro-window dataset chunks`
- `77112f7 docs: record intro-window cleanup checkpoint`
- `e9be477 docs: record voice filter audit checkpoint`
- `56dc731 fix: enforce real voice filtering smoke`
- `34a0ba5 chore: freeze restored Qwen3TTS state`
