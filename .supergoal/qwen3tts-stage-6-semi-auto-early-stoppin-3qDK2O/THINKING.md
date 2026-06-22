# Thinking: Qwen3TTS Stage 6 Semi-Auto Early Stopping

## Goals

- Implement semi-automatic early stopping in `tools/train_voice_candidates.py`.
- Use default policy requested by the owner: `min_epochs=2`, `max_epochs=6`, `patience=2`, `top_candidates=4`.
- Stop without listening after every epoch when there is no score improvement for two consecutive epochs or when a quality/degradation gate fires after the minimum epoch floor.
- Preserve Stage 5 behavior: every checkpoint still receives score and hard-gate rows, rejected checkpoints remain auditable, and final candidates come from non-rejected checkpoints.

## Constraints

- Do not launch real GPU training while implementing or verifying this stage.
- Keep tests and smoke deterministic in stub mode.
- Keep generated metrics, eval WAVs, checkpoints, candidate manifests, and raw `Input/` audio out of commit scope.
- Keep heavy imports lazy; importing `tools.train_voice_candidates` must remain standard-library only.

## Risks

1. **Stopping too early with only one or two useful candidates.** Mitigation: enforce `min_epochs=2`, keep `candidate_floor=3`, mark manifests limited when fewer than the floor are viable, and test no-improvement behavior with at least three stub epochs.
2. **History logic miscounts rejected checkpoints as improvements.** Mitigation: evaluate patience against non-rejected viable gates only and add synthetic multi-epoch unit tests.
3. **Degradation rules duplicate hard rejects inconsistently.** Mitigation: base degradation stop reasons on `checkpoint_gate.reject_reasons` and keep a separate `early_stop_decision` event explaining the stop.

## Dependencies

- Stage 4 score rows and metric summaries already exist.
- Stage 5 hard-reject `checkpoint_gate` rows and candidate selection already exist.
- The orchestrator currently loops `for epoch in range(args.max_epochs)` and writes `candidate_selection` after the loop; Stage 6 should insert a stop decision after each gate and break before the next epoch.

## Open Questions / Assumptions

- "Naturalness" is not directly measurable yet; Stage 6 will use the existing proxies: score, duration/pace/silence warnings, and hard rejects such as `pace_accelerated`, `suspected_cut`, and `score_drop`.
- Smoke may run multiple stub epochs to prove early stopping, because no GPU or heavy model is loaded in stub mode.
- `max_epochs` default should move to 6; callers can override for targeted tests by explicitly setting `--min_epochs 1 --max_epochs 1`.

## Best Practices Applied

- Keep stop policy as a serialized contract and CLI surface.
- Emit append-only JSONL events for every stop decision.
- Separate "why did training stop" from "which candidates were selected."
- Verify with tests for min floor, patience, max cap, degradation stop, manifest contents, help text, import safety, smoke output, and docs no-overclaim.
