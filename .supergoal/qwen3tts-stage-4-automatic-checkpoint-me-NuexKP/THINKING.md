# Thinking: Qwen3TTS Stage 4 Automatic Metrics

## Goals

- Add automatic checkpoint metrics after eval generation.
- Produce a numeric checkpoint score and warnings list for every checkpoint.
- Keep the workflow safe in smoke mode: no real GPU, Whisper, speaker embedding, or heavy Qwen load is required to verify the implementation.
- Preserve generated artifacts as ignored working outputs.

## Constraints

- Existing Stage 2/3 orchestrator files are uncommitted but complete; Stage 4 must build on them, not revert them.
- Raw `datasets/voices/**/Input/*` audio is ignored and must not become a commit candidate.
- `speaker_similarity` is optional until an embedding backend is added. The implementation should record an unavailable warning and redistribute scoring weight rather than fail the run.
- Heavy metric backends must be lazy/explicit. Importing `tools.train_voice_candidates` must still avoid importing `torch`, `qwen_tts`, `soundfile`, or `faster_whisper`.

## Risks

1. Audio metrics on stub sentinel files could be fake unless smoke writes valid WAVs.
   - Mitigation: update stub eval generation to write small valid PCM WAV files or route through a deterministic metric stub with explicit backend metadata.
2. Whisper and speaker similarity backends can make smoke slow or network/model-dependent.
   - Mitigation: provide backend modes (`stub`, `off`, real optional) and tests around unavailable-backend warnings.
3. A single aggregate score can hide hard audio failures.
   - Mitigation: record both per-sample metrics and checkpoint warnings; score is numeric but warnings remain first-class.

## Dependencies

- Metric schema depends on the existing run path model and `metrics.jsonl` writer.
- Audio metrics depend on generated eval files existing.
- Text/speaker backends depend on the metric schema and must be optional.
- Scoring depends on per-sample metric rows.

## Open Questions Assumed

- Use a 0-100 score.
- Use deterministic default thresholds based on the Stage 1 checkpoint protocol.
- Record metric rows in the existing `metrics.jsonl` stream; no database or new artifact store.
- Keep `speaker_similarity` optional with an explicit warning when no backend is configured.

## Best Practices Applied

- Structured JSONL rows for every metric and checkpoint score.
- Lazy optional imports for real audio/text/speaker backends.
- Tests use standard-library generated WAV fixtures and stub transcripts.
- Smoke remains `/tmp`-only and safe.
