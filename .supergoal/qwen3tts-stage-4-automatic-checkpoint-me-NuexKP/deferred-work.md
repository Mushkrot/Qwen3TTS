# Deferred Work Checks

## Requires Phase 1

- Metric-specific unit tests for the new schema and helper module.
- Any direct invocation of a new `tools/checkpoint_metrics.py` module if the executor chooses to create one.

## Requires Phase 2

- Audio metric fixture tests that need valid generated WAVs and metric extraction helpers.

## Requires Phase 3

- Text-match and optional speaker-similarity backend tests.
- Checkpoint aggregate scoring tests.

## Requires Phase 4

- Dedicated metrics smoke wrapper if added.
- Documentation grep for metric-score fields after docs are updated.

## External / Environment Work

These are not pre-flight or smoke requirements:

- real Faster-Whisper transcription;
- real speaker-embedding similarity;
- real GPU inference/training;
- downloading any model weights.

The safe implementation must still produce numeric checkpoint scores and warnings in stub/smoke mode.
