# Roadmap: Qwen3TTS Stage 5 Hard Reject Checkpoint Rules

**Task:** Add hard reject rules so clearly bad checkpoints cannot enter final candidate selection.
**Type:** brownfield, Python, ML workflow
**Created:** 2026-06-22
**Total phases:** 5

## Context Summary

- **Stack:** Python/Qwen3TTS workspace with project-local training orchestrator in `tools/train_voice_candidates.py`.
- **Package manager:** none detected; use existing Python environment and standard-library tests.
- **Build/test/lint commands:** `python -m unittest discover -s tests`; `bash scripts/run_train_voice_candidates_smoke.sh`; `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`; `git diff --check`.
- **Risky areas:** hard rejects must be conservative, history comparisons must not select bad checkpoints by accident, and generated artifacts/raw `Input/` audio must remain ignored.

## Scope

In scope:

- hard reject contract and thresholds;
- per-checkpoint gate decisions;
- history-aware rejects for pace acceleration and score collapse;
- candidate selection metadata/manifest that excludes rejected checkpoints;
- smoke/tests/docs proving bad checkpoints do not reach final candidates.

Out of scope:

- full automatic early stopping;
- copied candidate audio export package;
- human selected checkpoint persistence;
- real speaker embedding backend.

## Assumptions

- Stage 5 builds on existing Stage 4 `sample_metrics` and `checkpoint_score` rows.
- A rejected checkpoint remains auditable in `metrics.jsonl` but cannot appear in `candidate_manifest.json`.
- Candidate selection uses up to four non-rejected checkpoints, sorted by score with earlier epoch tie-break.
- Real `faster-whisper` and speaker embedding checks remain optional/env; smoke uses deterministic stub metrics.

## Risks

1. **False rejects remove a usable voice** — mitigation: conservative thresholds and explicit reject reasons.
2. **History-dependent rules miscompare epochs** — mitigation: compare against previous non-rejected checkpoint and unit-test synthetic multi-epoch histories.
3. **No viable candidate remains** — mitigation: write a limited/empty manifest and rejection summary instead of selecting a known-bad checkpoint.

## Phase Map

| # | Phase | Depends on | Deliverable |
|---|-------|------------|-------------|
| 1 | Define Gate Contract | none | hard reject thresholds, row schemas, parser options, tests |
| 2 | Evaluate Hard Rejects | 1 | checkpoint gate decisions and user-requested reject reasons |
| 3 | Select Candidates | 1, 2 | final candidate manifest excluding rejected checkpoints |
| 4 | Wire Smoke Docs | 1, 2, 3 | smoke assertions and documentation |
| 5 | Polish & Harden | 1, 2, 3, 4 | full verification and artifact hygiene |

---

## Phase 1 — Define Gate Contract

**Why:** Lock the hard reject data contract before adding selection behavior.

**Deliverables:**
- Hard reject threshold dataclass/helpers in `tools/train_voice_candidates.py`.
- Row schemas for `checkpoint_gate` and `candidate_selection`.
- CLI options for top-candidate count and hard reject threshold overrides where appropriate.
- Unit tests for schema serialization and defaults.

**Acceptance criteria:**
- [ ] Code defines stable event names for `checkpoint_gate` and `candidate_selection`.
- [ ] Code defines thresholds for ASR mismatch, pace acceleration, clipping, duration ratio, suspected cut, and score drop.
- [ ] Gate decision rows serialize `epoch`, `checkpoint_path`, `hard_rejected`, `reject_reasons`, `warning_reasons`, `score`, and `metric_summary`.
- [ ] Candidate selection rows serialize selected epochs and rejected epochs.
- [ ] Parser help exposes candidate count and hard-reject threshold options.
- [ ] Importing `tools.train_voice_candidates` still does not import `torch`, `qwen_tts`, `soundfile`, `faster_whisper`, or embedding models.

**Mandatory commands:**
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Unit test summary.
- Help excerpt for new options.
- Schema/default threshold excerpt.
- Command exit codes.

---

## Phase 2 — Evaluate Hard Rejects

**Why:** Convert metric evidence into explicit hard reject decisions.

**Deliverables:**
- `evaluate_checkpoint_gate(...)` or equivalent helper.
- `checkpoint_gate` event appended after each `checkpoint_score`.
- History-aware comparison against previous non-rejected checkpoint for pace and score-drop rules.
- Unit tests for every user-requested reject reason.

**Acceptance criteria:**
- [ ] Each checkpoint receives exactly one `checkpoint_gate` row after its `checkpoint_score`.
- [ ] Low `whisper_text_match` produces an ASR/text reject reason.
- [ ] Material pace acceleration versus a previous non-rejected checkpoint produces a reject reason.
- [ ] Clipping above threshold produces a reject reason.
- [ ] Too-short or too-long duration ratio produces a reject reason.
- [ ] Suspected cut from duration/silence anomalies produces a reject reason.
- [ ] Score drop beyond threshold versus previous viable/best checkpoint produces a reject reason.
- [ ] A clean stub checkpoint is not hard rejected.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Unit test summary.
- Example clean `checkpoint_gate` row.
- Example synthetic rejected gate row from tests or fixture.
- Command exit codes.

---

## Phase 3 — Select Candidates

**Why:** Ensure bad checkpoints cannot enter the final candidate list.

**Deliverables:**
- Candidate selection helper that reads gate/score rows.
- `candidate_selection` event written after a run completes.
- `candidate_manifest.json` in the run directory.
- Unit tests proving rejected checkpoints are excluded.

**Acceptance criteria:**
- [ ] Candidate selection ignores every checkpoint with `hard_rejected: true`.
- [ ] Candidate selection includes at most `top_candidates` non-rejected checkpoints.
- [ ] Candidate ordering uses score descending, then fewer warnings/reasons, then earlier epoch.
- [ ] If no checkpoint is viable, the manifest contains an empty candidates list plus rejected summary and limited status.
- [ ] `candidate_manifest.json` records selected candidates, rejected checkpoints, scores, gate reasons, checkpoint paths, and eval directories.
- [ ] The orchestrator writes `candidate_selection` after all epochs finish.
- [ ] Unit tests show a bad checkpoint with better raw score still does not appear in final candidates.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Unit test summary.
- Smoke `candidate_selection` row.
- Smoke `candidate_manifest.json` excerpt.
- Command exit codes.

---

## Phase 4 — Wire Smoke Docs

**Why:** Make the hard reject layer visible and safe to verify without real training.

**Deliverables:**
- Updated `scripts/run_train_voice_candidates_smoke.sh` assertions for gate rows and candidate manifest.
- Updated `docs/CHECKPOINT_SELECTION_PROTOCOL.md`, `docs/RUNBOOK.md`, `scripts/README.md`, and candidate review template as needed.
- Documentation of reject reasons and artifact policy.

**Acceptance criteria:**
- [ ] Smoke exits 0 and verifies `checkpoint_gate`, `candidate_selection`, and `candidate_manifest.json`.
- [ ] Smoke output prints selected candidate count and rejected checkpoint count.
- [ ] Documentation lists every hard reject reason requested by the user.
- [ ] Documentation states rejected checkpoints remain auditable but do not enter final candidates.
- [ ] Documentation keeps generated candidate manifests/metrics/checkpoints/eval WAVs and raw `Input/` audio out of commit scope.

**Mandatory commands:**
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `git diff --check`

**Evidence required:**
- Smoke output summary.
- Manifest/gate row excerpt.
- Documentation grep output.
- Command exit codes.

---

## Phase 5 — Polish & Harden

**Why:** Verify the hard reject layer is deterministic, documented, and safe to build on.

**Deliverables:**
- Final hard reject implementation, tests, smoke assertions, and docs.

**Acceptance criteria:**
- [ ] `python tools/train_voice_candidates.py --help` exits 0 and documents hard reject/candidate options.
- [ ] `python -m unittest discover -s tests` exits 0.
- [ ] `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and emits hard reject/candidate evidence.
- [ ] `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- [ ] `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- [ ] `git diff --check` exits 0.
- [ ] `git status --short --ignored` shows no generated metrics/audio/checkpoints/manifests or raw `Input/` audio as normal commit candidates due to this run.
- [ ] Smoke `candidate_manifest.json` contains no rejected checkpoints in `candidates`.
- [ ] Docs do not imply full automatic early stopping or full audio export is complete.

**Mandatory commands:**
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

**Evidence required:**
- Command exit codes.
- Candidate manifest excerpt.
- Final diff stat.
- Artifact hygiene summary.

