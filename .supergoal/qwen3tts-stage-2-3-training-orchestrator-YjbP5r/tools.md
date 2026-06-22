# Tool Discovery

- Supergoal skill: available at `/root/.codex/skills/supergoal/SKILL.md`.
- Recallant MCP: available and used for session/context startup.
- Local verification: shell, git, Python stdlib, `.venv`.
- Package manager: none detected at repository root.

## Planned Verification Commands

- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short`
