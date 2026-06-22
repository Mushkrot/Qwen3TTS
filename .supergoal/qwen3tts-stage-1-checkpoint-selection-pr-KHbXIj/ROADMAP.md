# Roadmap: Qwen3TTS Stage 1 Checkpoint Selection Protocol

**Task:** Define and document the protocol for semi-automatic checkpoint scoring, stopping, and top-candidate review.
**Type:** brownfield, documentation, ML workflow
**Created:** 2026-06-22
**Total phases:** 4

## Context summary

- **Stack:** Python/Qwen3-TTS workspace with local docs and helper scripts.
- **Package manager:** none detected at repo root; `.venv` is used locally.
- **Build / test / lint commands:** `git diff --check`; `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`; `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh`.
- **Risky areas:** evaluation is currently manual; upstream fine-tuning can degrade pace over epochs; dataset purity is a hard precondition.

## Assumptions

- Create `docs/CHECKPOINT_SELECTION_PROTOCOL.md` as the canonical protocol document.
- Add `docs/templates/CANDIDATE_REVIEW_REPORT.md` as the human-facing report template for future training runs.
- Keep existing `docs/EVAL_PHRASE_SET.md` as the fixed phrase source, extending it only where needed to avoid duplicate/conflicting scoring rules.
- Do not implement training orchestration code in this stage.
- Do not create or commit generated audio/checkpoint artifacts in this stage.

## Risk top 3

1. **Automatic metrics overrule human audio quality** — likelihood: high; mitigation: hard gates only reject obvious failures, soft scores rank candidates, final winner remains a human selection among 3-4 exported candidates.
2. **Protocol duplicates existing eval docs** — likelihood: medium; mitigation: update existing docs to point at one canonical protocol and preserve the current fixed phrase set.
3. **Later checkpoints regress pace/naturalness** — likelihood: high; mitigation: stopping rules include max epochs, patience, pace regression gates, earliest-checkpoint tie break, and the upstream issue `QwenLM/Qwen3-TTS#179` as rationale.

## Phase map

| # | Phase | Depends on | Deliverable |
|---|-------|------------|-------------|
| 1 | Draft Protocol | none | `docs/CHECKPOINT_SELECTION_PROTOCOL.md` |
| 2 | Align Eval Docs | 1 | Existing docs reference the protocol without conflicts |
| 3 | Add Report Template | 1, 2 | `docs/templates/CANDIDATE_REVIEW_REPORT.md` |
| 4 | Polish & Harden | 1, 2, 3 | Final documentation audit and static checks |

---

## Phase 1 — Draft Protocol

**Why:** Establish the canonical decision logic before any automation code is written.

**Deliverables:**
- `docs/CHECKPOINT_SELECTION_PROTOCOL.md`

**Acceptance criteria:**
- [ ] The protocol document defines scope and explicitly says Stage 1 is documentation, not an orchestrator implementation.
- [ ] The protocol lists the fixed eval phrase set or points to the exact canonical phrase source.
- [ ] The protocol defines automatic metrics, including ASR/text match, duration/pace, clipping/RMS, leading/trailing silence, onset/offset, training loss trend, and optional speaker similarity.
- [ ] The protocol separates hard reject gates from soft ranking scores.
- [ ] The protocol defines stopping defaults: minimum epochs, maximum epochs, patience, degradation stop, tie-break behavior, and number of final candidates.
- [ ] The protocol defines the candidate export shape and final report fields.
- [ ] The protocol states that dataset purity is a pre-training gate and references voice filtering docs.

**Mandatory commands:**
- `git diff --check`

**Evidence required:**
- Print the new document path.
- Print the section headings from the new document.
- Print the stopping defaults and hard reject list.
- Print `git diff --check` exit code.

**Dependencies:** none

---

## Phase 2 — Align Eval Docs

**Why:** Make the new protocol part of the existing documentation canon rather than a parallel policy.

**Deliverables:**
- Updated `docs/EVAL_PHRASE_SET.md`
- Updated `docs/PROJECT_STATUS.md`
- Updated `docs/RUNBOOK.md`
- Updated `README.md`

**Acceptance criteria:**
- [ ] `docs/EVAL_PHRASE_SET.md` references `docs/CHECKPOINT_SELECTION_PROTOCOL.md` for checkpoint selection and preserves the existing fixed English phrases.
- [ ] `docs/PROJECT_STATUS.md` describes the current policy as semi-automatic candidate review protocol pending future orchestration.
- [ ] `docs/RUNBOOK.md` includes a short checkpoint-selection/review section that points to the protocol and report template.
- [ ] `README.md` documentation index includes the new protocol and report template.
- [ ] No doc says the project already has fully automatic optimal stopping implemented.

**Mandatory commands:**
- `git diff --check`

**Evidence required:**
- Print `rg -n "CHECKPOINT_SELECTION_PROTOCOL|CANDIDATE_REVIEW_REPORT|automatic optimal|fully automatic" README.md docs`.
- Print `git diff --check` exit code.

**Dependencies:** 1

---

## Phase 3 — Add Report Template

**Why:** Give future training runs a concrete output format for top-3/top-4 user review.

**Deliverables:**
- `docs/templates/CANDIDATE_REVIEW_REPORT.md`

**Acceptance criteria:**
- [ ] The template includes run metadata: voice name, dataset build path, manifest path, model base, training command summary, epoch range, and generated-at timestamp.
- [ ] The template includes one table for candidate ranking with checkpoint, score, hard-gate status, warnings, and review sample path.
- [ ] The template includes a per-candidate listening checklist for similarity, naturalness, onset, offset, pace, pronunciation, and notes.
- [ ] The template includes a final user choice section that records the selected candidate and reason.
- [ ] The template includes artifact policy reminders that generated WAV/checkpoint files are not committed.

**Mandatory commands:**
- `git diff --check`

**Evidence required:**
- Print the new template path.
- Print the top-level headings from the template.
- Print `git diff --check` exit code.

**Dependencies:** 1, 2

---

## Phase 4 — Polish & Harden

**Why:** Catch documentation conflicts, vague criteria, and accidental claims before the protocol becomes project canon.

**Deliverables:**
- Final polished protocol and linked docs.

**Acceptance criteria:**
- [ ] `rg -n "CHECKPOINT_SELECTION_PROTOCOL" README.md docs/EVAL_PHRASE_SET.md docs/PROJECT_STATUS.md docs/RUNBOOK.md` returns at least one hit in each listed file.
- [ ] `rg -n "CANDIDATE_REVIEW_REPORT" README.md docs/RUNBOOK.md docs/CHECKPOINT_SELECTION_PROTOCOL.md` returns at least one hit in each listed file.
- [ ] `rg -n "fully automatic|optimal plateau|best checkpoint automatically" README.md docs` returns no misleading claim that this is already implemented.
- [ ] `rg -n "QwenLM/Qwen3-TTS#179|progressively faster|pace" docs/CHECKPOINT_SELECTION_PROTOCOL.md docs/EVAL_PHRASE_SET.md` shows the pace-regression risk is documented.
- [ ] `git diff --check` exits 0.
- [ ] `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts` exits 0.
- [ ] `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh` exits 0.
- [ ] Final `git diff --stat` shows only docs/template changes expected for Stage 1.

**Mandatory commands:**
- `git diff --check`
- `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh`
- `git diff --stat`

**Evidence required:**
- Print command exit codes.
- Print final `git diff --stat`.
- Print a short summary of changed docs.

**Dependencies:** 1, 2, 3
