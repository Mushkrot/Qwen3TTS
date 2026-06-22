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
  --voice_filter_export_quarantine \
  --voice_filter_export_quarantine_snippets \
  --validate_manifest
```

Review:

- `Ready/<run_name>/reports/quality_report.json`
- `Ready/<run_name>/filtered_out/removed_segments.jsonl`
- `Ready/<run_name>/manifests/train_raw.jsonl`

Do not stage raw `Input/` audio or generated `Ready/` outputs unless a small metadata file is intentionally added.

## Commit checklist

Before commit:

```bash
git status --ignored --short
git diff --stat
git diff --cached --stat
```

Stage only code, docs, config without secrets, scaffolds, patch files, and small manifests/templates.
Never stage raw `Input/` audio.
