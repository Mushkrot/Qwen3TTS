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

## Fixed eval phrase set

Generate exactly these 5 files for every checkpoint under test:

1. `01_en_short.wav` - `She said she would be here by noon.`
2. `02_en_long.wav` - `The old railway station was quiet in the morning, but by evening it was full of people waiting for the last train.`
3. `03_en_calm.wav` - `Take a slow breath, relax your shoulders, and speak with calm confidence.`
4. `04_ru_short.wav` - `Сегодня хороший день для спокойной и ясной речи.`
5. `05_ru_long.wav` - `Когда голос звучит естественно, слушатель легко понимает каждую фразу и не отвлекается на шум или странные паузы.`

The English phrases remain the primary product objective. The Russian phrases
are sanity checks for speaker identity and stability on source-language speech.

## Generation rules

- Keep `speaker` constant across all runs (`speaker_target`).
- Keep `attn_implementation` constant across all runs (`sdpa` unless explicitly changed for all checkpoints).
- Keep device and dtype constant (`cuda:0`, `bfloat16`) when possible.
- Do not change punctuation or wording in the phrase set.
- Save outputs under deterministic paths:
  - `experiments/qwen3_ru_en_speaker_v1/samples/<voice_name>/<run_name>/candidate_review/candidate_A_epochN/01_en_short.wav`
  - `.../02_en_long.wav`
  - `.../03_en_calm.wav`
  - `.../04_ru_short.wav`
  - `.../05_ru_long.wav`

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
7. Russian sanity
   - Russian phrases remain stable and recognizable without overriding the English objective.

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
