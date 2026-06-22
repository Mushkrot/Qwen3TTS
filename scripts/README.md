# Scripts

This folder contains helper scripts for Qwen3TTS training and dataset preparation.

## Automated dataset builder (input audio -> train_raw.jsonl)

Build a dataset from raw audio files with pre-ASR voice filtering:

Project-local voice inputs live under:

```text
datasets/voices/<VoiceName>/Input
```

Write generated output for the same voice under:

```text
datasets/voices/<VoiceName>/Ready/<run_name>
```

Storage rule:
- raw files in `Input/` are ignored local assets and must not be committed;
- generated files in `Ready/` are ignored working outputs unless a small metadata file is intentionally promoted;
- folder scaffolds and README/policy files are tracked.

Example for the current Baritone voice:

```bash
source .venv/bin/activate
python scripts/build_dataset_from_audio.py \
  --input_dir datasets/voices/Baritone/Input \
  --output_root datasets/voices/Baritone/Ready/build_strict \
  --language ru \
  --voice_filter_mode silero \
  --strict_mode \
  --voice_filter_export_quarantine \
  --voice_filter_export_quarantine_snippets \
  --validate_manifest
```

Do not use `/ai/whisper1` as the Qwen3TTS dataset home. That project is only an
external transcription/source project when explicitly needed.

```bash
source .venv/bin/activate
python scripts/build_dataset_from_audio.py \
  --input_dir /path/to/raw_audio \
  --output_root experiments/qwen3_ru_en_speaker_v1/dataset_auto \
  --language ru \
  --voice_filter_mode silero \
  --voice_filter_min_speech_ms 300 \
  --voice_filter_min_silence_ms 250 \
  --voice_filter_merge_gap_ms 150 \
  --voice_filter_min_coverage 0.75 \
  --voice_filter_export_quarantine \
  --use_whisperx_align \
  --validate_manifest
```

Output:
- chunks: `.../dataset_auto/chunks/*.wav` (24k mono)
- transcripts: `.../dataset_auto/transcripts/*.txt`
- manifest: `.../dataset_auto/manifests/train_raw.jsonl`
- quality report: `.../dataset_auto/reports/quality_report.{json,csv}`
- optional quarantine: `.../dataset_auto/filtered_out/removed_segments.jsonl`, snippets: `.../dataset_auto/filtered_out/snippets/*.wav`
- run metadata: `.../dataset_auto/filtered_out/run_metadata.json`

Optional:
- pass fixed reference voice with `--ref_audio /path/to/ref.wav`
- tune segmentation with `--min_pause`, `--target_duration`, `--max_duration`
- tune text quality with `--min_words`, `--min_chars`, `--min_avg_confidence`, `--max_low_conf_ratio`
- enable WhisperX boundary refinement with `--use_whisperx_align`

`voice_filter_mode`:
- `off`: legacy mode, no pre-ASR filtering (compatibility path)
- `silero` (default): local Silero VAD first, then conservative fallbacks
- `vad`: same behavior as `silero`
- `whisper` / `whisper_only`: whisper-style fallback path
- `hybrid`, `strict`, `legacy`: compatibility aliases

`strict` / `--strict_mode` enforces full-voice purity by default with `--voice_filter_min_coverage=1.0` (unless explicitly overridden).

Strictness controls:
- `--voice_filter_min_speech_ms` — minimum region length kept as speech
- `--voice_filter_min_silence_ms` — minimum silence length considered split/gap
- `--voice_filter_merge_gap_ms` — merges close speech regions
- `--voice_filter_min_coverage` — minimum speech ratio inside final chunk
- `--voice_filter_reject_initial_seconds` — reject opening chunks, useful for intro music/title cards

Validation and notes:
- `--voice_filter_export_quarantine` emits filtered-out regions for audit.
- Rejection reasons are machine-parseable, including `no_voice_regions_detected`, `non_voice_ratio_too_high`, `initial_window_rejected`, `too_few_voice_frames`, `region_too_short`, `too_many_low_confidence_words`, and others.

WhisperX notes:
- WhisperX is optional, but if `--use_whisperx_align` is enabled the run is fail-fast.
- If WhisperX is unavailable or alignment fails, the script stops with an explicit error.
- Install manually when needed:

```bash
source .venv/bin/activate
pip install whisperx
```

## Smoke voice filter verification

Run the smoke command to validate non-voice filtering behavior on a synthetic input set:

```bash
bash scripts/run_voice_filter_smoke.sh
```

The script uses `.venv/bin/python` automatically when it exists. Set `QWEN3TTS_PYTHON=/path/to/python`
to force another interpreter.

If the historical frozen smoke sample is missing but local Baritone input exists, the command uses
`datasets/voices/Baritone/Input/Baritone1.mp3` from a stable speech offset and runs filter-only smoke by default. This avoids
treating arbitrary raw source audio as a stable ASR fixture while still validating non-voice rejection.

If `faster-whisper` is missing, the command also falls back to filter-only smoke and still writes
deterministic `reports/smoke_voice_filter.json` and `filtered_out/removed_segments.jsonl` files.

Filter-only pass criteria are explicit:
- `voice.wav` must be accepted.
- `music.wav` and `silence.wav` must be rejected.
- `mixed.wav` must be rejected with an explicit non-voice reason.

Control fallback behavior with:

```bash
QWEN3TTS_SMOKE_REQUIRE_ASR=1 bash scripts/run_voice_filter_smoke.sh
```

If `QWEN3TTS_SMOKE_REQUIRE_ASR=1`, the command exits with error when `faster-whisper` is absent or
when the chosen source does not produce accepted ASR rows.

Use a known-good short speech source for full ASR smoke:

```bash
source .venv/bin/activate
QWEN3TTS_SMOKE_REQUIRE_ASR=1 \
QWEN3TTS_SMOKE_VOICE_SOURCE=/path/to/known-short-speech.wav \
QWEN3TTS_SMOKE_LANGUAGE=ru \
QWEN3TTS_SMOKE_ASR_MODEL=tiny \
QWEN3TTS_SMOKE_DEVICE=cpu \
bash scripts/run_voice_filter_smoke.sh
```

Use offline-only mode when ASR dependencies/models are not reachable:

```bash
QWEN3TTS_SMOKE_FORCE_FILTER_ONLY=1 bash scripts/run_voice_filter_smoke.sh
```

This forces filter-only smoke checks even if `faster-whisper` is installed in the environment.

Expected output:
- printed acceptance and rejection summary,
- generated manifest/report under `/tmp/qwen3tts_voice_filter_smoke/output/...`,
- `quality_report` contains at least one explicit non-voice rejection reason,
- `filtered_out/removed_segments.jsonl` exists and can be reviewed.

## Validation

```bash
source .venv/bin/activate
python scripts/validate_manifest.py --input_jsonl experiments/qwen3_ru_en_speaker_v1/manifests/train_raw.jsonl
```

Current state: `train_raw.jsonl` is not present until a dataset build or manual manifest handoff creates it.

## Preprocess (`audio_codes`)

```bash
bash scripts/run_prepare_data.sh \
  experiments/qwen3_ru_en_speaker_v1/manifests/train_raw.jsonl \
  experiments/qwen3_ru_en_speaker_v1/manifests/train_with_codes.jsonl
```

## Train (0.6B)

```bash
bash scripts/run_sft_0_6b.sh \
  experiments/qwen3_ru_en_speaker_v1/manifests/train_with_codes.jsonl \
  experiments/qwen3_ru_en_speaker_v1/runs/sft_0_6b_run1
```

## Training orchestrator (prepare -> epoch -> checkpoint -> eval pack)

Use the project-local orchestrator when a ready dataset manifest already exists
and you want repeatable one-epoch training steps with metrics and eval samples:

```bash
python tools/train_voice_candidates.py \
  --voice_name Baritone \
  --train_raw_jsonl datasets/voices/Baritone/Ready/<run_name>/manifests/train_raw.jsonl \
  --output_root experiments/qwen3_ru_en_speaker_v1/runs \
  --run_name baritone_sft_candidates_001 \
  --min_epochs 2 \
  --max_epochs 6 \
  --patience 2 \
  --top_candidates 4 \
  --speaker_name speaker_target
```

When `--output_root` is an experiment `runs` directory, the review pack defaults
to the sibling samples tree:

```text
experiments/qwen3_ru_en_speaker_v1/samples/Baritone/baritone_sft_candidates_001/candidate_review/
```

Use `--candidate_review_root` to override that location.

Real mode is GPU-heavy. It runs `scripts/run_prepare_data.sh`, then one
`NUM_EPOCHS=1` training job per requested epoch through `scripts/run_sft_0_6b.sh`,
then `scripts/run_infer_sample.py` once for each default eval phrase. The
orchestrator evaluates each checkpoint before deciding whether to continue.

Safe smoke mode does not load Qwen, Torch, or soundfile. It writes sentinel
artifacts under `/tmp/qwen3tts_train_voice_candidates_smoke`:

```bash
bash scripts/run_train_voice_candidates_smoke.sh
```

Expected smoke artifacts:

- `manifests/train_with_codes.jsonl`
- `metrics.jsonl`
- `candidate_manifest.json`
- `candidate_review/ranking.md`
- `candidate_review/metrics.jsonl`
- `candidate_review/candidate_A_epochN/{01_en_short.wav,02_en_long.wav,03_en_calm.wav,04_ru_short.wav,05_ru_long.wav}`
- `train/epoch-0/checkpoint-epoch-0/STUB_CHECKPOINT.txt`
- `eval/epoch-N/{01_en_short.wav,02_en_long.wav,03_en_calm.wav,04_ru_short.wav,05_ru_long.wav}`

The smoke also verifies automatic metric, gate, and stopping rows in
`metrics.jsonl`:

- five `sample_metrics` rows per completed epoch, one per eval phrase;
- one `checkpoint_score` row per checkpoint;
- numeric `score`, `sample_count`, `metric_summary`, and `warnings`.
- one `checkpoint_gate` row per checkpoint;
- one `early_stop_decision` row per completed epoch;
- one final `run_stop` row;
- one `candidate_selection` row after the epoch loop;
- one `candidate_review_export` row after the review pack is written;
- a parseable `candidate_manifest.json` with `candidate_floor`,
  `stop_summary`, `candidate_review`, and no hard-rejected checkpoint epoch in
  `candidates`;
- a candidate review tree with `candidate_A_epochN` style folders, copied WAVs,
  `ranking.md`, and copied `metrics.jsonl`.

Default semi-auto stopping values are `min_epochs=2`, `max_epochs=6`,
`patience=2`, `top_candidates=4`, and `candidate_floor=3`. The smoke should
complete more than one stub epoch and stop before `max_epochs=6`. It prints the
stop reason, epochs completed, selected candidate count, and rejected
checkpoint count. It also prints candidate review directory, exported candidate
count, ranking path, copied metrics path, review tree listing, and a
`ranking.md` excerpt.

Always-computed audio metrics are `duration_ratio`, `pace_chars_per_sec`,
`pace_words_per_sec`, `rms_dbfs`, `clipping_ratio`, `leading_silence_ms`, and
`trailing_silence_ms`. `whisper_text_match` is produced by the configured text
match backend; stub mode returns a deterministic numeric match, `off` records an
unavailable warning, and `--text_match_backend faster-whisper` lazily loads the
real ASR backend. Configure it with `--text_match_model`,
`--text_match_device`, `--text_match_compute_type`, or the matching
`QWEN3TTS_TEXT_MATCH_*` environment variables. `speaker_similarity` is optional:
use `--speaker_similarity_backend stub` only for contract tests until a real
embedding backend is wired. Missing optional backends keep the score numeric and
add warnings such as `speaker_similarity_unavailable`.

Generated `metrics.jsonl` files, copied review metrics, review WAVs,
checkpoints, eval WAVs, command logs, ranking files, and training outputs are
ignored working artifacts. Generated `candidate_manifest.json` files are also
run artifacts, not commit targets. Raw audio in voice `Input/` folders is also
not a commit target. Do not commit any of these files. Commit only the
orchestrator code, tests, docs, small templates, and intentional small
selection metadata.

Hard reject reasons currently emitted by the orchestrator:

- `asr_text_mismatch`: ASR/text match is too low;
- `pace_accelerated`: speech is noticeably faster than the previous
  non-rejected checkpoint;
- `audio_clipping`: clipping exceeds the configured limit;
- `duration_too_short` or `duration_too_long`: generated speech falls outside
  the duration-ratio band;
- `suspected_cut`: short duration plus almost no trailing silence suggests an
  abrupt cutoff;
- `score_drop`: score is sharply worse than the previous non-rejected
  checkpoint.

Rejected checkpoints stay auditable in `metrics.jsonl` and
`candidate_manifest.json.rejected_checkpoints`, but they are excluded from
`candidate_manifest.json.candidates`.

Current stop reasons:

- `min_epochs_pending`: continue until the minimum epoch floor is reached;
- `patience_exhausted`: stop after the configured patience window has no score
  improvement;
- `quality_degradation`: stop when a hard-rejected checkpoint indicates quality
  degradation after `min_epochs`;
- `max_epochs_reached`: stop at the configured epoch cap;
- hard failure: prepare/train/eval command failures abort the run and write a
  `failure` row.

Naturalness is currently represented by proxy metrics and hard gates. The
system narrows the run without owner listening after every epoch. Stage 7
exports the selected candidates into `candidate_review/`; the owner still
selects the final voice from those exported candidates.

## Winner selection (human choice -> selected checkpoint)

After listening to `candidate_review/ranking.md` and the exported candidate
folders, record the winner:

```bash
python tools/select_voice_candidate.py \
  --candidate B \
  --candidate_review_dir experiments/qwen3_ru_en_speaker_v1/samples/Baritone/baritone_sft_candidates_001/candidate_review
```

`--candidate` accepts `A`, `B`, `2`, or `candidate_B_epoch1`. The script reads
`candidate_manifest.json.candidates`, rejects choices that are missing or only
present in `rejected_checkpoints`, and writes:

- `selected_checkpoint.json`;
- `experiment_status.json`;
- `candidate_manifest.json.winner_selection`.

It does not copy checkpoint directories, generated WAVs, copied metrics, or raw
audio. In the normal `experiments/<experiment>/runs/<voice>/<run_name>/` layout,
the durable pointer lives at `experiments/<experiment>/selected_checkpoint.json`.
In temp/smoke layouts, it lives under the run directory.

Selection smoke:

```bash
bash scripts/run_select_voice_candidate_smoke.sh
```

The smoke creates a Stage 7 review pack, selects candidate B, verifies that the
selected metadata and local experiment status point to candidate B's checkpoint
and not candidate A's checkpoint, and verifies no heavy artifact copy was made.

Current MVP: epoch-by-epoch training, fixed eval audio generation, simple
metrics, hard rejects, semi-auto early stopping, top-4 candidate export, and
human winner selection. Future improvements are speaker similarity, smarter
scoring/naturalness signals, richer Markdown or HTML reports, and automatic
recommended-candidate assistance.

## Quick inference

```bash
source .venv/bin/activate
python scripts/run_infer_sample.py \
  --checkpoint experiments/qwen3_ru_en_speaker_v1/runs/sft_0_6b_run1/checkpoint-epoch-2 \
  --speaker speaker_target \
  --output_wav experiments/qwen3_ru_en_speaker_v1/samples/run1_sample.wav
```

Note: if `flash-attn` is not installed, switch `attn_implementation` in `run_infer_sample.py` to an implementation supported by your runtime.
Current default is `sdpa`.
