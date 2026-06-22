SUPERGOAL_PHASE_START
Phase: 5 of 5 - Polish & Harden
Task: Verify winner selection, docs, and artifact hygiene end to end.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/select_voice_candidate.py --help; python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; bash scripts/run_select_voice_candidate_smoke.sh; python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts; bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh scripts/run_select_voice_candidate_smoke.sh; git diff --check; git status --short --ignored
Acceptance criteria: 10
Evidence required: command exit codes, smoke selected-winner summary, artifact hygiene summary, docs overclaim check
Depends on phases: 1, 2, 3, 4

## Why

This is the final safety pass before the winner-selection workflow becomes the canonical way to mark a trained voice as primary.

## Work

- Re-run every relevant command.
- Verify selected-winner smoke evidence.
- Verify selected metadata is small and no heavy artifacts are copied.
- Verify docs do not overclaim automatic final winner selection.
- Verify generated outputs and raw audio remain ignored/non-commit artifacts.
- Review added lines for cleanliness.

## Acceptance Criteria

- `python tools/select_voice_candidate.py --help` exits 0.
- `python -m unittest discover -s tests` exits 0.
- `bash scripts/run_train_voice_candidates_smoke.sh` exits 0.
- `bash scripts/run_select_voice_candidate_smoke.sh` exits 0 and emits winner-selection evidence.
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh scripts/run_select_voice_candidate_smoke.sh` exits 0.
- `git diff --check` exits 0.
- `git status --short --ignored` shows no generated review WAVs, copied metrics, checkpoints, generated manifests, or raw `Input/` audio as normal commit candidates.
- Added-line cleanliness check finds no conflict markers, debug prints, or task markers in app code.
- Docs do not imply automatic final voice choice is complete.

## Mandatory Commands

- `python tools/select_voice_candidate.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `bash scripts/run_select_voice_candidate_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh scripts/run_select_voice_candidate_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

## Evidence Required

- Command exit codes.
- Selection smoke summary.
- Artifact hygiene summary.
- Docs overclaim check.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
