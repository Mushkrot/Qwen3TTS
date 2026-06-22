# Roadmap: Qwen3TTS Stage 8/9 Winner Selection

**Task:** Add human winner selection after candidate review export, then document and smoke-test the full procedure.
**Type:** brownfield, Python, ML workflow
**Created:** 2026-06-22
**Total phases:** 5

## Context Summary

- **Stack:** Python/Qwen3TTS workspace with project-local training orchestration.
- **Current state:** Stage 7 candidate review export is implemented in the working tree but not yet committed.
- **Primary implementation surface:** `tools/train_voice_candidates.py`, new `tools/select_voice_candidate.py`, tests, smoke scripts, and docs.
- **Artifact policy:** raw `Input/` audio, generated WAVs, metrics copies, checkpoints, and run directories stay out of normal commits.

## Scope

In scope:

- `tools/select_voice_candidate.py`;
- `python tools/select_voice_candidate.py --candidate B` style command;
- `selected_checkpoint.json` as a small durable selected-checkpoint pointer;
- local experiment status metadata;
- manifest update tying the human winner to the source `candidate_manifest.json`;
- no-GPU smoke for selecting candidate B from a generated review pack;
- docs for semi-auto training, candidate review, winner selection, and human verification;
- docs separating current MVP from future improvements.

Out of scope:

- automatic final winner selection;
- copying checkpoint directories or generated WAVs to a new active model store;
- deleting non-winning candidate artifacts;
- real speaker-similarity backend;
- smarter learned scoring or recommended candidate;
- HTML report generation;
- commit/push.

## Assumptions

- `--candidate` accepts `A`, `B`, `C`, `D`, `candidate_B_epoch1`, or a numeric rank, but docs emphasize the simple letter path.
- `--candidate_review_dir` is optional. Without it, the script auto-discovers only when the review pack is unambiguous.
- If discovery is ambiguous, the script exits non-zero with a message requiring `--candidate_review_dir`.
- When the run lives under `experiments/<experiment>/runs/<voice>/<run_name>`, the primary durable pointer should be `experiments/<experiment>/selected_checkpoint.json`.
- For temp/smoke runs without a normal experiment root, write the primary pointer under the run directory.
- Small selection metadata may be intentionally committed later if the owner wants to preserve the final choice. Generated audio/checkpoints remain non-commit artifacts.

## Risks

1. **Wrong run selected by auto-discovery** - mitigate with explicit ambiguity failure and tests.
2. **Winner points to a missing or rejected checkpoint** - mitigate by validating against `candidate_manifest.json.candidates`.
3. **Docs overclaim automation** - mitigate by stating the final winner is human-selected and recommended-candidate logic is deferred.

## Phase Map

| # | Phase | Depends on | Deliverable |
|---|-------|------------|-------------|
| 1 | Define Selection Contract | none | CLI/data contract and unit fixtures |
| 2 | Build Selection Writer | 1 | selected checkpoint persistence and status update |
| 3 | Wire Selection Smoke | 1, 2 | no-GPU smoke proves candidate B selection |
| 4 | Document Winner Workflow | 1, 2, 3 | docs for full training-to-winner procedure |
| 5 | Polish & Harden | 1, 2, 3, 4 | final verification and artifact hygiene |

## Pre-flight

Run only baseline-safe commands from `plan-integrity.md`. Do not run commands for `tools/select_voice_candidate.py` or `scripts/run_select_voice_candidate_smoke.sh` until the phases that create them.

---

## Phase 1 - Define Selection Contract

**Why:** The system needs a deterministic, safe contract for mapping a human choice like `B` to one exported candidate.

**Deliverables:**
- New `tools/select_voice_candidate.py`.
- CLI parser with `--candidate`, optional `--candidate_review_dir`, optional `--experiment_root`, and `--dry_run`.
- Helper functions for candidate normalization, review-pack discovery, manifest loading, and output-path resolution.
- Unit tests for candidate parsing, discovery ambiguity, and help output.

**Acceptance criteria:**
- [ ] `python tools/select_voice_candidate.py --help` exits 0 and documents `--candidate`, `--candidate_review_dir`, `--experiment_root`, and `--dry_run`.
- [ ] Candidate input `B`, `b`, `2`, and `candidate_B_epoch1` resolve to the same rank/label target.
- [ ] Auto-discovery accepts an explicit `--candidate_review_dir` and rejects ambiguous discovery with a clear error.
- [ ] The script can load a Stage 7 `candidate_manifest.json` and find candidates only from `candidates`, not `rejected_checkpoints`.
- [ ] Importing the new module is standard-library only.
- [ ] Unit tests cover helper behavior without creating real training/checkpoint artifacts.

**Mandatory commands:**
- `python tools/select_voice_candidate.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

---

## Phase 2 - Build Selection Writer

**Why:** After the owner listens, the project must know which checkpoint is primary without copying large artifacts.

**Deliverables:**
- Selection writer that validates the chosen candidate and checkpoint path.
- `selected_checkpoint.json` payload with candidate, checkpoint, score, run, review, and human-selection metadata.
- Local experiment status metadata.
- Manifest update recording the selected winner.
- Unit tests for success, missing candidate, rejected candidate, dry-run, and no-large-copy behavior.

**Acceptance criteria:**
- [ ] Selecting candidate B writes `selected_checkpoint.json` with checkpoint path, selected label, rank, epoch, score, review dir, and source manifest path.
- [ ] The local experiment status records the selected checkpoint as active/primary.
- [ ] `candidate_manifest.json` records a `winner_selection` or equivalent block without overwriting candidate quality status.
- [ ] `--dry_run` prints planned files and does not write output files.
- [ ] Selecting a missing candidate exits non-zero and writes no partial selection files.
- [ ] The implementation copies no checkpoint directories, WAV files, metrics files, or raw audio.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

---

## Phase 3 - Wire Selection Smoke

**Why:** A no-GPU smoke should prove the owner path from exported candidates to selected winner.

**Deliverables:**
- New `scripts/run_select_voice_candidate_smoke.sh`.
- Smoke flow that creates a stub review pack, selects candidate B, and verifies selection artifacts.
- Smoke output summary with selected candidate, selected checkpoint, selected metadata path, and active status path.

**Acceptance criteria:**
- [ ] `bash scripts/run_select_voice_candidate_smoke.sh` exits 0.
- [ ] Smoke first produces a Stage 7 candidate review pack with at least candidates A and B.
- [ ] Smoke runs `python tools/select_voice_candidate.py --candidate B` or the explicit-path equivalent.
- [ ] Smoke verifies `selected_checkpoint.json` points to candidate B's checkpoint and not candidate A.
- [ ] Smoke verifies local experiment status points to the same selected checkpoint.
- [ ] Smoke verifies no checkpoint/WAV directory copy was created by selection.

**Mandatory commands:**
- `bash scripts/run_select_voice_candidate_smoke.sh`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

---

## Phase 4 - Document Winner Workflow

**Why:** The owner needs one clear procedure for training, listening, selecting, and preserving the result.

**Deliverables:**
- Updated `docs/RUNBOOK.md`.
- Updated `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- Updated `scripts/README.md`.
- Updated `docs/templates/CANDIDATE_REVIEW_REPORT.md`.
- Updated `README.md` and `docs/PROJECT_STATUS.md` if needed.
- A short MVP-vs-future-improvements section.

**Acceptance criteria:**
- [ ] Docs show how to run semi-auto training.
- [ ] Docs show where candidates, `ranking.md`, copied metrics, and `selected_checkpoint.json` live.
- [ ] Docs show how to run `python tools/select_voice_candidate.py --candidate B`.
- [ ] Docs explain that the owner still verifies and chooses the final voice.
- [ ] Docs state the MVP includes epoch-by-epoch training, eval audio, simple metrics, hard rejects, top-4 export, and human winner selection.
- [ ] Docs list future improvements as speaker similarity, smarter scoring, richer report, and automatic recommended candidate.
- [ ] Docs keep generated audio/checkpoints/metrics out of commit scope while allowing intentional small selection metadata preservation.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `bash scripts/run_select_voice_candidate_smoke.sh`
- `git diff --check`

---

## Phase 5 - Polish & Harden

**Why:** The final state must be safe to use before real voice training resumes.

**Deliverables:**
- Final selection script, smoke, tests, docs, and plan state.

**Acceptance criteria:**
- [ ] `python tools/select_voice_candidate.py --help` exits 0.
- [ ] `python -m unittest discover -s tests` exits 0.
- [ ] `bash scripts/run_train_voice_candidates_smoke.sh` exits 0.
- [ ] `bash scripts/run_select_voice_candidate_smoke.sh` exits 0 and emits winner-selection evidence.
- [ ] `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- [ ] `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh scripts/run_select_voice_candidate_smoke.sh` exits 0.
- [ ] `git diff --check` exits 0.
- [ ] `git status --short --ignored` shows no generated review WAVs, copied metrics, checkpoints, generated manifests, or raw `Input/` audio as normal commit candidates.
- [ ] Added-line cleanliness check finds no conflict markers, debug prints, or task markers in app code.
- [ ] Docs do not imply automatic final voice choice is complete.

**Mandatory commands:**
- `python tools/select_voice_candidate.py --help`
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `bash scripts/run_select_voice_candidate_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh scripts/run_select_voice_candidate_smoke.sh`
- `git diff --check`
- `git status --short --ignored`
