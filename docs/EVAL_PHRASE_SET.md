# Evaluation Phrase Set and Scoring Checklist

## Purpose

This document defines a fixed evaluation protocol for comparing Qwen3-TTS checkpoints.
Use the same phrase set and scoring rubric for every run to keep decisions reproducible.

Checkpoint selection and semi-automatic stopping rules are defined in
`docs/CHECKPOINT_SELECTION_PROTOCOL.md`. This file remains the canonical fixed
phrase and listening-score source used by that protocol.

## Frozen production candidate

Historical reference checkpoint from previous status notes:
- `experiments/qwen3_ru_en_speaker_v1/runs/sft_1_7b_smoke1/checkpoint-epoch-0`

Current 2026-06-22 filesystem state:
- that checkpoint is not present in the working tree;
- `experiments/qwen3_ru_en_speaker_v1/runs/` and `samples/` currently contain only tracked scaffolds;
- restore the historical checkpoint/sample artifacts from backup, or regenerate them, before running this evaluation protocol.

## Fixed English phrase set

Generate exactly these 5 phrases for every checkpoint under test:

1. `This is a baseline quality check for the cloned voice.`
2. `The system should speak naturally, with stable rhythm and clear pauses.`
3. `In this lecture, we discuss the relationship between force, mass, and acceleration.`
4. `Please slow down slightly and keep a calm, explanatory tone.`
5. `The final result must sound close to the original speaker identity.`

## Generation rules

- Keep `speaker` constant across all runs (`speaker_target`).
- Keep `attn_implementation` constant across all runs (`sdpa` unless explicitly changed for all checkpoints).
- Keep device and dtype constant (`cuda:0`, `bfloat16`) when possible.
- Do not change punctuation or wording in the phrase set.
- Save outputs under deterministic paths:
  - `experiments/qwen3_ru_en_speaker_v1/samples/<run_name>_<checkpoint_tag>/01_sample.wav`
  - `.../02_sample.wav`
  - `.../03_sample.wav`
  - `.../04_sample.wav`
  - `.../05_sample.wav`

## Scoring checklist (1-5)

Score each category from 1 (bad) to 5 (excellent):

1. Speaker similarity
   - How close the generated voice is to the target identity.
2. Naturalness
   - Human-like delivery without robotic artifacts.
3. Onset quality
   - No noisy/breathy/unnatural starts.
4. Offset quality
   - No abrupt or truncated endings.
5. Pace and rhythm
   - Stable speed, no rushing, natural pauses.
6. English pronunciation clarity
   - Correct and intelligible English articulation.

Optional notes per phrase:
- Accent character (e.g., RU accent strong/medium/light).
- Artifact notes (hiss, clicks, breath noise, cutoff).

## Decision rule for checkpoint selection

Primary objective priority:
1. Naturalness
2. Speaker similarity
3. Pace and rhythm
4. Onset/offset quality
5. English pronunciation clarity

Selection policy:
- Promote a new checkpoint only if it is not worse on naturalness and onset/offset quality.
- If pronunciation improves but naturalness regresses, keep the older checkpoint.
- Apply early stopping when later epochs start to degrade naturalness or pacing.
- For semi-automatic candidate review, apply the hard gates, stopping defaults,
  and top-candidate export rules in `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- Treat pace regression as a first-class risk: upstream Qwen3-TTS issue
  `QwenLM/Qwen3-TTS#179` reports progressively faster speech across epochs.

## Minimal evaluation report template

Use this template after each run:

- Run ID:
- Checkpoint compared:
- Baseline checkpoint:
- Mean scores (Similarity/Naturalness/Onset/Offset/Pace/Pronunciation):
- Key observations:
- Final decision: keep baseline / promote checkpoint
