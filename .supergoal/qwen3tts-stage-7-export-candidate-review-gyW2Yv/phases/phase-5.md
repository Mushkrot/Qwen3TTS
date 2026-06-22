SUPERGOAL_PHASE_START
Phase: 5 of 5 - Polish & Harden
Task: Verify candidate review export, docs, and artifact hygiene end to end.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts; bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh; git diff --check; git status --short --ignored
Acceptance criteria: 9
Evidence required: command exit codes, smoke candidate-review summary, candidate review tree and ranking excerpt, artifact hygiene summary
Depends on phases: 1, 2, 3, 4

## Why

This is the final safety pass before candidate review export becomes part of the training workflow.

## Work

- Re-run all mandatory commands.
- Verify review export folder shape and contents.
- Verify no rejected checkpoint appears in review export.
- Verify docs do not overclaim final winner persistence.
- Confirm generated outputs and raw input audio remain ignored/non-commit artifacts.
- Review added lines for cleanliness.

## Acceptance Criteria

- `python tools/train_voice_candidates.py --help` exits 0 and documents review-root/candidate options.
- `python -m unittest discover -s tests` exits 0.
- `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and emits review-pack evidence.
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- `git diff --check` exits 0.
- `git status --short --ignored` shows no generated review WAVs, copied metrics, checkpoints, generated manifests, or raw `Input/` audio as normal commit candidates.
- Added-lines cleanliness check finds no conflict markers, debug prints, or task markers in app code.
- Docs do not imply selected-checkpoint persistence or automatic final voice choice is complete.

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
- Smoke candidate-review summary.
- Candidate review tree and ranking excerpt.
- Artifact hygiene summary.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
