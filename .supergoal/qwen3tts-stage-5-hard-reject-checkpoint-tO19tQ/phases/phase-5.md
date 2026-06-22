SUPERGOAL_PHASE_START
Phase: 5 of 5 — Polish & Harden
Task: Verify hard rejects, candidate filtering, docs, and artifact hygiene end to end.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts; bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh; git diff --check; git status --short --ignored
Acceptance criteria: 9
Evidence required: command exit codes, candidate manifest excerpt, final diff stat, artifact hygiene summary
Depends on phases: 1, 2, 3, 4

## Why

This is the final safety pass before hard rejects become part of the candidate workflow.

## Work

- Re-run all mandatory commands.
- Verify candidate manifests never include rejected checkpoints.
- Verify docs do not overclaim full early stopping or full audio export.
- Confirm generated outputs and raw input audio remain ignored/non-commit artifacts.
- Review added lines for debug/TODO/conflict markers.

## Acceptance Criteria

- `python tools/train_voice_candidates.py --help` exits 0 and documents hard reject/candidate options.
- `python -m unittest discover -s tests` exits 0.
- `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and emits hard reject/candidate evidence.
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- `git diff --check` exits 0.
- `git status --short --ignored` shows no generated metrics/audio/checkpoints/manifests or raw `Input/` audio as normal commit candidates due to this run.
- Smoke `candidate_manifest.json` contains no rejected checkpoints in `candidates`.
- Docs do not imply full automatic early stopping or full audio export is complete.

## Mandatory Commands

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

## Evidence Required

- Command exit codes.
- Candidate manifest excerpt.
- Final `git diff --stat`.
- Artifact hygiene summary.

## Notes

- No real GPU training.
- No real speaker embedding requirement.
- If docs overclaim automatic stopping/candidate audio export, correct them before completion.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.

