# Qwen3TTS Implementation Plan (Sub-task #1)

## 1) Goal and Scope

### Primary goal
Build a reproducible workflow to train/adapt **Qwen3-TTS** for a **single target speaker** using a Russian voice dataset and generate English speech with:
- high speaker similarity,
- natural prosody,
- controllable pace/pauses/prosody.

### In scope
- environment setup,
- project structure,
- model installation,
- dataset contract definition,
- first fine-tuning cycle,
- Sub-task #1 evaluation protocol.

### Out of scope (for now)
- video synchronization,
- dubbing pipeline orchestration,
- muxing and timeline alignment.

---

## 2) Confirmed constraints

- Runtime: single NVIDIA GPU with 24GB VRAM.
- Stack: Qwen3-TTS as primary candidate.
- Work mode: clean restart, avoid dependency on previous failed pipeline.
- Priority order:
  1. speaker identity similarity,
  2. naturalness,
  3. controllability (pace, pauses, prosody).

---

## 3) Working directory layout

Recommended structure under the current repository workspace:

```text
/ai/Qwen3TTS/
  docs/
  experiments/
    qwen3_ru_en_speaker_v1/
      manifests/
      runs/
      samples/
      notes/
```

Notes:
- Keep training artifacts in `experiments/.../runs/`.
- Keep manifest files in `experiments/.../manifests/`.
- Keep generated sample WAVs in `experiments/.../samples/`.
- Do not store secrets in repo.

---

## 4) Execution phases

## Phase A — Environment bootstrap
1. Verify CUDA visibility and GPU memory.
2. Create/verify Python virtual environment.
3. Install Qwen3-TTS dependencies.
4. Run a minimal import/smoke check.

Exit criteria:
- dependencies installed without conflicts,
- Qwen3-TTS scripts import successfully,
- baseline inference command is runnable.

## Phase B — Data contract (without committing dataset yet)
1. Freeze JSONL schema for training entries.
2. Define required audio/text validation checks.
3. Define a `ref_audio` policy for speaker identity consistency.
4. Prepare template manifest examples.

Exit criteria:
- approved manifest schema,
- approved folder/path conventions,
- clear checklist for dataset handoff.

## Phase C — Preprocessing and code extraction
1. Build `train_raw.jsonl` from approved dataset structure.
2. Run `prepare_data.py` to generate audio codes.
3. Validate output integrity before training.

Exit criteria:
- no broken paths,
- no empty records,
- valid prepared manifest for SFT.

## Phase D — First fine-tuning cycle (0.6B baseline)
1. Start first SFT run (`sft_12hz.py`) on 0.6B.
2. Save checkpoints and logs in run-specific folder.
3. Generate fixed evaluation sample set (same text prompts each run).

Exit criteria:
- successful train run completion,
- checkpoints saved,
- sample generation completed.

## Phase E — Sub-task #1 evaluation
1. Speaker similarity listening test (fixed prompt set).
2. Naturalness listening test (long-form + short-form).
3. Control test for pace/pauses/prosody on English text.
4. Compare against baseline run notes.

Exit criteria:
- decision: continue tuning / adjust data / switch model tier.

---

## 5) Evaluation protocol (Sub-task #1 only)

Use a stable prompt pack for every run:
- short neutral lines,
- technical lecture-like sentences,
- long paragraphs with punctuation,
- explicit slow/normal pacing instructions.

Track per run:
- perceived speaker similarity,
- perceived naturalness,
- controllability response quality,
- major artifacts (instability, accent collapse, rhythm drift).

---

## 6) Risks to control early

- Manifest/data formatting errors causing training instability.
- Inconsistent `ref_audio` strategy reducing identity lock.
- Overfitting on narrow speech patterns.
- Weak controllability despite good timbre similarity.

---

## 7) Deliverables for this stage

1. Reproducible setup instructions.
2. Approved dataset contract and manifest template.
3. First fine-tuning run artifacts and notes.
4. Initial quality assessment report for Sub-task #1.

---

## 8) Immediate next step

Proceed with **Phase A (Environment bootstrap)** and document exact install commands and validation checks in a dedicated setup guide (`docs/QWEN3TTS_SETUP.md`).
