# Stack context

Generated 2026-06-22.

## Language signals

- Python workspace with local helper scripts and upstream Qwen3-TTS clone under `external/`.
- No package manager detected at repo root.
- Existing dependencies are declared in `requirements.txt` and `requirements.lock.txt`.

## Current working tree

The tree is intentionally dirty from Stage 1:

- modified docs/log files from checkpoint selection protocol work;
- new `docs/CHECKPOINT_SELECTION_PROTOCOL.md`;
- new `docs/templates/CANDIDATE_REVIEW_REPORT.md`;
- completed `.supergoal/qwen3tts-stage-1-checkpoint-selection-pr-KHbXIj/` artifacts.

The Stage 2/3 executor must not revert or overwrite those changes.

## Existing command surfaces

- `scripts/run_prepare_data.sh`: validates `train_raw.jsonl`, then calls upstream `prepare_data.py`.
- `scripts/run_sft_0_6b.sh`: calls upstream `sft_12hz.py` with configurable env vars and `NUM_EPOCHS`.
- `scripts/run_infer_sample.py`: generates one WAV from one checkpoint and one text prompt.
- `external/Qwen3-TTS/finetuning/sft_12hz.py`: fixed-epoch trainer; it has `--num_epochs` but no explicit resume flag.

## Risky areas

- Upstream SFT has no explicit resume/continue contract.
- Real training and inference are heavy GPU operations, so automated verification needs a stub smoke path.
- Generated checkpoints and WAVs must remain ignored working artifacts.
