# Stack context

Generated 2026-06-22.

## Language signals

- Python project with `requirements.txt` and upstream `external/Qwen3-TTS/pyproject.toml`.

## Package manager

- No repo-root package manager detected.

## Likely commands

- Static Python check: `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- Shell syntax check: `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh`
- Diff whitespace check: `git diff --check`

## Git

- Branch: `main`
- Remote: `https://github.com/Mushkrot/Qwen3TTS`
- Working tree at planning time: tracked tree clean
- Branch state: ahead of `origin/main` by 26 commits

## Risky Areas

- Existing evaluation policy is manual; this stage must document semi-automatic checkpoint selection without claiming full objective TTS quality automation.
- Dataset purity remains a hard upstream dependency for any training decision.
- Upstream Qwen3-TTS fine-tuning has an open issue where later epochs can make speech progressively faster.
