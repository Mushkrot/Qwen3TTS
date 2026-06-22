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
- Architecture: `docs/ARCHITECTURE.md`
- Operational runbook: `docs/RUNBOOK.md`
- Artifact and data policy: `docs/ARTIFACT_POLICY.md`
- Dataset contract: `docs/DATASET_CONTRACT.md`
- Voice filtering policy: `docs/VOICE_FILTERING_POLICY.md`
- Voice filtering rollout notes: `docs/VOICE_FILTERING_ROLLOUT_NOTES.md`
- Evaluation protocol: `docs/EVAL_PHRASE_SET.md`
- Deep research context: `docs/VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md`
- Historical audit context: `docs/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md`

## Working assets

- Experiment workspace: `experiments/qwen3_ru_en_speaker_v1/`
- Helper scripts: `scripts/README.md`
- Project-local voice scaffold: `datasets/voices/<VoiceName>/{Input,Ready}`

## Current baseline decisions

- Primary stack: **Qwen3-TTS**
- Active production-candidate lineage in docs: `Qwen/Qwen3-TTS-12Hz-1.7B-Base`
- `0.6B` remains a debug track because upstream fine-tuning had an embedding-shape mismatch.
- Raw audio placed under `datasets/voices/**/Input/` is local source material and is never committed.
- Generated chunks, manifests, checkpoints, and samples are generated artifacts unless a small template/scaffold file is explicitly tracked.

## Current repository state

As of 2026-06-22:

- Dataset scaffold is tracked and restored with `.gitkeep` files.
- `.venv` has been recreated and runtime imports pass for `torch`, `qwen_tts`, `soundfile`, and `faster_whisper`.
- Voice-filter smoke passes in default local mode by using the Baritone input as a filter-only source.
- Full ASR smoke requires an explicit known-good short speech source; the current local Baritone fallback is not treated as a strict ASR fixture.
- Historical checkpoints and sample packs named in older docs are not present in the working tree and must be restored from backup or regenerated before evaluation.

## Quick onboarding

1. Read `docs/PROJECT_STATUS.md` first.
2. Read `docs/ARTIFACT_POLICY.md` before staging anything.
3. Use `docs/RUNBOOK.md` for verification commands.
4. Use `scripts/README.md` for dataset-building commands.
