# Scripts

This folder contains helper scripts for Qwen3TTS training and dataset preparation.

## Automated dataset builder (input audio -> train_raw.jsonl)

Build a dataset from raw audio files with pause-based chunking and word-level ASR:

```bash
source .venv/bin/activate
python scripts/build_dataset_from_audio.py \
  --input_dir /path/to/raw_audio \
  --output_root experiments/qwen3_ru_en_speaker_v1/dataset_auto \
  --language ru \
  --voice_filter_mode hybrid \
  --max_no_speech_prob 0.80 \
  --use_whisperx_align \
  --validate_manifest
```

Output:
- chunks: `.../dataset_auto/chunks/*.wav` (24k mono)
- transcripts: `.../dataset_auto/transcripts/*.txt`
- manifest: `.../dataset_auto/manifests/train_raw.jsonl`
- quality report: `.../dataset_auto/reports/quality_report.{json,csv}`

Optional:
- pass fixed reference voice with `--ref_audio /path/to/ref.wav`
- tune segmentation thresholds with `--min_pause`, `--target_duration`, `--max_duration`
- tune speech filtering with `--voice_filter_mode`, `--max_no_speech_prob`, `--min_word_voice_overlap`, `--min_segment_voice_ratio`
- tune old filtering with `--min_words`, `--min_avg_confidence`, `--max_low_conf_ratio`
- enable WhisperX boundary refinement with `--use_whisperx_align`

`voice_filter_mode`:
- `off`: legacy behavior (no additional non-voice filtering)
- `hybrid` (default): reject non-speech ASR segments using `no_speech_prob` and track voice overlap for each chunk
- `strict`: same as `hybrid` plus per-word overlap filtering before chunking

WhisperX notes:
- WhisperX is optional, but if `--use_whisperx_align` is enabled the run is fail-fast.
- If WhisperX is unavailable or alignment fails, the script stops with an explicit error.
- Install manually when needed:

```bash
source .venv/bin/activate
pip install whisperx
```

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
