SUPERGOAL_PHASE_START
Phase: 2 of 4 — Align Eval Docs
Task: Link the new protocol into the existing documentation canon without duplicating or contradicting the current eval policy.
Type: brownfield, documentation, ML workflow
Mandatory commands: git diff --check
Acceptance criteria: 5
Evidence required: rg output, command exit code
Depends on phases: 1

## Why

The new protocol should become the project route for checkpoint selection while preserving the existing fixed phrase set and project status.

## Work

- Update `docs/EVAL_PHRASE_SET.md` to reference `docs/CHECKPOINT_SELECTION_PROTOCOL.md` for checkpoint selection.
- Preserve the existing five fixed English phrases.
- Update `docs/PROJECT_STATUS.md` to say the current state is documented semi-automatic candidate review protocol, not implemented full auto-stop.
- Update `docs/RUNBOOK.md` with a short checkpoint-selection/review section.
- Update `README.md` documentation index with the new protocol and report template.

## Acceptance criteria (all must pass — verify each in transcript)

- `docs/EVAL_PHRASE_SET.md` references `docs/CHECKPOINT_SELECTION_PROTOCOL.md` for checkpoint selection and preserves the existing fixed English phrases.
- `docs/PROJECT_STATUS.md` describes the current policy as semi-automatic candidate review protocol pending future orchestration.
- `docs/RUNBOOK.md` includes a short checkpoint-selection/review section that points to the protocol and report template.
- `README.md` documentation index includes the new protocol and report template.
- No doc says the project already has fully automatic optimal stopping implemented.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `git diff --check`

## Evidence required in transcript

- Print `rg -n "CHECKPOINT_SELECTION_PROTOCOL|CANDIDATE_REVIEW_REPORT|automatic optimal|fully automatic" README.md docs`.
- Print `git diff --check` exit code.

## Notes

- Keep wording conservative: the protocol prepares later automation but does not claim the feature exists yet.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-1-checkpoint-selection-pr-KHbXIj/PROTOCOL.md without further
instruction needed here.
