SUPERGOAL_PHASE_START
Phase: 5 of 5 — Polish & Harden
Task: Verify the orchestrator, eval pack, docs, smoke safety, and artifact hygiene end to end.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts; bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh; git diff --check; git status --short --ignored
Acceptance criteria: 8
Evidence required: command exit codes, smoke tree, diff stat, artifact hygiene summary
Depends on phases: 1, 2, 3, 4

## Why

This is the final safety pass before the workflow becomes the way we start real voice training runs.

## Work

- Re-run all mandatory commands.
- Review help text, docs, and tests for misleading claims.
- Confirm smoke output is in `/tmp`.
- Confirm no generated checkpoint/WAV/raw audio files are introduced as commit candidates.
- Summarize final changed files.

## Acceptance criteria (all must pass — verify each in transcript)

- `python tools/train_voice_candidates.py --help` exits 0.
- `python -m unittest discover -s tests` exits 0.
- `bash scripts/run_train_voice_candidates_smoke.sh` exits 0.
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- `git diff --check` exits 0.
- `git status --short --ignored` shows no raw `datasets/voices/**/Input/` audio staged/untracked as a normal commit candidate due to this run.
- Final docs clearly distinguish stub smoke from real GPU training.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

Command classes:

- `python tools/train_voice_candidates.py --help`: requires-phase-1.
- `python -m unittest discover -s tests`: requires-phase-1.
- `bash scripts/run_train_voice_candidates_smoke.sh`: requires-phase-4.
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`: mixed; `tools` requires-phase-1, existing dirs are baseline-safe.
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`: mixed; new smoke script requires-phase-4, existing scripts are baseline-safe.
- `git diff --check`: baseline-safe.
- `git status --short --ignored`: baseline-safe inspection.

## Evidence required in transcript

- Command exit codes.
- Smoke output summary and tree.
- Final `git diff --stat`.
- Final changed-file summary with artifact hygiene note.

## Notes

- Do not run real GPU training during final verification.
- If docs or help imply fully automatic quality selection, correct them before completing.
- These full checks are valid in Phase 5 because all previous deliverables must already exist.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-2-3-training-orchestrator-YjbP5r/PROTOCOL.md without further
instruction needed here.
