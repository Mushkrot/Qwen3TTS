SUPERGOAL_PHASE_START
Phase: 1 of 5 - Define Export Contract
Task: Add candidate review export path, labels, CLI contract, and serialization tests.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: help excerpt, unit test summary, helper/schema excerpt, command exit codes
Depends on phases: none

## Why

The owner-facing export needs a stable contract before any audio files are copied.

## Work

- Add an optional `--candidate_review_root` parser argument.
- Add helper(s) for resolving the review pack root from args and `RunPaths`.
- Add helper(s) for rank labels: rank 1..4 maps to A..D, with epoch included in the folder name.
- Add a small serializable export metadata model or row shape for candidate review export.
- Add focused unit tests for helper behavior and parser help.
- Keep imports standard-library only.

## Acceptance Criteria

- A helper resolves the candidate review root deterministically and accepts `--candidate_review_root` override.
- A rank helper maps rank 1..4 to `candidate_A`..`candidate_D` and includes the epoch in the folder name.
- Parser help exits 0 and includes the new review-root option.
- Review export metadata schema is represented in code and can serialize review directory, ranking path, copied metrics path, candidate count, and exported epochs.
- Importing `tools.train_voice_candidates` still avoids heavy runtime modules.
- Unit tests cover helper outputs without creating real training artifacts.

## Mandatory Commands

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Help excerpt showing review-root option.
- Unit test summary.
- Export contract helper/schema excerpt.
- Command exit codes.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
