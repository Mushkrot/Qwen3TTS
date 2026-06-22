SUPERGOAL_PHASE_START
Phase: 3 of 5 — Select Candidates
Task: Produce candidate selection metadata that excludes hard-rejected checkpoints.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; bash scripts/run_train_voice_candidates_smoke.sh; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 7
Evidence required: unit test summary, candidate_selection row, candidate_manifest excerpt, command exit codes
Depends on phases: 1, 2

## Why

The user-facing criterion is that bad variants do not enter final candidates.

## Work

- Add candidate selection helper over score/gate rows.
- Write `candidate_selection` event after all epochs complete.
- Write `candidate_manifest.json` under the run directory.
- Ensure selected candidates reference checkpoint path and eval dir but do not copy generated WAVs into tracked paths.
- Add tests proving rejected checkpoints are excluded, even when their raw score is high.

## Acceptance Criteria

- Candidate selection ignores every checkpoint with `hard_rejected: true`.
- Candidate selection includes at most `top_candidates` non-rejected checkpoints.
- Candidate ordering uses score descending, then fewer warnings/reasons, then earlier epoch.
- If no checkpoint is viable, the manifest contains an empty candidates list plus rejected summary and limited status.
- `candidate_manifest.json` records selected candidates, rejected checkpoints, scores, gate reasons, checkpoint paths, and eval directories.
- The orchestrator writes `candidate_selection` after all epochs finish.
- Unit tests show a bad checkpoint with better raw score still does not appear in final candidates.

## Mandatory Commands

- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Unit test summary.
- Smoke `candidate_selection` row.
- Smoke `candidate_manifest.json` excerpt.
- Command exit codes.

## Notes

- This is metadata selection, not full copied audio export.
- Generated manifests stay in run output paths and are not committed.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.

