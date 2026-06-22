SUPERGOAL_PHASE_START
Phase: 1 of 5 - Define Selection Contract
Task: Create the winner-selection CLI contract and helper-level tests.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/select_voice_candidate.py --help; python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: help excerpt, unit test summary, helper/schema excerpt, command exit codes
Depends on phases: none

## Why

The project must safely map a human choice like `B` to one exported candidate without guessing the wrong run.

## Work

- Create `tools/select_voice_candidate.py` with standard-library-only import behavior.
- Add a parser with:
  - `--candidate`;
  - optional `--candidate_review_dir`;
  - optional `--experiment_root`;
  - `--dry_run`.
- Add helpers for:
  - normalizing candidate input such as `B`, `b`, `2`, and `candidate_B_epoch1`;
  - discovering a candidate review directory from cwd or known experiment paths;
  - refusing ambiguous discovery;
  - loading `candidate_manifest.json`;
  - resolving where selection metadata will be written.
- Add focused unit tests.

## Acceptance Criteria

- `python tools/select_voice_candidate.py --help` exits 0 and documents `--candidate`, `--candidate_review_dir`, `--experiment_root`, and `--dry_run`.
- Candidate input `B`, `b`, `2`, and `candidate_B_epoch1` resolve to the same rank/label target.
- Auto-discovery accepts an explicit `--candidate_review_dir` and rejects ambiguous discovery with a clear error.
- The script can load a Stage 7 `candidate_manifest.json` and find candidates only from `candidates`, not `rejected_checkpoints`.
- Importing `tools.select_voice_candidate` does not load Qwen/Torch/audio-heavy modules.
- Unit tests cover helper behavior without creating real training/checkpoint artifacts.

## Mandatory Commands

- `python tools/select_voice_candidate.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Help excerpt showing candidate options.
- Unit test summary.
- Helper/schema excerpt.
- Command exit codes.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
