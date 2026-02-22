# Qwen3TTS

This repository is the working workspace for **Qwen3-TTS Sub-task #1**:

- Train/adapt a single target speaker on a Russian dataset.
- Generate English speech with high speaker similarity and naturalness.
- Validate controllability (pace, pauses, prosody).

Synchronization and dubbing pipeline orchestration are intentionally out of scope for this stage.

## Documentation index

- Implementation plan: `docs/QWEN3TTS_IMPLEMENTATION_PLAN.md`
- Setup and installation: `docs/QWEN3TTS_SETUP.md`
- Live project state: `docs/PROJECT_STATUS.md`
- Dataset contract: `docs/DATASET_CONTRACT.md`
- Deep research context: `docs/VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md`
- Historical audit context: `docs/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md`

## Working assets

- Experiment workspace: `experiments/qwen3_ru_en_speaker_v1/`
- Helper scripts: `scripts/README.md`

## Current baseline decisions

- Primary stack: **Qwen3-TTS**
- First run model: `Qwen/Qwen3-TTS-12Hz-0.6B-Base`
- Defer `1.7B` until first 0.6B cycle is stable and reproducible

## Quick onboarding

1. Read `docs/QWEN3TTS_IMPLEMENTATION_PLAN.md`.
2. Execute `docs/QWEN3TTS_SETUP.md`.
3. Check `docs/PROJECT_STATUS.md` for the latest blockers and next step.