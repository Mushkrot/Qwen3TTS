SUPERGOAL_PHASE_START
Phase: 2 of 5 - Build Selection Writer
Task: Persist the human-selected candidate as the primary voice checkpoint.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: unit test summary, selected checkpoint JSON excerpt, status JSON excerpt, command exit codes
Depends on phases: 1

## Why

After the owner listens, the project needs a small durable pointer to the selected checkpoint without copying heavy artifacts.

## Work

- Implement selection execution in `tools/select_voice_candidate.py`.
- Validate that the requested candidate exists in `candidate_manifest.json.candidates`.
- Reject candidates that are absent or only present in `rejected_checkpoints`.
- Write `selected_checkpoint.json`.
- Update local experiment status metadata.
- Add a `winner_selection` or equivalent block to `candidate_manifest.json`.
- Implement `--dry_run` with no writes.
- Add tests for success and failure cases.

## Acceptance Criteria

- Selecting candidate B writes `selected_checkpoint.json` with checkpoint path, selected label, rank, epoch, score, review dir, and source manifest path.
- The local experiment status records the selected checkpoint as active/primary.
- `candidate_manifest.json` records a winner-selection block without overwriting candidate quality status.
- `--dry_run` prints planned files and does not write output files.
- Selecting a missing candidate exits non-zero and writes no partial selection files.
- The implementation copies no checkpoint directories, WAV files, metrics files, or raw audio.

## Mandatory Commands

- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Unit test summary.
- `selected_checkpoint.json` excerpt from a fixture or smoke output.
- Local status metadata excerpt.
- Command exit codes.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
