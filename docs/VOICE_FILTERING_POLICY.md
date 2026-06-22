# Voice Filtering Policy

## Goal

Keep dataset chunks restricted to human speech only.
For each run, non-voice portions must not enter `train_raw.jsonl`.

## Non-voice taxonomy

- Intro/outro music, jingles, instrumental stings
- Background music over speech
- Tone/sound effects (beeps, buzzers, alerts)
- Long room tone / HVAC / crowd noise with no speech
- Corrupt/garbled regions that fail detector or ASR alignment

## Kept audio policy

- Chunks with readable ASR output (`--min_chars`, `--min_words`)
- Chunks with speech coverage above `--voice_filter_min_coverage`
- Chunks inside detected voice regions and validated by quality gates

Acceptance guard:
- If a chunk does not pass the speech coverage or quality gates, it is rejected and never written to `train_raw.jsonl`.
- In strict mode, detector failures are treated as hard rejects for the source file, rather than passing whole-file fallback audio.

## Filter mode

Modes supported by `scripts/build_dataset_from_audio.py`:

- `off`: legacy behavior (no pre-ASR filtering)
- `silero` (default): pre-ASR region detector via reusable backend
- `vad`: alias for `silero`
- `whisper` / `whisper_only`: fallback voice-region path
- `hybrid`, `strict`, `legacy`: compatibility aliases

Strict mode (`strict` / `--strict_mode`) keeps pre-ASR filtering on and uses `--voice_filter_min_coverage=1.0` by default.

## Backend fallback chain

`voice_filter` runs detectors in strict order:

- `silero`/`vad`/`hybrid`: local Silero VAD model cache first, then WebRTC-VAD when installed, then
  conservative ffmpeg silencedetect fallback only when model-based VAD is unavailable.
- The default local Silero cache path is `/ai/models/torch_cache/hub/snakers4_silero-vad_master`.
  Override it with `QWEN3TTS_SILERO_VAD_DIR` when needed.
- The ffmpeg fallback is energy/silence based, not a speech classifier. If it sees continuous non-silent
  audio with no silence regions, it returns no speech regions instead of passing the whole file.
- `whisper`/`whisper_only`: strict fallback path (`detection_failed` if detector unavailable).
- if all fallbacks fail and full fallback is disabled, the source file is rejected.

## Flags

- `--voice_filter_mode`
- `--voice_filter_min_speech_ms`
- `--voice_filter_min_silence_ms`
- `--voice_filter_merge_gap_ms`
- `--voice_filter_min_coverage`
- `--voice_filter_export_quarantine`
- `--voice_filter_export_quarantine_snippets`
- `--legacy_mode`
- `--strict_mode`

## Report and metadata contract

Purity fields added to each quality report row:

- `speech_ratio`
- `non_voice_ratio`
- `voice_regions_used_ms`
- `source_duration_ms`
- `filter_mode`
- `filter_version`

Stable parseable rejection reasons:

- `no_voice_regions_detected`
- `non_voice_ratio_too_high`
- `too_few_voice_frames`
- `region_too_short`
- `text_too_short`
- `too_few_words`
- `duration_too_short`
- `duration_too_long`
- `avg_confidence_too_low`
- `too_many_low_confidence_words`
- `voice_filter_detection_failed`
- `transcription_empty`

## Quarantine

When enabled, filtered-out spans are written to:

- `output_root/filtered_out/removed_segments.jsonl`
- `output_root/filtered_out/run_metadata.json`

`removed_segments.jsonl` always contains row keys:

- `source_audio`
- `start`
- `end`
- `duration`
- `reason`

Optional snippets are stored under `filtered_out/snippets/` when `--voice_filter_export_quarantine_snippets` is set.

## Storage policy

Raw source audio in `datasets/voices/**/Input/` and generated builder output in
`datasets/voices/**/Ready/` are local working assets and must not be committed.
The repository tracks only scaffolds, docs, code, templates, and small reproducible metadata.

## Compatibility

`build_dataset_from_audio.py` keeps `--min_segment_voice_ratio` as a deprecated alias for
`--voice_filter_min_coverage`.
