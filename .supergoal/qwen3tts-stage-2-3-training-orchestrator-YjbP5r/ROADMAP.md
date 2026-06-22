# Roadmap: Qwen3TTS Stage 2/3 Training Orchestrator

**Task:** Build the project-local training orchestrator and per-checkpoint eval pack generation.
**Type:** brownfield, Python, ML workflow
**Created:** 2026-06-22
**Total phases:** 5

## Context summary

- **Stack:** Python/Qwen3-TTS workspace with shell wrappers and upstream trainer in `external/Qwen3-TTS`.
- **Package manager:** none detected; use `.venv` when running real commands.
- **Build / test / lint commands:** `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`; `python -m unittest discover -s tests`; `bash scripts/run_train_voice_candidates_smoke.sh`; `git diff --check`.
- **Risky areas:** upstream SFT has no explicit resume support; real train/infer is heavy; generated artifacts must remain uncommitted.

## Plan integrity and pre-flight policy

Pre-flight must run only commands classified as `baseline-safe`: commands that do not depend on files or directories created by future phases.

Command classes are maintained in:

- `.supergoal/qwen3tts-stage-2-3-training-orchestrator-YjbP5r/plan-integrity.md`
- `.supergoal/qwen3tts-stage-2-3-training-orchestrator-YjbP5r/deferred-work.md`

Baseline-safe pre-flight commands:

- `git diff --check`
- `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh`
- `git status --short --ignored`

Commands that require future deliverables, such as `python tools/train_voice_candidates.py --help`, `python -m unittest discover -s tests`, `bash scripts/run_train_voice_candidates_smoke.sh`, and `python -m compileall -q tools`, are mandatory phase checks only after the phase that creates those files has completed its work.

## Assumptions

- Create `tools/train_voice_candidates.py` as the main CLI.
- Add standard-library `unittest` tests under `tests/`; do not require `pytest`.
- Add `scripts/run_train_voice_candidates_smoke.sh` for a no-GPU stub smoke.
- The orchestrator accepts a ready/validated dataset manifest; it does not build a dataset from raw `Input/` audio in this stage.
- The eval pack filenames are exactly `01_en_short.wav`, `02_en_long.wav`, `03_en_calm.wav`, `04_ru_short.wav`, `05_ru_long.wav`.
- Real outputs stay under ignored experiment paths; smoke outputs stay under `/tmp`.

## Risk top 3

1. **Epoch continuation semantics are unclear** — likelihood: high; mitigation: phase 1 defines the command contract and phase 2 requires visible `init_model_path` logging where epoch N>0 defaults to the previous checkpoint or fails clearly.
2. **Verification accidentally runs expensive training** — likelihood: medium; mitigation: phase 2/3 require stub command mode and smoke script that creates sentinel checkpoints/WAVs under `/tmp`.
3. **Generated artifacts leak into Git** — likelihood: medium; mitigation: phase 4 docs and phase 5 status checks require no generated runs/samples staged and no raw `Input/` audio touched.

## Phase map

| # | Phase | Depends on | Deliverable |
|---|-------|------------|-------------|
| 1 | Define Contract | none | CLI contract, tests scaffold, path model |
| 2 | Build Orchestrator | 1 | `tools/train_voice_candidates.py` runs prepare + epoch training + metrics |
| 3 | Generate Eval Pack | 1, 2 | per-epoch five-file eval pack generation |
| 4 | Wire Smoke Docs | 1, 2, 3 | smoke script, tests, docs/runbook updates |
| 5 | Polish & Harden | 1, 2, 3, 4 | final audit, static checks, artifact hygiene |

---

## Phase 1 — Define Contract

**Why:** Lock the orchestration contract before wiring subprocesses so the script is testable without real GPU training.

**Deliverables:**
- `tools/train_voice_candidates.py` skeleton with argument parsing and no heavy imports at import time.
- `tests/test_train_voice_candidates.py` initial contract tests.

**Acceptance criteria:**
- [ ] `python tools/train_voice_candidates.py --help` exits 0 and shows `--voice_name`, `--train_raw_jsonl`, `--output_root`, `--run_name`, `--max_epochs`, and `--speaker_name`.
- [ ] The CLI has a stub or command-template mode that can be used by tests without importing `torch`, `qwen_tts`, or `soundfile`.
- [ ] The script defines deterministic paths for prepared manifest, per-epoch run dirs, checkpoint paths, eval dirs, logs, and `metrics.jsonl`.
- [ ] The initial unit tests assert the path model and default eval phrase filenames.
- [ ] `python -m unittest discover -s tests` exits 0.

**Mandatory commands:**
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools`
- `git diff --check`

**Command classes:** `python tools/train_voice_candidates.py --help`, `python -m unittest discover -s tests`, and `python -m compileall -q tools` are `requires-phase-1`; `git diff --check` is `baseline-safe`.

**Evidence required:**
- CLI help excerpt.
- Unit test summary.
- Path model excerpt from tests or script.
- Command exit codes.

**Dependencies:** none

---

## Phase 2 — Build Orchestrator

**Why:** Implement the one-command prepare -> epoch -> checkpoint sequence and durable `metrics.jsonl` logging.

**Deliverables:**
- `tools/train_voice_candidates.py` prepare/train loop implementation.
- Unit tests covering prepare command, epoch command, checkpoint detection, failure handling, and metrics rows.

**Acceptance criteria:**
- [ ] The script accepts a voice name and ready `train_raw.jsonl` path.
- [ ] The script runs prepare once and writes/uses a prepared manifest path.
- [ ] The script runs training as one-epoch jobs, one loop iteration per requested epoch.
- [ ] The script records `init_model_path` for every epoch; epoch 0 uses the configured base model, and epoch N>0 uses the previous checkpoint by default or fails clearly if that mode is not available.
- [ ] After epoch 0, the script records a checkpoint path and appends a JSONL metrics row with `event="checkpoint"`, `epoch=0`, and `checkpoint_path`.
- [ ] `metrics.jsonl` is append-only JSONL with run metadata, command exit status, started/finished timestamps, and paths.
- [ ] Command failures stop the run with a non-zero exit and a metrics row marking the failed stage.
- [ ] Unit tests cover both success and failure without launching real Qwen training.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Command classes:** `python -m unittest discover -s tests` and `python -m compileall -q tools scripts` are `requires-phase-1` and run after Phase 2 work; `git diff --check` is `baseline-safe`.

**Evidence required:**
- Unit test summary.
- Example `metrics.jsonl` rows from a temporary test/smoke run.
- Command exit codes.

**Dependencies:** 1

---

## Phase 3 — Generate Eval Pack

**Why:** After each checkpoint, the user needs ready-to-listen comparison audio without manually running inference.

**Deliverables:**
- Eval-pack generation in `tools/train_voice_candidates.py`.
- Tests for the five fixed eval filenames and inference command invocation.

**Acceptance criteria:**
- [ ] After every checkpoint, the script creates `eval/epoch-N/`.
- [ ] Each epoch eval dir contains or expects exactly these output files: `01_en_short.wav`, `02_en_long.wav`, `03_en_calm.wav`, `04_ru_short.wav`, `05_ru_long.wav`.
- [ ] The eval phrase list includes three English prompts and two Russian prompts.
- [ ] The script invokes inference once per eval phrase with checkpoint, speaker, text, language, and output path.
- [ ] Eval generation appends JSONL metrics rows with `event="eval_sample"` and output paths.
- [ ] Unit tests verify eval generation in stub mode without importing Qwen.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Command classes:** `python -m unittest discover -s tests` and `python -m compileall -q tools scripts` are `requires-phase-1`; `git diff --check` is `baseline-safe`.

**Evidence required:**
- Unit test summary.
- Example eval directory listing from a stub run.
- Example eval metrics rows.
- Command exit codes.

**Dependencies:** 1, 2

---

## Phase 4 — Wire Smoke Docs

**Why:** Make the new workflow discoverable and provide one safe command proving prepare -> epoch 0 -> checkpoint -> eval pack.

**Deliverables:**
- `scripts/run_train_voice_candidates_smoke.sh`
- Updated `scripts/README.md`
- Updated `docs/RUNBOOK.md`
- Updated `docs/CHECKPOINT_SELECTION_PROTOCOL.md` if needed for orchestrator status.

**Acceptance criteria:**
- [ ] `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and writes output under `/tmp/qwen3tts_train_voice_candidates_smoke`.
- [ ] The smoke output contains a prepared manifest, `metrics.jsonl`, an epoch-0 checkpoint sentinel, and five eval WAV/sentinel files under `eval/epoch-0/`.
- [ ] `scripts/README.md` documents the real orchestrator command and the smoke command.
- [ ] `docs/RUNBOOK.md` documents when to use the orchestrator and warns that real training is GPU-heavy.
- [ ] Docs state generated checkpoints/eval WAVs are ignored working artifacts and must not be committed.

**Mandatory commands:**
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `git diff --check`

**Command classes:** `bash scripts/run_train_voice_candidates_smoke.sh` is `requires-phase-4`; `python -m unittest discover -s tests` is `requires-phase-1`; `git diff --check` is `baseline-safe`.

**Evidence required:**
- Smoke command output summary.
- `/tmp/...` smoke tree listing.
- Metrics rows from smoke.
- Documentation grep output.

**Dependencies:** 1, 2, 3

---

## Phase 5 — Polish & Harden

**Why:** Verify the orchestrator is safe, documented, and does not disturb existing dataset/audio policy.

**Deliverables:**
- Final polished orchestrator, tests, smoke script, and docs.

**Acceptance criteria:**
- [ ] `python tools/train_voice_candidates.py --help` exits 0.
- [ ] `python -m unittest discover -s tests` exits 0.
- [ ] `bash scripts/run_train_voice_candidates_smoke.sh` exits 0.
- [ ] `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- [ ] `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- [ ] `git diff --check` exits 0.
- [ ] `git status --short --ignored` shows no raw `datasets/voices/**/Input/` audio staged/untracked as a normal commit candidate due to this run.
- [ ] Final docs clearly distinguish stub smoke from real GPU training.

**Mandatory commands:**
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`
- `git diff --check`
- `git status --short --ignored`

**Command classes:** full checks here intentionally include `requires-phase-1` and `requires-phase-4` commands because Phase 5 depends on all previous phases; `git diff --check`, existing-script syntax checks, existing-source compile checks, and `git status --short --ignored` are `baseline-safe`.

**Evidence required:**
- Command exit codes.
- Smoke output summary and tree.
- Final `git diff --stat`.
- Final changed-file summary with artifact hygiene note.

**Dependencies:** 1, 2, 3, 4
