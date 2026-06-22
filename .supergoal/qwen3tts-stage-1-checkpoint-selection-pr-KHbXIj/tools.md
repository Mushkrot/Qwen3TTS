# Tool Discovery

- Supergoal skill: available at `/root/.codex/skills/supergoal/SKILL.md`.
- Recallant MCP: available and used for session/context startup.
- Web/current upstream check: available through `curl -fsS`; GitHub issue `QwenLM/Qwen3-TTS#179` remains open as of 2026-06-22, and linked PR `#178` remains open/unmerged.
- Local verification tools: shell, git, Python virtualenv `.venv`, project scripts.
- Package manager: none detected for the repo root.

## Planned Verification Commands

- `git diff --check`
- `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh`
