# Project Status

## Mission

Primary mission for current stage:
- Sub-task #1 only (speaker identity + EN generation quality),
- no synchronization work in this stage.

Reference docs:
- `docs/QWEN3TTS_IMPLEMENTATION_PLAN.md`
- `docs/QWEN3TTS_SETUP.md`
- `docs/DATASET_CONTRACT.md`
- `docs/EVAL_PHRASE_SET.md`
- `docs/VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md`
- `docs/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md`

---

## Current decisions

- Primary stack: Qwen3-TTS.
- Active training track: `Qwen/Qwen3-TTS-12Hz-1.7B-Base`.
- `0.6B` currently in separate debug track due shape mismatch in upstream fine-tuning script.
- Current best checkpoint for product goals: `runs/sft_1_7b_smoke1/checkpoint-epoch-0`.
- Training policy: early stopping after first epoch unless listening tests clearly improve naturalness.

---

## Progress snapshot

### Completed
- Repository initialized at `/ai/Qwen3TTS`.
- Initial planning doc created.
- Setup guide created.
- Dependencies file created (`requirements.txt`).
- Environment template created (`.env.example`).
- Virtual environment prepared (`.venv`) and dependencies installed.
- Upstream repository cloned: `external/Qwen3-TTS`.
- Runtime checks passed (`torch`, CUDA visibility, `qwen_tts` import).
- Baseline model and tokenizer pre-downloaded from Hugging Face.
- Lock snapshot generated: `requirements.lock.txt`.
- Dataset contract documented (`docs/DATASET_CONTRACT.md`).
- Experiment scaffold created (`experiments/qwen3_ru_en_speaker_v1`).
- Helper scripts added for validate/prepare/train/infer (`scripts/`).
- `sox` installed and verified on host.
- Smoke preprocessing completed (`train_with_codes_24k.jsonl`).
- Smoke SFT completed on 1.7B (`runs/sft_1_7b_smoke1/checkpoint-epoch-0`).
- Longer run completed on 1.7B (`runs/sft_1_7b_run2_e3`, epochs 0..2 checkpoints saved).
- Listening feedback captured: later checkpoint (`run2 epoch-2`) improved EN accent but regressed naturalness (faster pace, abrupt start/end).
- Comparison sample packs generated for `run2 epoch-0` and `run2 epoch-1`.
- Final listening verdict: `mini_pack_en` is best for product goals (most natural rhythm/starts/ends; good speaker similarity), while run2 packs show stronger accent trade-offs but worse artifacts.
- Eval cycle run3 completed: `runs/sft_1_7b_run3_e1_eval/checkpoint-epoch-0`.
- Eval phrase-set samples generated: `samples/mini_pack_en_run3_epoch0_eval`.
- Run3 listening verdict: very close to baseline, but slightly worse start quality (minor extra noise).
- Checkpoint decision: keep frozen baseline `runs/sft_1_7b_smoke1/checkpoint-epoch-0`; do not promote run3.

### In progress
- Optional performance optimization (`flash-attn`) remains unresolved.
- Separate debug track for 0.6B shape mismatch.

### Pending
- No blocking pending items for current stage; production candidate is frozen.

---

## Runbook for a new developer

1. Read `docs/QWEN3TTS_IMPLEMENTATION_PLAN.md`.
2. Execute `docs/QWEN3TTS_SETUP.md` step-by-step.
3. Confirm runtime checks pass.
4. Continue with dataset handoff checklist and preprocessing stage.
5. Use `scripts/README.md` for command-level run helpers.

---

## Operational rules

- Keep documentation current after each major step.
- Record blockers and exact error messages in commit messages or docs.
- Keep experiment outputs in deterministic paths under `experiments/`.

## Known blockers

1. Optional `flash-attn` installation failed due CUDA mismatch (`13.0` detected vs torch CUDA `12.8`).
2. `0.6B` fine-tune path currently fails with embedding shape mismatch in upstream script.

---

## Next update trigger

Update this file immediately after:
- next dataset-quality iteration is prepared and evaluated with the same phrase set.

## Immediate next action

1. Keep current production candidate as baseline checkpoint.
2. Pause model-training iterations for this dataset snapshot.
3. Prepare dataset-quality improvements before the next training cycle.
