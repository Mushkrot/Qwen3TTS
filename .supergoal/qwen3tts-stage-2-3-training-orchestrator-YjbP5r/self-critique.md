# Self-Critique

## Falsifiability

Finding: the first draft did not make epoch continuation strict enough. "One-epoch jobs" could be misread as independent fresh runs.

Rewrite applied:
- Phase 2 now requires `init_model_path` logging for every epoch.
- Epoch 0 uses the configured base model.
- Epoch N>0 uses the previous checkpoint by default or fails clearly if that mode is unavailable.

Remaining criteria are tied to commands, file existence, JSONL metrics rows, output tree paths, exact eval filenames, or grep/status checks.

## Phase Atomicity

Clean. Each phase has one coherent deliverable:

- Phase 1 defines CLI contract and path model.
- Phase 2 builds prepare/train/checkpoint orchestration and metrics.
- Phase 3 adds eval pack generation.
- Phase 4 wires smoke command and docs.
- Phase 5 verifies and hardens.

## Weakest Dependency

Phase 2 is the weak point because later eval pack generation depends on checkpoint paths and metrics being correct. Mitigation: Phase 2 now requires success and failure tests, explicit previous-checkpoint initialization semantics, and concrete `metrics.jsonl` evidence before Phase 3 starts.
