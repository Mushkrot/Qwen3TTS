# Stack context

Generated: 2026-06-22T15:16:06+00:00

## Language signals

- Python workspace.
- No package manager detected; use the existing Python environment.
- Current Stage 4 surface is uncommitted but present in this working tree.

## Build / Test / Lint Commands

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

## Current State

- Branch: `main`.
- Remote: `https://github.com/Mushkrot/Qwen3TTS`.
- Working tree includes prior Stage 4 changes: `tools/`, `tests/`, smoke script, protocol docs, and runbook updates.
- Current baseline test: `python -m unittest discover -s tests` passes with 16 tests.

