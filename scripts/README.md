# Scripts

This folder contains helper scripts for Qwen3TTS training and dataset preparation.

## Automated dataset builder (input audio -> train_raw.jsonl)

Build a dataset from raw audio files with pre-ASR voice filtering:

Project-local voice inputs live under:

```text
datasets/voices/<VoiceName>/Input
```

Write generated output for the same voice under:

```text
datasets/voices/<VoiceName>/Ready/<run_name>
```

Example for the current Baritone voice:

```bash
source .venv/bin/activate
python scripts/build_dataset_from_audio.py \
  --input_dir datasets/voices/Baritone/Input \
  --output_root datasets/voices/Baritone/Ready/build_strict \
  --language ru \
  --voice_filter_mode silero \
  --strict_mode \
  --voice_filter_export_quarantine \
  --voice_filter_export_quarantine_snippets \
  --validate_manifest
```

Do not use `/ai/whisper1` as the Qwen3TTS dataset home. That project is only an
external transcription/source project when explicitly needed.

```bash
source .venv/bin/activate
python scripts/build_dataset_from_audio.py \
  --input_dir /path/to/raw_audio \
  --output_root experiments/qwen3_ru_en_speaker_v1/dataset_auto \
  --language ru \
  --voice_filter_mode silero \
  --voice_filter_min_speech_ms 300 \
  --voice_filter_min_silence_ms 250 \
  --voice_filter_merge_gap_ms 150 \
  --voice_filter_min_coverage 0.75 \
  --voice_filter_export_quarantine \
  --use_whisperx_align \
  --validate_manifest
```

Output:
- chunks: `.../dataset_auto/chunks/*.wav` (24k mono)
- transcripts: `.../dataset_auto/transcripts/*.txt`
- manifest: `.../dataset_auto/manifests/train_raw.jsonl`
- quality report: `.../dataset_auto/reports/quality_report.{json,csv}`
- optional quarantine: `.../dataset_auto/filtered_out/removed_segments.jsonl`, snippets: `.../dataset_auto/filtered_out/snippets/*.wav`
- run metadata: `.../dataset_auto/filtered_out/run_metadata.json`

Optional:
- pass fixed reference voice with `--ref_audio /path/to/ref.wav`
- tune segmentation with `--min_pause`, `--target_duration`, `--max_duration`
- tune text quality with `--min_words`, `--min_chars`, `--min_avg_confidence`, `--max_low_conf_ratio`
- enable WhisperX boundary refinement with `--use_whisperx_align`

`voice_filter_mode`:
- `off`: legacy mode, no pre-ASR filtering (compatibility path)
- `silero` (default): primary voice-region detector path
- `vad`: same behavior as `silero`
- `whisper` / `whisper_only`: whisper-style fallback path
- `hybrid`, `strict`, `legacy`: compatibility aliases

`strict` / `--strict_mode` enforces full-voice purity by default with `--voice_filter_min_coverage=1.0` (unless explicitly overridden).

Strictness controls:
- `--voice_filter_min_speech_ms` — minimum region length kept as speech
- `--voice_filter_min_silence_ms` — minimum silence length considered split/gap
- `--voice_filter_merge_gap_ms` — merges close speech regions
- `--voice_filter_min_coverage` — minimum speech ratio inside final chunk

Validation and notes:
- `--voice_filter_export_quarantine` emits filtered-out regions for audit.
- Rejection reasons are machine-parseable, including `no_voice_regions_detected`, `non_voice_ratio_too_high`, `too_few_voice_frames`, `region_too_short`, `too_many_low_confidence_words`, and others.

WhisperX notes:
- WhisperX is optional, but if `--use_whisperx_align` is enabled the run is fail-fast.
- If WhisperX is unavailable or alignment fails, the script stops with an explicit error.
- Install manually when needed:

```bash
source .venv/bin/activate
pip install whisperx
```

## Smoke voice filter verification

Run the smoke command to validate non-voice filtering behavior on a synthetic input set:

```bash
source .venv/bin/activate
QWEN3TTS_SMOKE_ASR_MODEL=tiny QWEN3TTS_SMOKE_DEVICE=cpu bash scripts/run_voice_filter_smoke.sh
```

If `faster-whisper` is installed, the smoke runs full dataset creation and ASR-based rejection checks.
If it is missing, the command falls back to a filter-only smoke mode and still writes deterministic
`reports/smoke_voice_filter.json` and `filtered_out/removed_segments.jsonl` files.

Control fallback behavior with:

```bash
QWEN3TTS_SMOKE_REQUIRE_ASR=1 bash scripts/run_voice_filter_smoke.sh
```

If `QWEN3TTS_SMOKE_REQUIRE_ASR=1`, the command exits with error when `faster-whisper` is absent.

Use offline-only mode when ASR dependencies/models are not reachable:

```bash
QWEN3TTS_SMOKE_FORCE_FILTER_ONLY=1 bash scripts/run_voice_filter_smoke.sh
```

This forces filter-only smoke checks even if `faster-whisper` is installed in the environment.

Expected output:
- printed acceptance and rejection summary,
- generated manifest/report under `/tmp/qwen3tts_voice_filter_smoke/output/...`,
- `quality_report` contains at least one explicit non-voice rejection reason,
- `filtered_out/removed_segments.jsonl` exists and can be reviewed.

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
