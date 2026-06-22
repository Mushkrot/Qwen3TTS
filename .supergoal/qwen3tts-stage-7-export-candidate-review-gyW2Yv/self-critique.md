# Self-Critique

## Falsifiability

Finding: Phase 3 originally allowed `metrics.jsonl` to be "byte-identical or content-equivalent", which was too soft.

Rewrite applied:
- Phase 3 now requires the copied review `metrics.jsonl` to be byte-identical to the run metrics.

## Phase Atomicity

Clean. Each phase has one main verification surface:
- Phase 1: contract helpers and parser/schema.
- Phase 2: exporter implementation.
- Phase 3: smoke and edge coverage.
- Phase 4: documentation.
- Phase 5: hardening audit.

## Weakest Dependency

Phase 2 is the critical dependency. If the exporter writes the wrong path or uses anything other than manifest candidates, Phases 3 and 4 can accidentally document or test the wrong behavior. The plan mitigates this with manifest metadata, missing-audio failure tests, and smoke tree assertions.
