# Plan Integrity

## Mandatory command classification

### Baseline-safe pre-flight commands

These commands may run before Stage 8 creates new files:

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

### Requires phase-created files

Do not run these before the phase that creates the file:

- `python tools/select_voice_candidate.py --help` requires Phase 1.
- `bash scripts/run_select_voice_candidate_smoke.sh` requires Phase 3.
- `bash -n scripts/run_select_voice_candidate_smoke.sh` requires Phase 3.

### External/env commands

- None required.

## Rule

Pre-flight must run only baseline-safe commands. Phase-time verification may run commands that depend on files created earlier in the same phase or previous phases.
