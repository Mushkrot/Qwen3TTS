# Voice filtering rollout notes (Qwen3TTS)

This handoff note captures implementation status, verification evidence, and rollout risks for non-voice filtering in dataset preprocessing.

## Scope covered

- `scripts/voice_filter.py` — reusable voice-region detector API with backend fallback.
- `scripts/build_dataset_from_audio.py` — pre-ASR filtering integration + reject reasons + quarantine outputs.
- CLI compatibility and strict/legacy/off controls.
- documentation and smoke command for non-voice rejection behavior.

## Completion by phase

1) ✅ Voice-purity policy docs and compatibility contract:
   - `docs/VOICE_FILTERING_POLICY.md`
   - `docs/DATASET_CONTRACT.md`
2) ✅ Implemented reusable region detection API:
   - `scripts/voice_filter.py`
3) ✅ Integrated voice-only preprocessing before ASR:
   - `scripts/build_dataset_from_audio.py`
4) ✅ Added purity gates + machine-parseable reject reasons:
   - `scripts/build_dataset_from_audio.py`
5) ✅ Added deterministic quarantine outputs:
   - `filtered_out/removed_segments.jsonl`
   - `filtered_out/run_metadata.json`
   - optional snippet export controlled by `--voice_filter_export_quarantine_snippets`
6) ✅ Runtime controls, compatibility toggles, off mode:
   - `--voice_filter_mode`, `--strict_mode`, `--legacy_mode`, compatibility aliases
7) ✅ Smoke verification command and docs:
   - `scripts/run_voice_filter_smoke.sh` now runs deterministic filter-only checks when `faster-whisper` is unavailable.
   - `scripts/README.md` documents both ASR and filter-only smoke paths plus fallback control.
8) ⚠️ Hardening + full verification is implemented but environment-dependent:
   - non-trainable check steps below were partially blocked by missing `faster-whisper`.

## Verification evidence

Executed in `/ai/Qwen3TTS`:

- `python -m py_compile scripts/voice_filter.py scripts/build_dataset_from_audio.py` ✅
- `python scripts/build_dataset_from_audio.py --help` ✅
- `python scripts/voice_filter.py <speech.wav> --backend silero --sample_rate 16000` ✅ (returns non-empty speech spans)
- `python scripts/voice_filter.py <silence.wav> --backend silero --sample_rate 16000` ❌ by design without `webrtcvad`? returns no regions and enforces strict filter failure path (no fallback-to-full path)
- `bash scripts/run_voice_filter_smoke.sh` ✅ now runnable without `faster-whisper` in filter-only mode;
  use `QWEN3TTS_SMOKE_REQUIRE_ASR=1` for full ASR-run enforcement.

## Known blocker and safe-rollout precondition

- `faster-whisper` is required by `scripts/build_dataset_from_audio.py` and the full smoke path.
- Error observed:
- `ERROR: faster-whisper is required for dataset builder. Details: No module named 'faster_whisper'`
  (pipeline smoke still runs in filter-only mode by default, unless ASR enforcement is forced).
- Install in active virtualenv before final rollout verification.

## Final rollout command sequence

```bash
source .venv/bin/activate
pip install faster-whisper
QWEN3TTS_SMOKE_ASR_MODEL=tiny QWEN3TTS_SMOKE_DEVICE=cpu bash scripts/run_voice_filter_smoke.sh
```

Expected pass criteria:

- `reports/smoke_voice_filter.json` exists and contains at least one `rejected` row with reason
  one of: `no_voice_regions_detected`, `non_voice_ratio_too_high`, `voice_filter_detection_failed`, `transcription_empty`.
- `filtered_out/removed_segments.jsonl` exists and is inspectable.
- Every row in output `manifest` passed all quality and voice-overlap gates.
