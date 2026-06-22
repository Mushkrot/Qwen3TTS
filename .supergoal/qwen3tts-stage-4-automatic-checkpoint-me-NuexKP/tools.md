# Tool Discovery

- Supergoal skill available and used for this planning run.
- Recallant MCP available; session `f5180ba9-d56c-4a59-b6e6-8daea92ccc70`, context pack `8cc7c9f9-a53e-4650-ad58-221951c4c4c9`.
- Web/network available but not required for this plan; implementation can use current local code and existing dependencies.
- Baseline-safe local verification commands:
  - `python tools/train_voice_candidates.py --help`
  - `python -m unittest discover -s tests`
  - `bash scripts/run_train_voice_candidates_smoke.sh`
  - `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
  - `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
  - `git diff --check`
  - `git status --short --ignored`
