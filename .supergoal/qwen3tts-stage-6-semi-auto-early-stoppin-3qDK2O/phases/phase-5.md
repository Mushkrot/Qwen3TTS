SUPERGOAL_PHASE_START
Phase: 5 of 5 — Polish & Harden
Task: Verify semi-auto early stopping, candidate filtering, docs, and artifact hygiene end to end.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts; bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh; git diff --check; git status --short --ignored
Acceptance criteria: 9
Evidence required: command exit codes, smoke stop summary, candidate manifest excerpt, artifact hygiene summary
Depends on phases: 1, 2, 3, 4

## Why

This is the final safety pass before semi-auto stopping becomes part of the training workflow.

## Work

- Re-run all mandatory commands.
- Verify smoke stops before default `max_epochs`.
- Verify candidate manifests never include rejected checkpoints.
- Verify docs do not overclaim copied WAV export or final human choice persistence.
- Confirm generated outputs and raw input audio remain ignored/non-commit artifacts.
- Review added lines for debug/task/conflict markers.

## Acceptance Criteria

- `python tools/train_voice_candidates.py --help` exits 0 and documents early-stop/candidate options.
- `python -m unittest discover -s tests` exits 0.
- `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and emits auto-stop evidence.
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- `git diff --check` exits 0.
- `git status --short --ignored` shows no generated metrics/audio/checkpoints/manifests or raw `Input/` audio as normal commit candidates due to this run.
- Smoke proves epochs completed are `< max_epochs` under default policy.
- Docs do not imply copied candidate WAV export or final human choice persistence is complete.

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
- Smoke stop summary.
- Candidate manifest excerpt.
- Artifact hygiene summary.

## Notes

- No real GPU training.
- No real speaker embedding requirement.
- No commit during the `/goal` run unless the owner explicitly asks afterward.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
