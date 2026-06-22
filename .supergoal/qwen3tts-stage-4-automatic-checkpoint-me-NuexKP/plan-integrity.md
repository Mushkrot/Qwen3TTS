# Plan Integrity: Pre-Flight Command Classification

## Rule

Pre-flight runs only `baseline-safe` commands: commands that can pass before this Stage 4 run creates new files or scripts.

Commands that need files created by a future phase remain mandatory phase checks and must not be part of pre-flight.

## Command Classes

| Command | Class | Earliest phase | Reason |
|---|---|---:|---|
| `python tools/train_voice_candidates.py --help` | baseline-safe | pre-flight | Existing Stage 2/3 CLI is present in the current working tree. |
| `python -m unittest discover -s tests` | baseline-safe | pre-flight | Existing Stage 2/3 tests are present and must stay green. |
| `bash scripts/run_train_voice_candidates_smoke.sh` | baseline-safe | pre-flight | Existing Stage 2/3 smoke script is present and safe. |
| `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` | baseline-safe | pre-flight | Existing source directories only. |
| `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` | baseline-safe | pre-flight | Existing shell scripts only. |
| `git diff --check` | baseline-safe | pre-flight | Checks current diff whitespace. |
| `git status --short --ignored` | baseline-safe | pre-flight | Inspection command. |
| `python -m unittest tests.test_checkpoint_metrics` | requires-phase-1 | 1 | Phase 1 creates metric-specific tests/module. |
| `bash scripts/run_train_voice_metrics_smoke.sh` | requires-phase-4 | 4 | Phase 4 may add an optional dedicated metrics smoke wrapper. |
| Real Whisper transcription metrics | external/env | after implementation | Requires model availability and runtime resources. |
| Real speaker embedding metrics | external/env | after implementation | Requires a configured embedding backend/reference. |

## Repaired Pre-Flight Set

Use these before dispatch:

```bash
python tools/train_voice_candidates.py --help
python -m unittest discover -s tests
bash scripts/run_train_voice_candidates_smoke.sh
python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts
bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh
git diff --check
git status --short --ignored
```
