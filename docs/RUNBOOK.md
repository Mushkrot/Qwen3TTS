# Runbook

## Start-of-session checks

```bash
cd /ai/Qwen3TTS
git status --short --branch
git status --ignored --short
```

Use Recallant per `AGENTS.md` before non-trivial work.

## Runtime setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Verification:

```bash
source .venv/bin/activate
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
python -c "import soundfile; print('soundfile ok')"
python -c "import faster_whisper; print('faster_whisper ok')"
python -c "import qwen_tts; print('qwen_tts ok')"
```

Current 2026-06-22 verified environment:

- `.venv` exists;
- `torch` imports and CUDA is visible;
- `soundfile`, `faster_whisper`, and `qwen_tts` import;
- `flash-attn` is still optional and not required for the default `sdpa` path.

## Smoke checks

Syntax/static checks:

```bash
python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts
bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh
python scripts/build_dataset_from_audio.py --help
python scripts/voice_filter.py --help
python scripts/validate_manifest.py --help
python scripts/run_infer_sample.py --help
```

Default local voice-filter smoke:

```bash
bash scripts/run_voice_filter_smoke.sh
```

When the historical frozen sample is missing, the script uses local Baritone input and runs filter-only smoke by default.
This validates the voice/non-voice rejection path without treating raw Baritone audio as a stable ASR fixture.
It uses `.venv/bin/python` automatically when present.
Expected filter-only result: speech accepted, music rejected, silence rejected, and mixed speech+non-speech rejected.

Full ASR smoke:

```bash
source .venv/bin/activate
QWEN3TTS_SMOKE_REQUIRE_ASR=1 \
QWEN3TTS_SMOKE_VOICE_SOURCE=/path/to/known-short-speech.wav \
QWEN3TTS_SMOKE_LANGUAGE=ru \
QWEN3TTS_SMOKE_ASR_MODEL=tiny \
QWEN3TTS_SMOKE_DEVICE=cpu \
bash scripts/run_voice_filter_smoke.sh
```

Use a known-good short speech fixture for full ASR smoke.
The current local Baritone fallback starts from raw source audio and may produce no accepted ASR rows.

## Dataset build

```bash
source .venv/bin/activate
python scripts/build_dataset_from_audio.py \
  --input_dir datasets/voices/Baritone/Input \
  --output_root datasets/voices/Baritone/Ready/build_strict \
  --language ru \
  --voice_filter_mode silero \
  --strict_mode \
  --voice_filter_reject_initial_seconds 30 \
  --voice_filter_export_quarantine \
  --voice_filter_export_quarantine_snippets \
  --validate_manifest
```

Review:

- `Ready/<run_name>/reports/quality_report.json`
- `Ready/<run_name>/filtered_out/removed_segments.jsonl`
- `Ready/<run_name>/manifests/train_raw.jsonl`

For audiobook-style sources with intro music/title cards, keep `--voice_filter_reject_initial_seconds`
enabled and verify that early title/intro chunks are rejected with `initial_window_rejected`.

Do not stage raw `Input/` audio or generated `Ready/` outputs unless a small metadata file is intentionally added.

## Training orchestrator

Use the training orchestrator after a ready `train_raw.jsonl` exists and the
dataset quality gate has been reviewed. It performs:

1. `prepare_data` once, producing a prepared manifest with audio codes;
2. one SFT epoch per loop iteration;
3. checkpoint capture after each epoch;
4. five fixed eval samples after each checkpoint;
5. append-only `metrics.jsonl` logging;
6. automatic checkpoint metrics and a numeric checkpoint score;
7. one `checkpoint_gate` hard-reject decision per checkpoint;
8. final `candidate_selection` metadata and `candidate_manifest.json`.

Real command shape:

```bash
source .venv/bin/activate
python tools/train_voice_candidates.py \
  --voice_name Baritone \
  --train_raw_jsonl datasets/voices/Baritone/Ready/<run_name>/manifests/train_raw.jsonl \
  --output_root experiments/qwen3_ru_en_speaker_v1/runs \
  --run_name baritone_sft_candidates_001 \
  --max_epochs 1 \
  --speaker_name speaker_target
```

Real mode is GPU-heavy. Do not use it as a smoke test, and do not launch it
until the dataset report shows only clean speech entering `train_raw.jsonl`.

Safe no-GPU smoke:

```bash
bash scripts/run_train_voice_candidates_smoke.sh
```

The smoke writes only under `/tmp/qwen3tts_train_voice_candidates_smoke` and
creates sentinel checkpoint/eval files. It proves the project orchestration
contract without loading Qwen, Torch, or soundfile. It also verifies that
`metrics.jsonl` contains at least five `sample_metrics` rows and one
`checkpoint_score` row with a numeric `score`, a `metric_summary`, and a
`warnings` list. Stage 5 smoke also verifies at least one `checkpoint_gate`
row, one `candidate_selection` row, and a parseable `candidate_manifest.json`.
It prints selected candidate count and rejected checkpoint count.

Current Stage 4/5 metrics and gates:

- loss signals: `loss_last` and `loss_min` from the train log, with `missing_loss`
  when no loss can be parsed;
- timing signals: `duration_ratio`, `pace_chars_per_sec`, and
  `pace_words_per_sec`;
- signal health: `rms_dbfs`, `clipping_ratio`, `leading_silence_ms`, and
  `trailing_silence_ms`;
- prompt fidelity: `whisper_text_match`;
- voice identity: optional `speaker_similarity` when a backend is configured.

Current hard reject reasons:

- `asr_text_mismatch`: ASR/text match is below the configured threshold;
- `pace_accelerated`: speech becomes materially faster than the previous
  non-rejected checkpoint;
- `audio_clipping`: clipping exceeds the configured threshold;
- `duration_too_short` / `duration_too_long`: generated speech is outside the
  allowed duration-ratio band;
- `suspected_cut`: duration is short and trailing silence is near zero;
- `score_drop`: score is sharply worse than the previous non-rejected
  checkpoint.

Rejected checkpoints stay auditable in `metrics.jsonl` and in
`candidate_manifest.json.rejected_checkpoints`; they must not enter
`candidate_manifest.json.candidates`.

Backend modes are explicit. `--metrics_mode auto` resolves to audio metrics in
stub smoke and real runs, `--metrics_mode off` records disabled audio metrics,
`--text_match_backend auto` resolves to stub text match during smoke, and
`--speaker_similarity_backend off` records an unavailable warning while keeping
checkpoint scores numeric. For real ASR prompt matching, pass
`--text_match_backend faster-whisper`; it lazily loads the configured
`--text_match_model`, `--text_match_device`, and `--text_match_compute_type`.

Generated `metrics.jsonl` files, `candidate_manifest.json` files, checkpoints,
eval WAVs, command logs, and run directories are working artifacts and must not
be committed. Raw audio in voice `Input/` folders is also not a commit target.
Keep generated outputs under ignored experiment paths or `/tmp`; commit only
code, tests, docs, scaffolds, small templates, and intentional metadata.

## Checkpoint selection and review

Use `docs/CHECKPOINT_SELECTION_PROTOCOL.md` before comparing training checkpoints.
The current policy is semi-automatic candidate review: automatic metrics and
hard gates narrow a completed run to up to 3-4 candidate checkpoints in
`candidate_manifest.json`, then the owner chooses the final voice by listening.
This is not full automatic early stopping and does not yet copy a final WAV
review pack.

Use `docs/templates/CANDIDATE_REVIEW_REPORT.md` as the report format when a
candidate review pack is generated.

Do not stage generated candidate WAVs, checkpoints, metrics, or candidate
manifests. Keep them under ignored `experiments/**/samples/` and
`experiments/**/runs/` paths unless a future small metadata file is deliberately
promoted.

## Commit checklist

Before commit:

```bash
git status --ignored --short
git diff --stat
git diff --cached --stat
```

Stage only code, docs, config without secrets, scaffolds, patch files, and small manifests/templates.
Never stage raw `Input/` audio.
