# Project Status

## Mission

Primary mission for current stage:
- Sub-task #1 only (speaker identity + EN generation quality),
- no synchronization work in this stage.

Reference docs:
- `docs/QWEN3TTS_IMPLEMENTATION_PLAN.md`
- `docs/QWEN3TTS_SETUP.md`
- `docs/VOICE_CLONING_DEEP_RESEARCH_SINCE_2025-09.md`
- `docs/VOICE_CLONING_PROJECTS_AUDIT_2026-02-21.md`

---

## Current decisions

- Primary stack: Qwen3-TTS.
- Baseline model for first run: `Qwen/Qwen3-TTS-12Hz-0.6B-Base`.
- 1.7B model is deferred until setup + first 0.6B cycle is stable.

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

### In progress
- Resolving system/runtime blockers (`sox`, optional `flash-attn`).

### Pending
- Dataset contract finalization and manifest templates.
- First preprocessing + first SFT run.
- First quality/control evaluation report.

---

## Runbook for a new developer

1. Read `docs/QWEN3TTS_IMPLEMENTATION_PLAN.md`.
2. Execute `docs/QWEN3TTS_SETUP.md` step-by-step.
3. Confirm runtime checks pass.
4. Continue with dataset handoff checklist and preprocessing stage.

---

## Operational rules

- Keep documentation current after each major step.
- Record blockers and exact error messages in commit messages or docs.
- Keep experiment outputs in deterministic paths under `experiments/`.

## Known blockers

1. `sox` binary is missing on host (detected during `qwen_tts` import).
2. Optional `flash-attn` installation failed due CUDA mismatch (`13.0` detected vs torch CUDA `12.8`).

---

## Next update trigger

Update this file immediately after:
- first successful `prepare_data.py` run,
- first successful `sft_12hz.py` run.

## Immediate next action

1. Install system `sox` package on host.
2. Re-run `prepare_data.py --help` sanity check.
3. Freeze dataset contract and create `train_raw.jsonl` template.
