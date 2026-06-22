# Roadmap: Qwen3TTS Stage 4 Automatic Checkpoint Metrics

**Task:** Add automatic metrics so every checkpoint receives numeric evidence, a numeric score, and warnings.
**Type:** brownfield, Python, ML workflow
**Created:** 2026-06-22
**Total phases:** 5

## Context summary

- **Stack:** Python/Qwen3TTS workspace with project-local training orchestrator in `tools/train_voice_candidates.py`.
- **Package manager:** none detected; use existing Python environment and standard-library tests.
- **Build / test / lint commands:** `python -m unittest discover -s tests`; `bash scripts/run_train_voice_candidates_smoke.sh`; `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`; `git diff --check`.
- **Risky areas:** real Whisper/speaker embedding backends may be heavy or unavailable; smoke must stay `/tmp`-only; every checkpoint must still get a numeric score and warnings list.

## Plan integrity and pre-flight policy

Pre-flight must run only commands classified as `baseline-safe`: commands that do not depend on files or scripts created by future phases.

Command classes are maintained in:

- `.supergoal/qwen3tts-stage-4-automatic-checkpoint-me-NuexKP/plan-integrity.md`
- `.supergoal/qwen3tts-stage-4-automatic-checkpoint-me-NuexKP/deferred-work.md`

Baseline-safe pre-flight commands:

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

Real Whisper transcription, real speaker embedding, and real GPU training are `external/env` checks and must not be required for smoke completion.

## Assumptions

- Stage 4 extends the existing `tools/train_voice_candidates.py` orchestrator rather than replacing it.
- Store metric events in the existing append-only `metrics.jsonl`.
- Use a 0-100 `score` for each checkpoint.
- Use a `warnings` list for hard/soft metric problems.
- `speaker_similarity` is optional until an embedding backend is configured; when unavailable, emit an explicit warning and redistribute/skip that weight without failing smoke.
- Stub smoke must create deterministic metric evidence without loading Qwen, Torch, soundfile, faster-whisper, or speaker embedding models.
- Stage 4 does not implement full automatic early stopping or candidate export; it prepares the scoring substrate for those later stages.

## Risk top 3

1. **Metrics silently fake audio quality in smoke** — likelihood: medium; mitigation: write valid deterministic WAV fixtures or explicit stub backend metadata and unit tests.
2. **Optional backends make smoke flaky** — likelihood: high; mitigation: lazy backend modes and unavailable-backend warnings.
3. **Score hides serious failures** — likelihood: medium; mitigation: always persist per-sample metrics and per-checkpoint warnings next to the numeric score.

## Phase map

| # | Phase | Depends on | Deliverable |
|---|-------|------------|-------------|
| 1 | Define Metric Contract | none | Metric schema, thresholds, backend modes, tests |
| 2 | Compute Signal Metrics | 1 | loss/audio metrics per eval sample and epoch |
| 3 | Score Checkpoints | 1, 2 | text match, optional speaker similarity, aggregate score/warnings |
| 4 | Wire Smoke Docs | 1, 2, 3 | smoke evidence and docs for automatic metrics |
| 5 | Polish & Harden | 1, 2, 3, 4 | full verification and artifact hygiene |

---

## Phase 1 — Define Metric Contract

**Why:** Lock the metric schema before computing anything so all later rows are parseable and testable.

**Deliverables:**
- Metric dataclasses/helpers in `tools/train_voice_candidates.py` or a new `tools/checkpoint_metrics.py`.
- Unit tests for metric event names, score schema, warnings schema, backend modes, and threshold defaults.

**Acceptance criteria:**
- [ ] The code defines a stable metric event contract for `sample_metrics` and `checkpoint_score` rows.
- [ ] The metric schema includes fields for loss, duration ratio, pace, RMS/clipping, leading/trailing silence, whisper text match, optional speaker similarity, numeric score, and warnings.
- [ ] The score is numeric and normalized to a 0-100 range.
- [ ] Backend modes distinguish safe stub/off behavior from real Whisper and speaker-similarity backends.
- [ ] Importing `tools.train_voice_candidates` still does not import `torch`, `qwen_tts`, `soundfile`, `faster_whisper`, or any embedding model.
- [ ] Unit tests cover schema serialization and default thresholds.

**Mandatory commands:**
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Command classes:** all commands are `baseline-safe` because Stage 2/3 already created `tools/`, `tests/`, and the smoke/script surface.

**Evidence required:**
- Unit test summary.
- Schema/default threshold excerpt.
- Command exit codes.

**Dependencies:** none

---

## Phase 2 — Compute Signal Metrics

**Why:** Produce objective numeric evidence from training logs and generated eval audio.

**Deliverables:**
- Loss extraction from train logs/metrics into checkpoint-level loss fields.
- Audio metric extraction for each eval sample: duration, duration ratio, words/sec or chars/sec, RMS dBFS, clipping ratio, leading silence, trailing silence.
- Stub/smoke eval files that are valid enough for metric extraction or explicit stub metrics with backend metadata.

**Acceptance criteria:**
- [ ] Each generated eval sample produces a `sample_metrics` JSONL row.
- [ ] Every `sample_metrics` row includes `duration_seconds`, `expected_duration_seconds`, `duration_ratio`, `pace_chars_per_sec`, `pace_words_per_sec`, `rms_dbfs`, `clipping_ratio`, `leading_silence_ms`, and `trailing_silence_ms`.
- [ ] Training loss is parsed from train logs when present and recorded as numeric `loss_last` and `loss_min` fields for the checkpoint.
- [ ] Missing loss data produces a warning, not a crash.
- [ ] Stub smoke generates deterministic metric values without real Qwen/GPU execution.
- [ ] Unit tests cover normal audio, clipping, silence boundaries, pace/duration calculation, and missing-loss behavior.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Command classes:** all commands are `baseline-safe`; real audio/model work remains `external/env`.

**Evidence required:**
- Unit test summary.
- Example `sample_metrics` rows.
- Smoke output excerpt.
- Command exit codes.

**Dependencies:** 1

---

## Phase 3 — Score Checkpoints

**Why:** Convert per-sample evidence into a single checkpoint score plus warnings so bad checkpoints can be rejected automatically later.

**Deliverables:**
- Checkpoint-level aggregation and scoring.
- Whisper text match backend abstraction with safe stub/off behavior.
- Optional speaker similarity backend abstraction with unavailable-backend warning.
- `checkpoint_score` metrics row after every checkpoint.

**Acceptance criteria:**
- [ ] Every checkpoint gets one `checkpoint_score` JSONL row.
- [ ] Each `checkpoint_score` row contains numeric `score`, `epoch`, `checkpoint_path`, `sample_count`, `metric_summary`, and `warnings`.
- [ ] `whisper_text_match` is numeric in stub mode and real-backend-ready without importing Faster-Whisper at module import time.
- [ ] `speaker_similarity` is numeric when a backend result is available; otherwise it is absent/null with a warning and scoring still produces a numeric score.
- [ ] Hard warning conditions include duration/pace out of band, clipping, too-quiet audio, leading/trailing silence problems, text mismatch, missing loss, and unavailable speaker backend.
- [ ] Unit tests verify score bounds, warning generation, text-match behavior, and optional speaker-similarity fallback.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Command classes:** all commands are `baseline-safe`; real Whisper and real speaker embedding checks are `external/env`.

**Evidence required:**
- Unit test summary.
- Example `checkpoint_score` row with numeric score and warnings list.
- Command exit codes.

**Dependencies:** 1, 2

---

## Phase 4 — Wire Smoke Docs

**Why:** Make the metrics visible and safe to verify without manual inspection or heavy model execution.

**Deliverables:**
- Updated `scripts/run_train_voice_candidates_smoke.sh` that asserts metric rows and checkpoint score exist.
- Updated `scripts/README.md`, `docs/RUNBOOK.md`, and `docs/CHECKPOINT_SELECTION_PROTOCOL.md` describing metrics, score, warnings, and backend modes.
- Optional small report/template updates if needed.

**Acceptance criteria:**
- [ ] Smoke exits 0 and verifies at least five `sample_metrics` rows and one `checkpoint_score` row.
- [ ] Smoke output prints the metric file path and the checkpoint score.
- [ ] Documentation lists all Stage 4 metrics requested by the user.
- [ ] Documentation states which metrics are always computed, which are optional, and what warnings mean.
- [ ] Documentation warns that generated metric artifacts, checkpoints, eval WAVs, and raw input audio must not be committed.

**Mandatory commands:**
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `git diff --check`

**Command classes:** all commands are `baseline-safe`; docs grep is phase-local evidence.

**Evidence required:**
- Smoke output summary.
- Metrics rows from smoke.
- Documentation grep output.
- Command exit codes.

**Dependencies:** 1, 2, 3

---

## Phase 5 — Polish & Harden

**Why:** Verify the metrics layer is deterministic, documented, and does not disturb dataset/audio policy.

**Deliverables:**
- Final automatic metrics implementation, tests, smoke assertions, and documentation.

**Acceptance criteria:**
- [ ] `python tools/train_voice_candidates.py --help` exits 0 and documents metric/backend options.
- [ ] `python -m unittest discover -s tests` exits 0.
- [ ] `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and emits metric score evidence.
- [ ] `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- [ ] `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- [ ] `git diff --check` exits 0.
- [ ] `git status --short --ignored` shows no generated metrics/audio/checkpoints or raw `Input/` audio as normal commit candidates due to this run.
- [ ] Every checkpoint in smoke has numeric `score` and `warnings` list in `metrics.jsonl`.
- [ ] Final docs distinguish stub/off/real metric backends and do not imply automatic stopping is complete.

**Mandatory commands:**
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

**Command classes:** all commands are valid by Phase 5 and baseline-safe in the current Stage 2/3 working tree.

**Evidence required:**
- Command exit codes.
- Smoke metric rows and score row.
- Final `git diff --stat`.
- Artifact hygiene summary.

**Dependencies:** 1, 2, 3, 4
