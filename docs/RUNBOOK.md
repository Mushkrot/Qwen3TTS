# Runbook

## Start-of-session checks

```bash
cd /ai/Qwen3TTS
git status --short --branch
git status --ignored --short
```

Use Recallant per `AGENTS.md` before non-trivial work.

## Runtime setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

Verification:

```bash
source .venv/bin/activate
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
python -c "import soundfile; print('soundfile ok')"
python -c "import faster_whisper; print('faster_whisper ok')"
python -c "import qwen_tts; print('qwen_tts ok')"
```

Current 2026-06-22 verified environment:

- `.venv` exists;
- `torch` imports and CUDA is visible;
- `soundfile`, `faster_whisper`, and `qwen_tts` import;
- `flash-attn` is still optional and not required for the default `sdpa` path.

## Smoke checks

Syntax/static checks:

```bash
python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts
bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh
python scripts/build_dataset_from_audio.py --help
python scripts/voice_filter.py --help
python scripts/validate_manifest.py --help
python scripts/run_infer_sample.py --help
```

Default local voice-filter smoke:

```bash
bash scripts/run_voice_filter_smoke.sh
```

When the historical frozen sample is missing, the script uses local Baritone input and runs filter-only smoke by default.
This validates the voice/non-voice rejection path without treating raw Baritone audio as a stable ASR fixture.
It uses `.venv/bin/python` automatically when present.
Expected filter-only result: speech accepted, music rejected, silence rejected, and mixed speech+non-speech rejected.

Full ASR smoke:

```bash
source .venv/bin/activate
QWEN3TTS_SMOKE_REQUIRE_ASR=1 \
QWEN3TTS_SMOKE_VOICE_SOURCE=/path/to/known-short-speech.wav \
QWEN3TTS_SMOKE_LANGUAGE=ru \
QWEN3TTS_SMOKE_ASR_MODEL=tiny \
QWEN3TTS_SMOKE_DEVICE=cpu \
bash scripts/run_voice_filter_smoke.sh
```

Use a known-good short speech fixture for full ASR smoke.
The current local Baritone fallback starts from raw source audio and may produce no accepted ASR rows.

## Dataset build

```bash
source .venv/bin/activate
python scripts/build_dataset_from_audio.py \
  --input_dir datasets/voices/Baritone/Input \
  --output_root datasets/voices/Baritone/Ready/build_strict \
  --language ru \
  --voice_filter_mode silero \
  --strict_mode \
  --voice_filter_reject_initial_seconds 30 \
  --voice_filter_export_quarantine \
  --voice_filter_export_quarantine_snippets \
  --validate_manifest
```

Review:

- `Ready/<run_name>/reports/quality_report.json`
- `Ready/<run_name>/filtered_out/removed_segments.jsonl`
- `Ready/<run_name>/manifests/train_raw.jsonl`

For audiobook-style sources with intro music/title cards, keep `--voice_filter_reject_initial_seconds`
enabled and verify that early title/intro chunks are rejected with `initial_window_rejected`.

Do not stage raw `Input/` audio or generated `Ready/` outputs unless a small metadata file is intentionally added.

Current verified Baritone full dataset:

```text
datasets/voices/Baritone/Ready/full_gpu_002_clean_text/manifests/train_raw.jsonl
```

This dataset was built on 2026-06-22 from the three ignored Baritone `Input/`
MP3 files with CUDA ASR, strict Silero filtering, opening-window rejection, and
manifest validation. The accepted manifest has 988 rows. Subtitle/title-card
boilerplate such as "subtitles by" / "субтитры сделал" is rejected with
`transcript_boilerplate` and must not appear in `train_raw.jsonl`.

## Training orchestrator

Use the training orchestrator after a ready `train_raw.jsonl` exists and the
dataset quality gate has been reviewed. It performs:

1. `prepare_data` once, producing a prepared manifest with audio codes;
2. one SFT epoch per loop iteration;
3. checkpoint capture after each epoch;
4. five fixed eval samples after each checkpoint;
5. append-only `metrics.jsonl` logging;
6. automatic checkpoint metrics and a numeric checkpoint score;
7. one `checkpoint_gate` hard-reject decision per checkpoint;
8. one `early_stop_decision` per checkpoint;
9. a final `run_stop` row when the loop stops;
10. final `candidate_selection` metadata and `candidate_manifest.json`;
11. a candidate review pack with copied selected eval WAVs, `ranking.md`, and
    copied `metrics.jsonl`.

Real command shape:

```bash
source .venv/bin/activate
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

For the active `Qwen/Qwen3-TTS-12Hz-1.7B-Base` Baritone track, use the lower
learning rate below. A real 2026-06-22 GPU run with `2e-5` learned prompt/text
artifacts too aggressively and produced subtitle-credit hallucinations in eval
audio. The verified full run with `2e-6` kept `whisper_text_match_mean=1.0` for
all exported candidates.

```bash
source .venv/bin/activate
python tools/train_voice_candidates.py \
  --voice_name Baritone \
  --train_raw_jsonl datasets/voices/Baritone/Ready/full_gpu_002_clean_text/manifests/train_raw.jsonl \
  --output_root experiments/qwen3_ru_en_speaker_v1/runs \
  --run_name baritone_full_gpu_005_clean_text_lr2e6 \
  --min_epochs 2 \
  --max_epochs 6 \
  --patience 2 \
  --top_candidates 4 \
  --speaker_name speaker_target \
  --base_model Qwen/Qwen3-TTS-12Hz-1.7B-Base \
  --device cuda:0 \
  --batch_size 1 \
  --learning_rate 2e-6 \
  --execution_mode real \
  --metrics_mode audio \
  --text_match_backend faster-whisper \
  --text_match_device cuda \
  --text_match_compute_type float16
```

With `--output_root experiments/qwen3_ru_en_speaker_v1/runs`, the candidate
review pack defaults to:

```text
experiments/qwen3_ru_en_speaker_v1/samples/Baritone/baritone_sft_candidates_001/candidate_review/
```

Use `--candidate_review_root /path/to/candidate_review` only when the owner
wants a different review location.

Real mode is GPU-heavy. Do not use it as a smoke test, and do not launch it
until the dataset report shows only clean speech entering `train_raw.jsonl`.

Runtime patch requirement: `external/Qwen3-TTS` is ignored by Git. Before real
training on a fresh checkout, apply or verify
`patches/qwen3-tts-sft-runtime-local-model.patch`. The patch keeps local
snapshot copy behavior, uses `QWEN3_TTS_ATTN_IMPL=sdpa` by default, and reloads
the speaker encoder from `SPEAKER_ENCODER_MODEL_PATH` when continuing
epoch-by-epoch from a custom checkpoint.

```bash
git -C external/Qwen3-TTS apply --unidiff-zero ../../patches/qwen3-tts-sft-runtime-local-model.patch
```

Safe no-GPU smoke:

```bash
bash scripts/run_train_voice_candidates_smoke.sh
```

The smoke writes only under `/tmp/qwen3tts_train_voice_candidates_smoke` and
creates sentinel checkpoint/eval files. It proves the project orchestration
contract without loading Qwen, Torch, or soundfile. It also verifies that
`metrics.jsonl` contains `sample_metrics`, one `checkpoint_score` row per
checkpoint, one `checkpoint_gate` row per checkpoint, `early_stop_decision`
rows, a final `run_stop` row, one `candidate_selection` row, and one
`candidate_review_export` row. The current default smoke runs more than one
stub epoch but stops before `max_epochs=6`. It prints stop reason, epochs
completed, selected candidate count, and rejected checkpoint count. Stage 7
smoke also verifies and prints the candidate review directory, exported
candidate count, `ranking.md` path, copied `metrics.jsonl` path, a review tree
listing, and a ranking excerpt.

Current Stage 4/5 metrics and gates:

- loss signals: `loss_last` and `loss_min` from the train log, with `missing_loss`
  when no loss can be parsed;
- timing signals: `duration_ratio`, `pace_chars_per_sec`, and
  `pace_words_per_sec`;
- signal health: `rms_dbfs`, `clipping_ratio`, `leading_silence_ms`, and
  `trailing_silence_ms`;
- prompt fidelity: `whisper_text_match`;
- voice identity: optional `speaker_similarity` when a backend is configured.

Current hard reject reasons:

- `asr_text_mismatch`: ASR/text match is below the configured threshold;
- `pace_accelerated`: speech becomes materially faster than the previous
  non-rejected checkpoint;
- `audio_clipping`: clipping exceeds the configured threshold;
- `duration_too_short` / `duration_too_long`: generated speech is outside the
  allowed duration-ratio band;
- `suspected_cut`: duration is short and trailing silence is near zero;
- `score_drop`: score is sharply worse than the previous non-rejected
  checkpoint.

Rejected checkpoints stay auditable in `metrics.jsonl` and in
`candidate_manifest.json.rejected_checkpoints`; they must not enter
`candidate_manifest.json.candidates`.

Semi-auto early stopping defaults:

- `min_epochs=2`;
- `max_epochs=6`;
- `patience=2`;
- `top_candidates=4`;
- `candidate_floor=3`.

Current stop reasons:

- `min_epochs_pending`: continue until the minimum epoch floor is reached;
- `patience_exhausted`: stop after two consecutive non-improving viable epochs
  by default;
- `quality_degradation`: stop when a hard-rejected checkpoint shows quality
  degradation after the minimum epoch floor;
- `max_epochs_reached`: stop at the maximum epoch cap;
- hard failure: prepare/train/eval command failures abort the run and write a
  `failure` row instead of producing a candidate.

Naturalness is represented by the proxy metrics and gates above. The system no
longer requires owner listening after every epoch, but the final winner remains
human-selected from the exported candidates in `candidate_review/`.

Backend modes are explicit. `--metrics_mode auto` resolves to audio metrics in
stub smoke and real runs, `--metrics_mode off` records disabled audio metrics,
`--text_match_backend auto` resolves to stub text match during smoke, and
`--speaker_similarity_backend off` records an unavailable warning while keeping
checkpoint scores numeric. For real ASR prompt matching, pass
`--text_match_backend faster-whisper`; it lazily loads the configured
`--text_match_model`, `--text_match_device`, and `--text_match_compute_type`.

Generated `metrics.jsonl` files, `candidate_manifest.json` files, copied review
metrics, candidate review WAVs, checkpoints, eval WAVs, command logs, and run
directories are working artifacts and must not be committed. Raw audio in voice
`Input/` folders is also not a commit target. Keep generated outputs under
ignored experiment paths or `/tmp`; commit only code, tests, docs, scaffolds,
small templates, and intentional metadata.

## Checkpoint selection and review

Use `docs/CHECKPOINT_SELECTION_PROTOCOL.md` before comparing training checkpoints.
The current policy is semi-automatic candidate review: automatic metrics,
hard gates, and project-local early stopping narrow a run to up to 3-4
candidate checkpoints in `candidate_manifest.json`, export those candidates to
`candidate_review/`, then the owner chooses the final voice by listening only
to those exported candidates. The run no longer requires listening after every
epoch.

Current verified Baritone candidate review pack:

```text
experiments/qwen3_ru_en_speaker_v1/samples/Baritone/baritone_full_gpu_005_clean_text_lr2e6/candidate_review/
```

That run stopped automatically after epoch 2 with `patience_exhausted`, selected
epochs 0, 1, and 2 as candidates A, B, and C, and exported five eval WAVs per
candidate. All three candidates are non-rejected. Known warnings are
`leading_silence_too_long` and `speaker_similarity_unavailable`; final choice is
still by human listening.

After the owner chooses a candidate, record the winner:

```bash
python tools/select_voice_candidate.py \
  --candidate B \
  --candidate_review_dir experiments/qwen3_ru_en_speaker_v1/samples/Baritone/baritone_sft_candidates_001/candidate_review
```

`--candidate` accepts `A`, `B`, a numeric rank such as `2`, or a full label such
as `candidate_B_epoch1`. If there is exactly one review pack under the current
working tree, the script can discover it; if more than one exists, pass
`--candidate_review_dir` explicitly. The command writes small metadata only:

- `selected_checkpoint.json`;
- `experiment_status.json`;
- `candidate_manifest.json.winner_selection`.

For normal experiment runs shaped as
`experiments/<experiment>/runs/<voice>/<run_name>/candidate_manifest.json`, the
durable pointer is `experiments/<experiment>/selected_checkpoint.json`. For
temporary smoke runs, the pointer is written under the run directory. The
selection command does not copy checkpoint directories, WAV files, metrics, or
raw audio.

Safe no-GPU winner-selection smoke:

```bash
bash scripts/run_select_voice_candidate_smoke.sh
```

The smoke first creates a Stage 7 review pack, selects `candidate_B_epoch1`, and
verifies that `selected_checkpoint.json`, `experiment_status.json`, and
`candidate_manifest.json.winner_selection` all point to the same checkpoint.
It also verifies that the set of checkpoint directories, WAVs, and metrics files
is unchanged by selection.

Use `docs/templates/CANDIDATE_REVIEW_REPORT.md` as the report format when a
candidate review pack is generated. The generated `ranking.md` is the quick
listening guide; the template is for the owner's final notes and choice.

Do not stage generated candidate WAVs, checkpoints, metrics, copied review
metrics, ranking files, or generated candidate manifests. Keep them under
ignored `experiments/**/samples/` and `experiments/**/runs/` paths. A small
sanitized `selected_checkpoint.json`, `experiment_status.json`, or final report
may be deliberately promoted if it is needed to preserve the chosen voice and
contains no private source paths.

## Deployment / release gate

This project stage does not deploy a daemon, web app, or public service. Treat
deployment as a local release gate before committing or starting a real training
run:

```bash
python tools/select_voice_candidate.py --help
python -m unittest discover -s tests
bash scripts/run_train_voice_candidates_smoke.sh
bash scripts/run_select_voice_candidate_smoke.sh
python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts
bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh scripts/run_select_voice_candidate_smoke.sh
git diff --check
git status --short --ignored
```

Only after this gate is green should the repository snapshot be committed.

## Commit checklist

Before commit:

```bash
git status --ignored --short
git diff --stat
git diff --cached --stat
```

Stage only code, docs, config without secrets, scaffolds, patch files, and small manifests/templates.
Never stage raw `Input/` audio.
