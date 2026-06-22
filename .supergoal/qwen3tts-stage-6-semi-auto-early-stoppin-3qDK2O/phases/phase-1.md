SUPERGOAL_PHASE_START
Phase: 1 of 5 — Define Stop Contract
Task: Add the semi-auto early stopping contract, defaults, parser options, and row schemas.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: help excerpt, unit test summary, stop defaults/schema excerpt, command exit codes
Depends on phases: none

## Why

The stop policy needs a stable data contract before changing training loop behavior.

## Work

- Add stable event constants for `early_stop_decision` and `run_stop`.
- Add dataclasses/helpers for early stopping defaults and serialized stop decisions.
- Add CLI options:
  - `--min_epochs` default `2`;
  - `--max_epochs` default `6`;
  - `--patience` default `2`;
  - `--early_stop_min_delta`;
  - `--candidate_floor` default `3`;
  - keep `--top_candidates` default `4`.
- Add parser validation for invalid combinations.
- Add unit tests for defaults, serialization, help text, invalid args, and import safety.

## Acceptance Criteria

- Code defines stable event names for `early_stop_decision` and `run_stop`.
- Defaults match `min_epochs=2`, `max_epochs=6`, `patience=2`, `top_candidates=4`.
- Stop decision rows serialize `epoch`, `should_stop`, `reason`, `best_epoch`, `best_score`, `epochs_without_improvement`, and `min_epochs_reached`.
- Parser help exposes all early-stop options.
- Invalid parser combinations fail fast, including `--min_epochs < 1`, `--max_epochs < 1`, `--patience < 1`, and `--min_epochs > --max_epochs`.
- Importing `tools.train_voice_candidates` still does not import `torch`, `qwen_tts`, `soundfile`, `faster_whisper`, or embedding models.

## Mandatory Commands

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

## Evidence Required

- Help excerpt for early-stop options.
- Unit test summary.
- Stop defaults/schema excerpt.
- Command exit codes.

## Notes

- Keep this phase contract-only where possible; loop behavior belongs in Phase 2.

---

The agent will print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and SUPERGOAL_PHASE_DONE after completion.
