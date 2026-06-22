# Plan Integrity: Pre-Flight Command Classification

## Rule

Pre-flight runs only `baseline-safe` commands: commands that can pass before any future phase creates new files.

Commands that need files created by a future phase must stay in that phase's mandatory commands and must not be part of pre-flight.

## Command Classes

| Command | Class | Earliest phase | Reason |
|---|---|---:|---|
| `git diff --check` | baseline-safe | pre-flight | Checks current diff whitespace; no future deliverable required. |
| `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` | baseline-safe | pre-flight | Uses existing source directories only. |
| `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh` | baseline-safe | pre-flight | Uses existing shell scripts only. |
| `git status --short --ignored` | baseline-safe | pre-flight | Inspection command; does not depend on future files. |
| `python tools/train_voice_candidates.py --help` | requires-phase-1 | 1 | `tools/train_voice_candidates.py` is created in Phase 1. |
| `python -m unittest discover -s tests` | requires-phase-1 | 1 | `tests/` and initial tests are created in Phase 1. |
| `python -m compileall -q tools` | requires-phase-1 | 1 | `tools/` is created in Phase 1. |
| `python -m compileall -q tools scripts` | requires-phase-1 | 2 | `tools/` exists after Phase 1; Phase 2 expands it. |
| `bash scripts/run_train_voice_candidates_smoke.sh` | requires-phase-4 | 4 | Smoke script is created in Phase 4. |
| `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` | requires-phase-4 | 5 | Includes the new smoke script created in Phase 4. |
| Real orchestrator execution without stub mode | external/env | after implementation | Requires ready dataset, model cache/CUDA/runtime resources, and may be long-running. |

## Repaired Pre-Flight Set

Run these only before dispatch:

```bash
git diff --check
python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts
bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh
git status --short --ignored
```

## Integrity Notes

- No scope was removed from the plan.
- Commands that failed in the earlier pre-flight remain mandatory phase checks.
- The red pre-flight was a plan-integrity issue, not evidence that the repository baseline is broken.
