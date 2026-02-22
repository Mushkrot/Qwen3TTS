# Scripts

This folder contains helper scripts for the first Qwen3-TTS 0.6B cycle.

## Validation

```bash
source .venv/bin/activate
python scripts/validate_manifest.py --input_jsonl experiments/qwen3_ru_en_speaker_v1/manifests/train_raw.jsonl
```

## Preprocess (`audio_codes`)

```bash
bash scripts/run_prepare_data.sh \
  experiments/qwen3_ru_en_speaker_v1/manifests/train_raw.jsonl \
  experiments/qwen3_ru_en_speaker_v1/manifests/train_with_codes.jsonl
```

## Train (0.6B)

```bash
bash scripts/run_sft_0_6b.sh \
  experiments/qwen3_ru_en_speaker_v1/manifests/train_with_codes.jsonl \
  experiments/qwen3_ru_en_speaker_v1/runs/sft_0_6b_run1
```

## Quick inference

```bash
source .venv/bin/activate
python scripts/run_infer_sample.py \
  --checkpoint experiments/qwen3_ru_en_speaker_v1/runs/sft_0_6b_run1/checkpoint-epoch-2 \
  --speaker speaker_target \
  --output_wav experiments/qwen3_ru_en_speaker_v1/samples/run1_sample.wav
```

Note: if `flash-attn` is not installed, switch `attn_implementation` in `run_infer_sample.py` to an implementation supported by your runtime.
