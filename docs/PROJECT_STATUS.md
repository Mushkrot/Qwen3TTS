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
- Historical best checkpoint for old product goals: `runs/sft_1_7b_smoke1/checkpoint-epoch-0`.
- Current Baritone full-cycle result: `baritone_full_gpu_005_clean_text_lr2e6`.
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
- Current 1.7B Baritone training policy: use `--learning_rate 2e-6` for the
  real candidate run unless a new controlled experiment proves otherwise.
  A `2e-5` full run overfit text artifacts and produced subtitle-credit
  hallucinations in eval audio.
- Long-form finding from 2026-06-23: Qwen3TTS Baritone timbre is useful for
  short phrases, but the tested Russian-trained voice is not good enough for
  long connected narration. Built-in native-English voices Aiden/Ryan read
  English much better with `02_quality_longer_chunks`; the next Qwen3TTS test
  should use a native-English source speaker with the desired timbre.

---

## Current verified state (2026-06-23)

### Working

- Human-facing generated audio now lives under `datasets/voices/**/Ready/`:
  - `datasets/voices/Aiden/Ready/builtin_quality_2026-06-23/`
  - `datasets/voices/Ryan/Ready/builtin_quality_2026-06-23/`
  - `datasets/voices/Baritone/Ready/prosody_control_2026-06-23/`
- Built-in Aiden/Ryan English `02_quality_longer_chunks` samples are the best
  current long-form Qwen3TTS listening results.
- `experiments/qwen3_ru_en_speaker_v1/` has been cleaned back to lightweight
  scaffolds/templates after useful listening samples were copied to
  `datasets/voices/**/Ready/`.
- The remaining `experiments/` tree is only a technical scratch area:
  `manifests/train_raw.template.jsonl`, `notes/.gitkeep`, `runs/.gitkeep`,
  and `samples/.gitkeep`.

### Not present locally after cleanup

- The generated Baritone checkpoints, eval WAVs, logs, candidate review packs,
  and old experiment samples under `experiments/**/runs/` and
  `experiments/**/samples/` were local ignored artifacts and were removed on
  2026-06-23.
- Any future custom-voice generation with the old A/C checkpoints requires
  retraining, restoring those checkpoints from backup, or passing explicit
  checkpoint paths to the helper scripts.

### Next voice experiment

Collect native-English source recordings with a timbre close to the desired
voice and place them under a new `datasets/voices/<NewVoice>/Input/` folder.
The success test is the same English long-form `02_quality_longer_chunks`
benchmark, judged on reading quality, timbre stability, pace, pauses, and
unclipped word endings.

---

## Previous verified state (2026-06-22)

### Working

- Tracked repository scaffold is intact.
- Dataset voice folders are restored and tracked through `.gitkeep` files:
  - `datasets/voices/Dima/{Input,Ready}`
  - `datasets/voices/Baritone/{Input,Ready}`
- Local Baritone source audio exists under ignored `datasets/voices/Baritone/Input/`.
- Current clean Baritone dataset exists under ignored generated output:
  `datasets/voices/Baritone/Ready/full_gpu_002_clean_text/`.
- Its `train_raw.jsonl` has 988 accepted rows, passed manifest validation, and
  rejects subtitle/title-card boilerplate with `transcript_boilerplate`.
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
- Full real GPU candidate run completed historically:
  - run: `experiments/qwen3_ru_en_speaker_v1/runs/Baritone/baritone_full_gpu_005_clean_text_lr2e6/`;
  - dataset: `datasets/voices/Baritone/Ready/full_gpu_002_clean_text/manifests/train_raw.jsonl`;
  - base model: `Qwen/Qwen3-TTS-12Hz-1.7B-Base`;
  - device: `cuda:0`;
  - learning rate: `2e-6`;
  - stop reason: `patience_exhausted` after epochs 0, 1, and 2;
  - exported review pack:
    `experiments/qwen3_ru_en_speaker_v1/samples/Baritone/baritone_full_gpu_005_clean_text_lr2e6/candidate_review/`;
  - candidates: A/epoch-0, B/epoch-1, C/epoch-2;
  - all selected candidates are non-rejected and have `whisper_text_match_mean=1.0`;
  - known warnings: `leading_silence_too_long`, `speaker_similarity_unavailable`.
  - cleanup note: these generated local artifacts were removed from
    `experiments/` on 2026-06-23 after the owner had listened to the relevant
    outputs and useful samples were copied to `datasets/voices/**/Ready/`.
- Runtime patch needed for real training is preserved as
  `patches/qwen3-tts-sft-runtime-local-model.patch`; the live ignored
  `external/Qwen3-TTS/finetuning/sft_12hz.py` must contain that patch on a
  working checkout.
- Deployment status: this repository has no long-running service or public
  deployment target for the current stage. The deploy/release gate is a
  verified local workflow snapshot: docs, tests, smoke checks, artifact hygiene,
  and a Git commit preserving the current implementation.

### Not restored / not ready

- Historical pre-recovery checkpoints/sample packs are not restored.
- No final Baritone winner should be promoted from the old A/B/C long-form
  test. Listening showed that the Russian-trained Baritone voice is not a good
  long-form narration target for the current goal.
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
- Keep technical training outputs in deterministic paths under `experiments/`,
  but copy owner-facing listening samples to `datasets/voices/<Voice>/Ready/`.

## Known blockers

1. Optional `flash-attn` remains unresolved and has not been revalidated after the 2026-06-22 environment rebuild.
2. `0.6B` fine-tune path currently fails with embedding shape mismatch in upstream script.
3. Historical checkpoint/sample artifacts from before recovery are not present in this checkout.
4. Current full ASR smoke requires a known-good speech fixture; raw Baritone fallback is validated only through filter-only smoke by default.
5. Speaker-similarity scoring is still unavailable, so final voice identity choice remains human listening.

---

## Next update trigger

Update this file immediately after:
- a new native-English source speaker is added under `datasets/voices/`;
- a new Qwen3TTS English-speaker training run produces listening samples.

## Immediate next action

1. Add the next native-English source speaker under
   `datasets/voices/<NewVoice>/Input/`.
2. Build/train a new voice aimed at English long-form narration quality.
3. Compare against built-in Aiden/Ryan `02_quality_longer_chunks`.
4. Commit only code/docs/patch/test changes, not raw audio, generated datasets,
   checkpoints, or candidate WAVs.
