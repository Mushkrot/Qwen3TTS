SUPERGOAL_PHASE_START
Phase: 5 of 5 — Polish & Harden
Task: Verify automatic metrics end to end and preserve artifact hygiene.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts; bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh; git diff --check; git status --short --ignored
Acceptance criteria: 9
Evidence required: command exit codes, smoke metric rows, final diff stat, artifact hygiene summary
Depends on phases: 1, 2, 3, 4

## Why

This is the final safety pass before automatic metrics become part of normal training workflow.

## Work

- Re-run all mandatory commands.
- Verify help text and docs do not overclaim full early stopping.
- Verify smoke metrics prove every checkpoint has numeric score and warnings list.
- Confirm generated outputs remain ignored or under `/tmp`.

## Acceptance criteria (all must pass — verify each in transcript)

- `python tools/train_voice_candidates.py --help` exits 0 and documents metric/backend options.
- `python -m unittest discover -s tests` exits 0.
- `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and emits metric score evidence.
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- `git diff --check` exits 0.
- `git status --short --ignored` shows no generated metrics/audio/checkpoints or raw `Input/` audio as normal commit candidates due to this run.
- Every checkpoint in smoke has numeric `score` and `warnings` list in `metrics.jsonl`.
- Final docs distinguish stub/off/real metric backends and do not imply automatic stopping is complete.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

Command classes:

- All commands are valid by Phase 5 and baseline-safe in the current Stage 2/3 working tree.

## Evidence required in transcript

- Command exit codes.
- Smoke metric rows and score row.
- Final `git diff --stat`.
- Artifact hygiene summary.

## Notes

- Do not run real GPU training during final verification.
- Do not require real Whisper or real speaker embedding in smoke.
- If docs imply automatic stopping/candidate export is complete, correct them before completing.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-4-automatic-checkpoint-me-NuexKP/PROTOCOL.md without further
instruction needed here.
