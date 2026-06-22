# Thinking: Stage 5 Hard Reject Checkpoint Rules

## Goal

Add a hard reject layer so clearly bad checkpoints are excluded from final candidate selection before the user listens.

## Constraints

- Build on Stage 4 `sample_metrics` and `checkpoint_score` rows.
- Keep real training and heavy ASR/speaker embedding optional.
- Smoke must remain no-GPU and write only under `/tmp/qwen3tts_train_voice_candidates_smoke`.
- Preserve raw `Input/` audio and generated artifact policy.
- Do not claim full automatic early stopping yet; this stage filters final candidates.

## Design Direction

Hard rejects should be first-class decisions, not hidden score penalties:

- Add a `checkpoint_gate` event with `hard_rejected`, `reject_reasons`, and comparison context.
- Add candidate selection metadata that excludes rejected checkpoints.
- Write a small candidate manifest under the run directory.
- Keep rejected checkpoints auditable in `metrics.jsonl`.

## Gate Rules

Initial hard reject rules should cover:

- ASR/text mismatch: low `whisper_text_match`.
- Pace acceleration: current pace materially faster than previous viable checkpoint.
- Clipping: `clipping_ratio_max` above threshold.
- Too short/long: duration ratio out of band.
- Suspected cut: leading/trailing silence anomalies and too-short duration.
- Score collapse: current score sharply worse than previous viable/best checkpoint.

## Risks

1. False rejects remove a usable voice.
   Mitigation: conservative thresholds, explicit reasons, and docs saying rejected checkpoints are auditable.
2. No viable candidates after gates.
   Mitigation: produce an empty/limited manifest with rejection summary instead of silently selecting bad audio.
3. History-dependent pace/score rules drift.
   Mitigation: compare against previous non-rejected checkpoint and unit-test multi-epoch histories.

## Dependencies

- Phase 1 defines the contract.
- Phase 2 implements gate evaluation.
- Phase 3 depends on gate rows and filters candidate selection.
- Phase 4 makes smoke/docs prove the behavior.
- Phase 5 re-runs all checks and validates artifact hygiene.

## Open Assumptions

- This stage creates final candidate metadata/manifest, not a full copied audio export package.
- Top candidate count remains 4 by default.
- Rejected checkpoints remain on disk for audit, but do not appear in final candidates.

