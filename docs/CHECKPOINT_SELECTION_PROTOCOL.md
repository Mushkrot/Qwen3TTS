# Checkpoint Selection Protocol

## Purpose

This document defines how this project should decide which Qwen3-TTS training checkpoints become the final voice candidates for human review.

The protocol is for semi-automatic checkpoint selection:

- automatic gates reject obviously bad checkpoints;
- automatic scores rank viable checkpoints;
- the final winner is selected by a human from a small candidate set.

Stage 1 was documentation only. Stage 2/3 adds the first project-local
orchestrator in `tools/train_voice_candidates.py`: it can run `prepare_data`,
train one epoch at a time, record checkpoints, and generate a fixed eval pack
after each checkpoint. Stage 4 adds automatic `sample_metrics` and
`checkpoint_score` rows with numeric scores and warnings. Stage 5 adds
`checkpoint_gate` hard-reject rows plus `candidate_selection` metadata and a
`candidate_manifest.json` that excludes hard-rejected checkpoints from the
review set. Stage 6 implements project-local semi-auto early stopping with
`early_stop_decision` and `run_stop` rows. Stage 7 exports the selected
candidates into a candidate review pack with copied eval WAVs, `ranking.md`,
and a copied `metrics.jsonl`, and appends a `candidate_review_export` row to
the run metrics. Stage 8/9 adds `tools/select_voice_candidate.py` so the owner
can persist the human-selected winner as `selected_checkpoint.json`, local
experiment status, and a `candidate_manifest.json.winner_selection` block. This
still does not claim that upstream Qwen3-TTS has native optimal stopping, and
it still leaves the final voice choice to the owner.

## Scope

In scope:

- single-speaker Qwen3-TTS fine-tuning for the current Sub-task #1;
- checkpoint comparison across one training run;
- selection of 3-4 review candidates;
- repeatable evaluation audio and reporting.

Out of scope:

- multi-speaker training;
- synchronization, dubbing, muxing, or video alignment;
- committing generated WAVs, checkpoints, or raw input audio;
- replacing the human listening decision.

## Required Pre-Training Gate

Dataset quality is a hard precondition. Do not start SFT when the dataset report shows music, music-like intros/outros, sustained non-speech, corrupt audio, or low-confidence transcripts entering `train_raw.jsonl`.

Before training, verify the dataset against:

- `docs/DATASET_CONTRACT.md`
- `docs/VOICE_FILTERING_POLICY.md`
- `docs/ARTIFACT_POLICY.md`

For Baritone-style audiobook sources, use the current conservative build policy from the runbook: `--voice_filter_mode silero --strict_mode --voice_filter_reject_initial_seconds 30`, then inspect the quality report for `initial_window_rejected` and spot-check accepted chunks by ear.

## Fixed Evaluation Phrases

Use `docs/EVAL_PHRASE_SET.md` and `tools/train_voice_candidates.py` as the
canonical phrase sources. The current fixed eval pack contains three English
phrases and two Russian sanity phrases, all generated for every checkpoint
under review. English generation remains the primary product objective; Russian
phrases help catch identity or stability regressions.

## Candidate Artifacts

The project-local orchestrator writes generated artifacts under deterministic,
ignored working paths. For candidate-review exports, keep this shape:

```text
experiments/qwen3_ru_en_speaker_v1/
  runs/<voice_name>/<run_name>/
    candidate_manifest.json
    metrics.jsonl
  samples/<voice_name>/<run_name>/candidate_review/
    candidate_A_epoch0/
    candidate_B_epoch1/
    candidate_C_epoch2/
    candidate_D_epoch3/
    metrics.jsonl
    ranking.md
```

Generated metric JSONL files, WAV files, model checkpoints, command logs, and
dataset chunks are working artifacts and must not be committed. Generated
`candidate_manifest.json` files and candidate review packs are run artifacts
too: keep them in ignored run/sample directories unless a small sanitized
metadata snapshot is deliberately promoted.
Small winner-selection metadata may be preserved intentionally when it is the
durable record of the chosen voice. It must not duplicate checkpoints, WAVs,
copied metrics, or raw source audio.
Raw audio in voice `Input/` folders is also not a commit target. Commit only
docs, code, tests, small templates, small reproducible metadata, and scaffolds.

## Automatic Metrics

Automatic metrics are evidence, not final truth. They should reject obvious failures and rank candidates for listening review.

| Metric | Direction | Use |
|---|---:|---|
| `whisper_text_match` | higher is better | Check whether generated speech matches the prompt text. Stub mode is deterministic; the real backend boundary is `faster-whisper`. |
| `duration_ratio` | near target is better | Compare generated duration with expected duration from phrase length and baseline pace. |
| `pace_chars_per_sec` | within band is better | Detect rushed or slow output, especially epoch-to-epoch acceleration. |
| `pace_words_per_sec` | within band is better | Secondary pace proxy for languages/prompts where word count is meaningful. |
| `rms_dbfs` | within band is better | Detect overly quiet or overly loud output. |
| `clipping_ratio` | lower is better | Reject distorted files. |
| `leading_silence_ms` | within band is better | Detect bad starts or long dead air. |
| `trailing_silence_ms` | within band is better | Detect abrupt endings or excessive tail silence. |
| `onset_anomaly` | lower is better | Detect noisy, breathy, or unstable starts when measurable. |
| `offset_anomaly` | lower is better | Detect cutoffs, clicks, or unstable endings when measurable. |
| `loss_last` / `loss_min` | lower trend can help | Supporting signal parsed from the train log; never promote a checkpoint on loss alone. |
| `speaker_similarity` | higher is better | Optional if a speaker-embedding backend is available and documented. |

Stage 4 writes these metrics as append-only JSONL events in each run's
`metrics.jsonl`:

- `sample_metrics`: one row per eval WAV with `duration_ratio`,
  `pace_chars_per_sec`, `pace_words_per_sec`, `rms_dbfs`, `clipping_ratio`,
  `leading_silence_ms`, `trailing_silence_ms`, `whisper_text_match`, optional
  `speaker_similarity`, and per-sample `warnings`;
- `checkpoint_score`: one row per checkpoint with numeric `score`,
  `sample_count`, `metric_summary`, and a checkpoint-level `warnings` list.

Always-computed metrics are the WAV-derived duration, pace, RMS, clipping, and
silence values. `whisper_text_match` depends on `--text_match_backend`; use
`--text_match_backend faster-whisper` plus `--text_match_model`,
`--text_match_device`, and `--text_match_compute_type` for real ASR prompt
matching. `speaker_similarity` depends on `--speaker_similarity_backend` and may
be null. Unavailable optional metrics add warnings but must not prevent a
numeric checkpoint score.

The project has external evidence that later epochs can make generated speech progressively faster in upstream fine-tuning (`QwenLM/Qwen3-TTS#179`, linked PR `#178` still unmerged at the time this protocol was written). Therefore pace metrics are mandatory for semi-automatic stopping. Naturalness is currently represented by proxy metrics and hard gates, not by a learned perceptual quality model.

## Hard Reject Gates

Stage 5 hard gates are implemented in `tools/train_voice_candidates.py` after
each `checkpoint_score`. A rejected checkpoint remains auditable in
`metrics.jsonl` and in `candidate_manifest.json.rejected_checkpoints`, but it
must not appear in `candidate_manifest.json.candidates`.

Current hard reject reasons:

| Reason | Rejects when |
|---|---|
| `asr_text_mismatch` | ASR/text match falls below the configured threshold. |
| `pace_accelerated` | Speech becomes materially faster than the previous non-rejected checkpoint. |
| `audio_clipping` | Clipping ratio exceeds the configured threshold. |
| `duration_too_short` | Mean duration ratio is below the allowed band. |
| `duration_too_long` | Mean duration ratio is above the allowed band. |
| `suspected_cut` | Duration is short and trailing silence is near zero, indicating a likely cutoff. |
| `score_drop` | Score is sharply worse than the previous non-rejected checkpoint. |

Dataset-level failures such as intro music, non-speech, corrupt input, or bad
transcripts are handled before training by the dataset gate. Failed eval
generation or invalid WAV metrics become score warnings today and should be
promoted to hard gates in a later implementation if real runs show they can
otherwise reach the candidate set.

Hard gates are conservative. A false reject is acceptable; a clearly bad
checkpoint should not reach the user's listening set.

## Soft Ranking Score

After hard gates, rank remaining checkpoints with a weighted score. Initial weights:

| Component | Weight |
|---|---:|
| Text match / intelligibility proxy | 20 |
| Pace and duration stability | 25 |
| Onset and offset quality proxy | 15 |
| Audio level and clipping health | 10 |
| Speaker similarity, when available | 20 |
| Loss stability, as supporting evidence | 10 |

In the current implementation, unavailable `speaker_similarity` adds
a warning and a small score penalty while keeping the checkpoint score numeric.
The candidate selector ranks only non-rejected checkpoints, with up to
`--top_candidates` entries written to `candidate_manifest.json` and exported to
the candidate review pack. Future metric-weight changes should record the
policy in `metrics.jsonl`, `candidate_manifest.json`, or the review report.

Tie break order:

1. fewer hard-gate warnings;
2. better pace stability;
3. better onset/offset health;
4. earlier epoch.

Prefer the earliest checkpoint when candidates are effectively tied. This matches the local project history where later epochs sometimes improved one axis while hurting naturalness or starts/ends.

## Semi-Auto Early Stopping

Stage 6 implements semi-auto early stopping in `tools/train_voice_candidates.py`.
The orchestrator trains one epoch at a time, evaluates the checkpoint, writes
`checkpoint_score` and `checkpoint_gate`, then appends an
`early_stop_decision`. When the decision stops the loop, the run writes a final
`run_stop` row and then writes `candidate_manifest.json`.

```text
min_epochs = 2
max_epochs = 6
patience = 2
top_candidates = 4
candidate_floor = 3
tie_break = earliest_checkpoint
```

Default CLI values match the table above. Override them only when the run has a
clear owner-approved reason.

Current stop and decision reasons:

- `min_epochs_pending`: continue because fewer than `min_epochs` have completed;
- `score_improved`: continue because the current viable score improved;
- `patience_pending`: continue while non-improvement has not yet reached
  `patience`;
- `patience_exhausted`: stop after `patience` consecutive non-improving viable
  epochs;
- `quality_degradation`: stop after `min_epochs` when the current checkpoint is
  hard-rejected for quality degradation such as pace acceleration, clipping,
  bad duration, suspected cutoff, ASR mismatch, or sharp score drop;
- `max_epochs_reached`: stop at `max_epochs` even if scores keep improving;
- `no_viable_checkpoint`: continue/mark limited when no viable checkpoint exists.

Hard failures such as prepare/train/eval command failure still abort the run and
write a `failure` row. They are not candidate checkpoints.

If fewer than `candidate_floor` viable candidates exist when the loop stops,
`candidate_manifest.json.status` is `limited` and
`limited_reasons` includes `candidate_count_below_floor`. The manifest records
`candidate_floor` and a `stop_summary` copied from the final `run_stop` row.

## Candidate Export

Stage 7 exports at most `top_candidates` selected candidates into a review pack.
Only `candidate_manifest.json.candidates` are copied; rejected checkpoints stay
auditable in `candidate_manifest.json.rejected_checkpoints` and are not copied.
Candidate labels are rank labels for review convenience, not a final voice
decision:

```text
candidate_A_epoch0/
candidate_B_epoch1/
candidate_C_epoch2/
candidate_D_epoch3/
```

Each candidate folder contains the same generated eval phrase files with stable
names from `docs/EVAL_PHRASE_SET.md`. The review root defaults to:

```text
<output_root_parent>/samples/<voice_name>/<run_name>/candidate_review/
```

when `--output_root` is named `runs`, such as
`experiments/qwen3_ru_en_speaker_v1/runs`. For smoke/temp roots whose
`--output_root` is not named `runs`, the default is
`<run_dir>/candidate_review/`. Override either default with
`--candidate_review_root`.

The review pack contains:

- `candidate_A_epochN/` through `candidate_D_epochN/`, up to
  `--top_candidates`;
- the fixed eval WAV files under each candidate folder;
- `ranking.md` with rank, epoch, checkpoint path, score, selection reason,
  risks/warnings, and audio files to listen to;
- copied `metrics.jsonl`, kept byte-identical to the run metrics after
  `run_end`.

The orchestrator also records `candidate_review` metadata in
`candidate_manifest.json`: review directory, ranking path, metrics copy path,
exported candidate count, exported epochs, and candidate directories. The same
review-pack summary is appended as a `candidate_review_export` row in
`metrics.jsonl` before the final copied metrics file is synchronized.

The report must include:

- run id and timestamp;
- voice name;
- dataset build path and manifest path;
- base model;
- training command summary;
- epoch range evaluated;
- metrics backend versions;
- hard-gate thresholds;
- candidate ranking table;
- per-candidate warnings;
- sample paths;
- human listening checklist;
- final user choice section.

Use `docs/templates/CANDIDATE_REVIEW_REPORT.md` as the human-facing report template.

## Human Selection Gate

The user should listen only to the 3-4 candidates selected by
`candidate_manifest.json` and exported under `candidate_review/`, not every
epoch. Semi-auto stopping decides when the run has enough evidence to stop; it
does not choose the final voice. The selected candidate becomes the active voice
candidate only after the user records the final choice:

```bash
python tools/select_voice_candidate.py \
  --candidate B \
  --candidate_review_dir experiments/qwen3_ru_en_speaker_v1/samples/<voice_name>/<run_name>/candidate_review
```

The selector accepts `A`, `B`, a numeric rank such as `2`, or a full label such
as `candidate_B_epoch1`. It reads only `candidate_manifest.json.candidates`;
checkpoints that exist only in `candidate_manifest.json.rejected_checkpoints`
are rejected. On success it writes:

- `selected_checkpoint.json` with candidate label/rank/epoch, score,
  checkpoint path, review dir, and source manifest path;
- `experiment_status.json` with `active_checkpoint` and `primary_checkpoint`;
- `candidate_manifest.json.winner_selection`.

For normal experiment layouts, `selected_checkpoint.json` is written at
`experiments/<experiment>/selected_checkpoint.json`. For temp/smoke layouts, it
is written under the run directory. Selection writes small metadata only and
does not copy checkpoint directories, generated WAVs, copied metrics, or raw
audio.

The report should preserve the reason for the choice because the best checkpoint may not be the highest automatic score when human naturalness, voice identity, or delivery feel differs from proxy metrics.

## Current MVP And Later Improvements

The current MVP includes epoch-by-epoch training, fixed eval audio generation,
simple automatic metrics, hard-reject gates, semi-auto early stopping, top-4
candidate export, and human winner selection through
`tools/select_voice_candidate.py`.

Deferred improvements:

- real speaker-similarity embedding backend;
- smarter scoring and a better naturalness signal;
- richer Markdown or HTML report generation;
- automatic recommended-candidate logic for review assistance.

Do not patch upstream `sft_12hz.py` to pretend it has built-in early stopping. Keep orchestration in project-local scripts so upstream behavior remains understandable and reproducible.
