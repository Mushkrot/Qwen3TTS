# Stack context

Generated: 2026-06-22T19:07:29+00:00

## Language signals

- Python repository with `requirements.txt`, `pyproject.toml`, shell smoke scripts, and project-local tools.

## Package manager

- None detected as primary workflow.

## Current branch and baseline

- Branch: `main`
- Current HEAD: `72b3b29a633b5719c0254b9bb9c0afaf2143d8ee`
- Working tree is intentionally dirty with completed Stage 7 candidate-review export changes.

## Known verification commands

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`
