SUPERGOAL_PHASE_START
Phase: 3 of 5 - Wire Selection Smoke
Task: Add a no-GPU smoke for choosing candidate B from an exported review pack.
Type: brownfield, Python, ML workflow
Mandatory commands: bash scripts/run_select_voice_candidate_smoke.sh; bash scripts/run_train_voice_candidates_smoke.sh; python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: smoke output summary, selected checkpoint excerpt, status excerpt, command exit codes
Depends on phases: 1, 2

## Why

The normal smoke path should prove the owner workflow from generated review pack to selected winner.

## Work

- Add `scripts/run_select_voice_candidate_smoke.sh`.
- Reuse or invoke the training candidate smoke so a fresh review pack exists.
- Select candidate B.
- Verify selected checkpoint metadata points to candidate B and not candidate A.
- Verify active experiment status points to the same checkpoint.
- Verify selection did not copy heavy directories or WAVs.
- Print a concise summary.

## Acceptance Criteria

- `bash scripts/run_select_voice_candidate_smoke.sh` exits 0.
- Smoke first produces a Stage 7 candidate review pack with at least candidates A and B.
- Smoke runs `python tools/select_voice_candidate.py --candidate B` or the explicit-path equivalent.
- Smoke verifies `selected_checkpoint.json` points to candidate B's checkpoint and not candidate A.
- Smoke verifies local experiment status points to the same selected checkpoint.
- Smoke verifies no checkpoint/WAV directory copy was created by selection.

## Mandatory Commands

- `bash scripts/run_select_voice_candidate_smoke.sh`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Smoke output summary.
- Selected checkpoint excerpt.
- Status metadata excerpt.
- Command exit codes.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
