SUPERGOAL_PHASE_START
Phase: 2 of 5 - Build Review Export
Task: Create the candidate review pack writer and integrate it after selection.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 7
Evidence required: unit test summary, manifest review-pack excerpt, ranking excerpt, command exit codes
Depends on phases: 1

## Why

After semi-auto stopping, the user should receive copied audio and a readable ranking without digging through all epoch outputs.

## Work

- Write a review pack after `candidate_manifest.json` has been created.
- Copy selected candidates' eval WAV files into rank/epoch folders.
- Copy the run `metrics.jsonl` into the review pack.
- Generate `ranking.md` with checkpoint path, why selected, risks/warnings, and copied audio paths.
- Append a `candidate_review_export` metrics event or equivalent serialized metadata.
- Add review-pack metadata into `candidate_manifest.json`.
- Add unit tests for happy path and missing eval audio failure.

## Acceptance Criteria

- Export runs after `candidate_manifest.json` is written.
- Only `candidate_manifest.json.candidates` are exported; rejected checkpoints are not copied.
- Each exported candidate folder contains the same fixed eval WAV filenames.
- `ranking.md` lists rank, epoch, checkpoint path, score, why selected, warnings/risks, and audio files to listen to.
- The pack includes a copied `metrics.jsonl`.
- The manifest records review directory, ranking path, metrics copy path, exported candidate count, and exported epochs.
- Missing selected eval audio raises `OrchestrationError` instead of producing an incomplete pack.

## Mandatory Commands

- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Unit test summary.
- Manifest review-pack excerpt.
- `ranking.md` excerpt from a stub run or unit fixture.
- Command exit codes.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
