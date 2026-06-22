# Voice Filtering Policy

## Goal

Keep dataset chunks restricted to human speech only.
For the next training cycle we treat anything outside clear voice speech as non-voice and block it from `train_raw.jsonl`.

## Non-voice taxonomy

- Intro/outro music (instrumental loops, songs, jingles)
- Background music over speech
- Tone/sound effects (beeps, buzzers, ringing, environmental sounds)
- Long room tone / HVAC / crowd noise with no speech
- Low-quality corrupted spans with unstable ASR timestamps

## What is kept as voice

- Chunks with at least one readable linguistic token (`--min_words`, `--min_chars`)
- Chunks inside model speech segments that pass `no_speech_prob` gating
- Chunks whose confidence and low-confidence ratio are acceptable
- Chunks passing required duration constraints (`--min_duration`, `--target_duration`, `--max_duration`)

## Non-voice filter modes

- `off`
  - No filtering beyond existing ASR segmentation and confidence rules.
  - Use only to reproduce historic behavior.
- `hybrid` (default)
  - Removes ASR segments with high `no_speech_prob` (`--max_no_speech_prob`).
  - Calculates voice-overlap per chunk and reports `voice_overlap_ratio`.
- `strict`
  - `hybrid` rules plus per-word voice overlap check (`--min_word_voice_overlap`) before final segment assembly.

## Defaults

- `--voice_filter_mode hybrid`
- `--max_no_speech_prob 0.80`
- `--min_segment_voice_ratio 0.75`
- `--min_word_voice_overlap 0.65`

## Evidence model in reports

- `reasons == insufficient_voice_coverage` means the chunk was rejected due to low overlap with speech spans.
- `voice_overlap_ratio` is added in both accepted and rejected rows.

## Fallback behavior

- If ASR output does not contain `segment.no_speech_prob`, legacy behavior is used for that field (the segment is kept).
- `train_raw.jsonl` schema does **not** change.
