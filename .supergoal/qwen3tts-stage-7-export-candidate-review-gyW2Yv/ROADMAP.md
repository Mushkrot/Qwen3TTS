# Roadmap: Qwen3TTS Stage 7 Candidate Review Export

**Task:** Export only the selected training candidates into a human review pack after semi-auto stopping.
**Type:** brownfield, Python, ML workflow
**Created:** 2026-06-22
**Total phases:** 5

## Context Summary

- **Stack:** Python/Qwen3TTS workspace with project-local training orchestration in `tools/train_voice_candidates.py`.
- **Package manager:** none detected.
- **Build/test/lint commands:** `python tools/train_voice_candidates.py --help`; `python -m unittest discover -s tests`; `bash scripts/run_train_voice_candidates_smoke.sh`; `python -m compileall -q tools scripts`; `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`; `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh`; `git diff --check`; `git status --short --ignored`.
- **Recent baseline:** commit `72b3b29` implemented Stage 6 semi-auto early stopping.
- **Risky areas:** exporting rejected checkpoints, creating review output in a surprising path, and overclaiming that the system chose the final voice.

## Scope

In scope:

- candidate review export directory after training stops;
- copied candidate eval WAVs grouped by rank and epoch;
- copied run `metrics.jsonl` for review/audit;
- deterministic `ranking.md` with checkpoint, selection reason, risks, and audio paths;
- manifest/export metadata that points to the review pack;
- smoke and tests proving the owner only sees selected candidates.

Out of scope:

- selected-checkpoint persistence as the final winner;
- real listening-based naturalness model;
- real speaker embedding backend;
- committing generated review WAVs, metrics copies, checkpoints, or raw `Input/` audio.

## Assumptions

- Add an optional `--candidate_review_root`; when omitted, the orchestrator chooses a deterministic review directory.
- Normal real-run default should be a sibling samples path, equivalent to `experiments/.../samples/<voice>/<run_name>/candidate_review` when `--output_root experiments/.../runs`.
- Candidate folders use stable rank letters: `candidate_A_epoch0`, `candidate_B_epoch1`, `candidate_C_epoch2`, `candidate_D_epoch3`.
- If fewer than four candidates exist, export only the available non-rejected candidates and mark limited status in `ranking.md`.
- Missing selected eval audio is an orchestration error, because the review pack would be unsafe to hand to the owner.

## Risks

1. **Rejected candidates leak into review** - mitigation: export only manifest `candidates`, assert rejected/candidate disjointness in tests and smoke.
2. **Ranking is unhelpful** - mitigation: require checkpoint path, score, why selected, risk bullets, stop summary, and exact audio paths.
3. **Pre-flight breaks on future-only commands** - mitigation: mandatory commands are baseline-safe; phase evidence may grep new outputs only after the phase creates them.

## Phase Map

| # | Phase | Depends on | Deliverable |
|---|-------|------------|-------------|
| 1 | Define Export Contract | none | path/label/report contract and tests |
| 2 | Build Review Export | 1 | review pack writer integrated after selection |
| 3 | Wire Smoke Coverage | 1, 2 | smoke and tests prove export output |
| 4 | Update Docs | 1, 2, 3 | docs say candidate export is implemented |
| 5 | Polish & Harden | 1, 2, 3, 4 | full verification and artifact hygiene |

---

## Phase 1 - Define Export Contract

**Why:** Lock the path, labels, manifest fields, and report schema before copying audio.

**Deliverables:**
- Export path and candidate label helpers in `tools/train_voice_candidates.py`.
- CLI option `--candidate_review_root`.
- Event/manifest field contract for candidate review export.
- Unit tests for path resolution, label generation, parser help, and import safety.

**Acceptance criteria:**
- [ ] A helper resolves the candidate review root deterministically and accepts `--candidate_review_root` override.
- [ ] A rank helper maps rank 1..4 to `candidate_A`..`candidate_D` and includes the epoch in the folder name.
- [ ] Parser help exits 0 and includes the new review-root option.
- [ ] Review export metadata schema is represented in code and can serialize review directory, ranking path, copied metrics path, candidate count, and exported epochs.
- [ ] Importing `tools.train_voice_candidates` still avoids heavy runtime modules.
- [ ] Unit tests cover helper outputs without creating real training artifacts.

**Mandatory commands:**
- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Help excerpt showing review-root option.
- Unit test summary.
- Export contract helper/schema excerpt.
- Command exit codes.

---

## Phase 2 - Build Review Export

**Why:** Create the actual owner-facing candidate folders, copied metrics, and ranking file after selection.

**Deliverables:**
- Review pack writer in `tools/train_voice_candidates.py`.
- `candidate_review/metrics.jsonl` copied from the run metrics.
- `candidate_review/ranking.md` generated with checkpoint, why selected, risks, and audio paths.
- Candidate folders containing copied eval WAVs for selected candidates only.
- Metrics event and manifest metadata pointing to the review pack.

**Acceptance criteria:**
- [ ] Export runs after `candidate_manifest.json` is written.
- [ ] Only `candidate_manifest.json.candidates` are exported; rejected checkpoints are not copied.
- [ ] Each exported candidate folder contains the same fixed eval WAV filenames.
- [ ] `ranking.md` lists rank, epoch, checkpoint path, score, why selected, warnings/risks, and audio files to listen to.
- [ ] The pack includes a copied `metrics.jsonl`.
- [ ] The manifest records review directory, ranking path, metrics copy path, exported candidate count, and exported epochs.
- [ ] Missing selected eval audio raises `OrchestrationError` instead of producing an incomplete pack.

**Mandatory commands:**
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Unit test summary.
- Manifest review-pack excerpt.
- `ranking.md` excerpt from a stub run or unit fixture.
- Command exit codes.

---

## Phase 3 - Wire Smoke Coverage

**Why:** Prove the normal no-GPU smoke path produces the same owner-facing pack the real run will produce.

**Deliverables:**
- Smoke script assertions for candidate review directory, candidate folders, copied WAVs, copied metrics, and ranking markdown.
- Smoke output summary with candidate review path and exported candidate count.
- Tests for rejected high-score non-export and limited candidate packs.

**Acceptance criteria:**
- [ ] Smoke exits 0 and prints candidate review directory, exported candidate count, ranking path, and copied metrics path.
- [ ] Smoke exports more than one candidate and fewer than or equal to `top_candidates`.
- [ ] Smoke review folders are named `candidate_A_epoch0`, `candidate_B_epoch1`, etc. for selected candidates.
- [ ] Smoke `ranking.md` contains checkpoint path, selected reason, risk text, and audio filenames.
- [ ] Smoke copied `metrics.jsonl` exists under candidate review and is byte-identical to the run metrics.
- [ ] Unit tests prove a rejected high-score checkpoint is not exported.
- [ ] Unit tests prove limited candidate count is reflected in ranking/report text.

**Mandatory commands:**
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

**Evidence required:**
- Smoke output summary.
- Candidate review tree listing.
- `ranking.md` excerpt.
- Command exit codes.

---

## Phase 4 - Update Docs

**Why:** Documentation must shift candidate WAV export from future work to implemented workflow without claiming final voice persistence.

**Deliverables:**
- Updated `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- Updated `docs/RUNBOOK.md`.
- Updated `scripts/README.md`.
- Updated `docs/templates/CANDIDATE_REVIEW_REPORT.md`.
- Updated `README.md` and `docs/PROJECT_STATUS.md` if they mention export as future-only.

**Acceptance criteria:**
- [ ] Docs state Stage 7 exports a candidate review pack after semi-auto stopping.
- [ ] Docs list the review pack shape including candidate folders, `ranking.md`, and copied `metrics.jsonl`.
- [ ] Docs explain that the owner listens only to exported candidates, not every epoch.
- [ ] Docs state final winner remains human-selected and selected-checkpoint persistence is still out of scope.
- [ ] Docs keep generated review WAVs, copied metrics, checkpoints, generated manifests, and raw `Input/` audio out of commit scope.
- [ ] Docs mention the optional review-root override or deterministic default path.

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

## Phase 5 - Polish & Harden

**Why:** Verify the export layer is deterministic, safe, documented, and ready before real training.

**Deliverables:**
- Final candidate review export implementation, tests, smoke assertions, docs, and plan state.

**Acceptance criteria:**
- [ ] `python tools/train_voice_candidates.py --help` exits 0 and documents review-root/candidate options.
- [ ] `python -m unittest discover -s tests` exits 0.
- [ ] `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and emits review-pack evidence.
- [ ] `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- [ ] `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh scripts/run_train_voice_candidates_smoke.sh` exits 0.
- [ ] `git diff --check` exits 0.
- [ ] `git status --short --ignored` shows no generated review WAVs, copied metrics, checkpoints, generated manifests, or raw `Input/` audio as normal commit candidates.
- [ ] Added-lines cleanliness check finds no conflict markers, debug prints, or task markers in app code.
- [ ] Docs do not imply selected-checkpoint persistence or automatic final voice choice is complete.

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
- Smoke candidate-review summary.
- Candidate review tree and ranking excerpt.
- Artifact hygiene summary.
