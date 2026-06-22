# Roadmap: Qwen3TTS Stage 6 Semi-Auto Early Stopping

**Task:** Implement semi-automatic early stopping for the project-local Qwen3TTS voice training orchestrator.
**Type:** brownfield, Python, ML workflow
**Created:** 2026-06-22
**Total phases:** 5

## Context Summary

- **Stack:** Python/Qwen3TTS workspace with training orchestration in `tools/train_voice_candidates.py`.
- **Package manager:** none detected; use existing Python environment and standard-library tests.
- **Build/test/lint commands:** `python tools/train_voice_candidates.py --help`; `python -m unittest discover -s tests`; `bash scripts/run_train_voice_candidates_smoke.sh`; `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`; `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`; `git diff --check`; `git status --short --ignored`.
- **Risky areas:** stop history must count only viable checkpoints, degradation must not bypass the minimum floor accidentally, and generated training artifacts/raw `Input/` audio must remain ignored.

## Scope

In scope:

- early stopping defaults and CLI options;
- `early_stop_decision` / `run_stop` metadata;
- no-improvement patience over viable checkpoints;
- degradation stop from hard-reject evidence after `min_epochs`;
- max epoch cap;
- candidate manifest/reporting that records stop reason and still chooses top non-rejected checkpoints;
- deterministic stub smoke proving training stops automatically.

Out of scope:

- real listening-based naturalness model;
- real speaker embedding backend;
- copied candidate WAV export pack;
- selected-checkpoint persistence;
- committing generated metrics/audio/checkpoints/manifests or raw `Input/` audio.

## Assumptions

- Default policy is `min_epochs=2`, `max_epochs=6`, `patience=2`, `top_candidates=4`.
- A tiny `early_stop_min_delta` default is acceptable to avoid float noise in score comparisons.
- Degradation uses existing hard reject reasons and metric warnings until a real naturalness model exists.
- If fewer than three viable candidates remain, `candidate_manifest.json` can be marked `limited` while still excluding rejected checkpoints.

## Risks

1. **False early stop before enough candidates exist** — mitigation: enforce `min_epochs`, add `candidate_floor`, and test limited manifests.
2. **Patience counted against rejected epochs** — mitigation: compare only non-rejected viable gates and unit-test rejected high-score histories.
3. **Docs overclaim full automatic voice selection** — mitigation: docs must say this removes per-epoch listening, but final winner remains human-selected.

## Phase Map

| # | Phase | Depends on | Deliverable |
|---|-------|------------|-------------|
| 1 | Define Stop Contract | none | defaults, CLI options, stop event schemas, tests |
| 2 | Implement Stop Decisions | 1 | min/max/patience/degradation loop behavior |
| 3 | Wire Manifest Smoke | 1, 2 | stop metadata in manifest and smoke assertions |
| 4 | Update Docs | 1, 2, 3 | runbook/protocol/docs reflect semi-auto stopping |
| 5 | Polish & Harden | 1, 2, 3, 4 | full verification and artifact hygiene |

---

## Phase 1 — Define Stop Contract

**Why:** Lock the early-stop contract before changing the training loop.

**Deliverables:**
- Early stopping constants/dataclasses/helpers in `tools/train_voice_candidates.py`.
- Event schemas for `early_stop_decision` and `run_stop`.
- CLI options for `--min_epochs`, `--patience`, `--early_stop_min_delta`, `--candidate_floor`, and default `--max_epochs 6`.
- Unit tests for defaults, serialization, parser help, and import safety.

**Acceptance criteria:**
- [ ] Code defines stable event names for `early_stop_decision` and `run_stop`.
- [ ] Defaults match `min_epochs=2`, `max_epochs=6`, `patience=2`, `top_candidates=4`.
- [ ] Stop decision rows serialize `epoch`, `should_stop`, `reason`, `best_epoch`, `best_score`, `epochs_without_improvement`, and `min_epochs_reached`.
- [ ] Parser help exposes all early-stop options.
- [ ] Invalid parser combinations fail fast, including `--min_epochs < 1`, `--max_epochs < 1`, `--patience < 1`, and `--min_epochs > --max_epochs`.
- [ ] Importing `tools.train_voice_candidates` still does not import `torch`, `qwen_tts`, `soundfile`, `faster_whisper`, or embedding models.

**Mandatory commands:**
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Help excerpt for early-stop options.
- Unit test summary.
- Stop defaults/schema excerpt.
- Command exit codes.

---

## Phase 2 — Implement Stop Decisions

**Why:** Make the epoch loop stop itself from metric/gate evidence.

**Deliverables:**
- Stop decision helper over prior `checkpoint_gate` rows.
- `early_stop_decision` appended after every checkpoint gate.
- Training loop `break` when decision says stop.
- `run_stop` row summarizing the final stop reason before `run_end`.
- Unit tests for minimum floor, patience, degradation, and max cap.

**Acceptance criteria:**
- [ ] The loop always runs at least `min_epochs` unless training/eval raises a hard failure.
- [ ] With stable stub scores, default policy stops before epoch 6 via `patience_exhausted`.
- [ ] `max_epochs_reached` stops exactly at `max_epochs` when patience/degradation do not stop earlier.
- [ ] A degradation hard reject after `min_epochs` stops before the next epoch.
- [ ] Rejected checkpoints do not reset the no-improvement patience counter.
- [ ] Every completed checkpoint has exactly one `early_stop_decision` row after its `checkpoint_gate`.
- [ ] `run_stop` records `reason`, `epoch`, `best_epoch`, `best_score`, and `epochs_completed`.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Unit test summary.
- Example patience stop row.
- Example degradation stop row.
- Command exit codes.

---

## Phase 3 — Wire Manifest Smoke

**Why:** Make the automatic stop observable in the normal smoke path and final candidate manifest.

**Deliverables:**
- `candidate_manifest.json` includes stop summary and candidate floor/limited status.
- `scripts/run_train_voice_candidates_smoke.sh` verifies early-stop rows, run-stop rows, stopped epoch count, and candidate manifest stop summary.
- Smoke runs enough stub epochs to prove automatic stopping without GPU.
- Tests prove selected candidates are top non-rejected checkpoints after early stop.

**Acceptance criteria:**
- [ ] Smoke exits 0 and prints stop reason, epochs completed, selected candidate count, and rejected checkpoint count.
- [ ] Smoke produces more than one checkpoint but fewer than default `max_epochs=6`.
- [ ] Smoke `metrics.jsonl` contains `early_stop_decision`, `run_stop`, and `candidate_selection`.
- [ ] `candidate_manifest.json` records stop reason, best epoch/score, epochs completed, `candidate_floor`, and limited status.
- [ ] Manifest candidates do not include rejected checkpoints.
- [ ] Unit tests prove a rejected high-score checkpoint cannot become a final candidate after early stop.

**Mandatory commands:**
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Smoke output summary.
- `run_stop` JSONL excerpt.
- `candidate_manifest.json` excerpt.
- Command exit codes.

---

## Phase 4 — Update Docs

**Why:** Documentation must match the new operational behavior before real training.

**Deliverables:**
- Updated `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- Updated `docs/RUNBOOK.md`.
- Updated `scripts/README.md`.
- Updated `docs/templates/CANDIDATE_REVIEW_REPORT.md` if stop summary fields belong in reports.
- Updated `README.md`, `docs/PROJECT_STATUS.md`, or `PROJECT_LOG.md` if they still describe early stopping as future-only.

**Acceptance criteria:**
- [ ] Docs state Stage 6 implements semi-auto early stopping in project-local orchestration.
- [ ] Docs list defaults: `min_epochs=2`, `max_epochs=6`, `patience=2`, `top_candidates=4`.
- [ ] Docs explain stop reasons: `min_epochs_pending`, `patience_exhausted`, `quality_degradation`, `max_epochs_reached`, and hard failure.
- [ ] Docs state the system no longer requires listening after every epoch.
- [ ] Docs state final winner remains human-selected from top candidates.
- [ ] Docs keep copied candidate WAV export and selected-checkpoint persistence out of scope unless implemented.
- [ ] Docs keep generated metrics/manifests/checkpoints/eval WAVs and raw `Input/` audio out of commit scope.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`

**Evidence required:**
- Documentation grep output.
- Smoke output summary.
- Unit test summary.
- Command exit codes.

---

## Phase 5 — Polish & Harden

**Why:** Verify the new stopping layer is deterministic, documented, and safe to build on.

**Deliverables:**
- Final early stopping implementation, tests, smoke assertions, docs, and plan state.

**Acceptance criteria:**
- [ ] `python tools/train_voice_candidates.py --help` exits 0 and documents early-stop/candidate options.
- [ ] `python -m unittest discover -s tests` exits 0.
- [ ] `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and emits auto-stop evidence.
- [ ] `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- [ ] `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- [ ] `git diff --check` exits 0.
- [ ] `git status --short --ignored` shows no generated metrics/audio/checkpoints/manifests or raw `Input/` audio as normal commit candidates due to this run.
- [ ] Smoke proves epochs completed are `< max_epochs` under default policy.
- [ ] Docs do not imply copied candidate WAV export or final human choice persistence is complete.

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
- Smoke stop summary.
- Candidate manifest excerpt.
- Artifact hygiene summary.
