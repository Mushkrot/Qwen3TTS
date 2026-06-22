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
- Historical best checkpoint for product goals: `runs/sft_1_7b_smoke1/checkpoint-epoch-0`.
- Current filesystem state: historical run/sample artifacts are not present in `experiments/`.
- Training policy: use the documented semi-automatic candidate review protocol in
  `docs/CHECKPOINT_SELECTION_PROTOCOL.md`; project-local orchestration now
  supports epoch-by-epoch checkpoints, eval packs, automatic metrics,
  hard-reject gates, semi-auto early stopping, candidate manifests, and
  exported candidate review packs. Default stopping values are `min_epochs=2`,
  `max_epochs=6`, `patience=2`, and `top_candidates=4`. The review pack copies
  selected eval WAVs, `ranking.md`, and `metrics.jsonl`; the owner then records
  the human winner with `tools/select_voice_candidate.py`, which writes
  `selected_checkpoint.json`, `experiment_status.json`, and
  `winner_selection` metadata without copying checkpoints or audio.
- Raw source audio in `datasets/voices/**/Input/` is never committed.
- Commit code, docs, scaffolds, small config, and reproducible patches only.

---

## Current verified state (2026-06-22)

### Working

- Tracked repository scaffold is intact.
- Dataset voice folders are restored and tracked through `.gitkeep` files:
  - `datasets/voices/Dima/{Input,Ready}`
  - `datasets/voices/Baritone/{Input,Ready}`
- Local Baritone source audio exists under ignored `datasets/voices/Baritone/Input/`.
- `.venv` has been recreated.
- Runtime imports pass:
  - `torch` imports and CUDA is visible;
  - `qwen_tts` imports with the expected optional `flash-attn` warning;
  - `soundfile` imports;
  - `faster_whisper` imports.
- Static checks pass:
  - `python -m compileall -q scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
  - `bash -n scripts/run_prepare_data.sh scripts/run_sft_0_6b.sh scripts/run_voice_filter_smoke.sh`
- Default local smoke passes:
  - `bash scripts/run_voice_filter_smoke.sh`
  - current fallback uses local Baritone input and runs filter-only smoke unless full ASR is explicitly required.
- Training candidate and winner-selection smokes pass:
  - `bash scripts/run_train_voice_candidates_smoke.sh`
  - `bash scripts/run_select_voice_candidate_smoke.sh`
  - the selection smoke chooses `candidate_B_epoch1`, verifies status metadata,
    and verifies no checkpoint/WAV/metrics copy is created by selection.
- Deployment status: this repository has no long-running service or public
  deployment target for the current stage. The deploy/release gate is a
  verified local workflow snapshot: docs, tests, smoke checks, artifact hygiene,
  and a Git commit preserving the current implementation.

### Not restored / not ready

- `experiments/qwen3_ru_en_speaker_v1/runs/` contains only scaffold, no restored checkpoint.
- `experiments/qwen3_ru_en_speaker_v1/samples/` contains only scaffold, no restored sample pack.
- `experiments/qwen3_ru_en_speaker_v1/manifests/train_raw.jsonl` is not present.
- Full ASR smoke with current local Baritone fallback is not a stable fixture and can produce `ERROR: no dataset rows produced`.
- `.git/objects/pack/` contains old `tmp_pack_*` garbage files from a previous interrupted Git operation; do not clean them without a deliberate recovery/backup decision.

---

## Historical progress snapshot

These items describe prior project history and may refer to generated artifacts that are not currently present in the working tree.

### Completed historically
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
- Restore or regenerate the manifest/checkpoint/sample artifacts before any new evaluation.
- Build a fresh Baritone dataset with current voice-filtering rules.

---

## Runbook for a new developer

1. Read `README.md`, `docs/ARTIFACT_POLICY.md`, and `docs/RUNBOOK.md`.
2. Confirm `git status --ignored --short` does not show raw `Input/` audio as untracked stage candidates.
3. Confirm runtime checks pass.
4. Continue with dataset handoff/build checklist and preprocessing stage.
5. Use `scripts/README.md` for command-level helpers.
6. Use `docs/CHECKPOINT_SELECTION_PROTOCOL.md` before comparing training checkpoints.

---

## Operational rules

- Keep documentation current after each major step.
- Record blockers and exact error messages in commit messages or docs.
- Keep experiment outputs in deterministic paths under `experiments/`.

## Known blockers

1. Optional `flash-attn` remains unresolved and has not been revalidated after the 2026-06-22 environment rebuild.
2. `0.6B` fine-tune path currently fails with embedding shape mismatch in upstream script.
3. Historical checkpoint/sample artifacts are not present in this checkout.
4. Current full ASR smoke requires a known-good speech fixture; raw Baritone fallback is validated only through filter-only smoke by default.

---

## Next update trigger

Update this file immediately after:
- next dataset-quality iteration is prepared and evaluated with the same phrase set.

## Immediate next action

1. Build a fresh dataset under `datasets/voices/Baritone/Ready/<run_name>` with `--voice_filter_reject_initial_seconds 30` for Baritone-style audiobook sources.
2. Review quarantine/report output to confirm music/noise/non-speech rejection, including `initial_window_rejected` for title/intro chunks.
3. Spot-check accepted chunks by ear before training.
4. Restore or regenerate checkpoints/samples before measuring model quality.
