# Self-Critique

## Falsifiability

Finding: the original Polish & Harden criterion said "all intended links", which was too broad.

Rewrite applied:
- `CHECKPOINT_SELECTION_PROTOCOL` must appear in `README.md`, `docs/EVAL_PHRASE_SET.md`, `docs/PROJECT_STATUS.md`, and `docs/RUNBOOK.md`.
- `CANDIDATE_REVIEW_REPORT` must appear in `README.md`, `docs/RUNBOOK.md`, and `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.

Remaining criteria are yes/no checks tied to file existence, exact strings, command exit codes, or specific content sections.

## Phase Atomicity

Clean. Each phase has one coherent deliverable:

- Phase 1 creates the protocol.
- Phase 2 integrates it with existing docs.
- Phase 3 adds the report template.
- Phase 4 audits and verifies consistency.

## Weakest Dependency

Phase 1 is the weak point: if the protocol is vague, every later doc and template inherits that vagueness. Mitigation: Phase 1 acceptance requires exact metric categories, hard gates, stopping defaults, candidate export shape, final report fields, and dataset-purity precondition.
