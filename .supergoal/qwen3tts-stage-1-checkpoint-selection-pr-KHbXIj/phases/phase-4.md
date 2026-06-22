SUPERGOAL_PHASE_START
Phase: 4 of 4 — Polish & Harden
Task: Audit the checkpoint protocol docs for consistency, conservative claims, and baseline static checks.
Type: brownfield, documentation, ML workflow
Mandatory commands: git diff --check; python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts; bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh; git diff --stat
Acceptance criteria: 8
Evidence required: rg outputs, command exit codes, diff stat, changed-docs summary
Depends on phases: 1, 2, 3

## Why

Documentation that will steer autonomous training must be internally consistent and must not promise implemented automation before it exists.

## Work

- Review the final docs for contradictions and misleading claims.
- Confirm protocol links are discoverable from README and docs.
- Confirm pace-regression risk and dataset-purity preconditions are visible.
- Run the baseline static checks listed below.
- Summarize the final diff.

## Acceptance criteria (all must pass — verify each in transcript)

- `rg -n "CHECKPOINT_SELECTION_PROTOCOL" README.md docs/EVAL_PHRASE_SET.md docs/PROJECT_STATUS.md docs/RUNBOOK.md` returns at least one hit in each listed file.
- `rg -n "CANDIDATE_REVIEW_REPORT" README.md docs/RUNBOOK.md docs/CHECKPOINT_SELECTION_PROTOCOL.md` returns at least one hit in each listed file.
- `rg -n "fully automatic|optimal plateau|best checkpoint automatically" README.md docs` returns no misleading claim that this is already implemented.
- `rg -n "QwenLM/Qwen3-TTS#179|progressively faster|pace" docs/CHECKPOINT_SELECTION_PROTOCOL.md docs/EVAL_PHRASE_SET.md` shows the pace-regression risk is documented.
- `git diff --check` exits 0.
- `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh` exits 0.
- Final `git diff --stat` shows only docs/template changes expected for Stage 1.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `git diff --check`
- `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh`
- `git diff --stat`

## Evidence required in transcript

- Print command exit codes.
- Print final `git diff --stat`.
- Print a short summary of changed docs.

## Notes

- This phase must not run training or generate dataset/audio/checkpoint artifacts.
- If a command fails because baseline is already broken, follow the Supergoal failure protocol and surface the exact failure.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-1-checkpoint-selection-pr-KHbXIj/PROTOCOL.md without further
instruction needed here.
