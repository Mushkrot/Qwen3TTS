# Thinking: Stage 2/3 Training Orchestrator + Eval Pack

## Goal

Build a project-local training orchestrator that can be launched with one command, accepts a voice name and ready dataset manifest, runs preprocessing, trains checkpoint candidates one epoch at a time, writes `metrics.jsonl`, and generates a fixed eval audio pack after each checkpoint.

## Constraints

- Preserve existing uncommitted Stage 1 documentation changes.
- Do not run real GPU training during ordinary verification.
- Do not commit raw audio, generated dataset chunks, generated checkpoints, or generated WAV samples.
- Use project-local orchestration instead of pretending upstream Qwen3-TTS has native early stopping.
- Keep the first implementation conservative and observable; it should be easy to inspect the exact commands run.

## Architecture Direction

Create `tools/train_voice_candidates.py` as a standard-library Python CLI. It should:

- accept `--voice_name`, `--train_raw_jsonl`, `--output_root`, `--run_name`, `--max_epochs`, `--speaker_name`;
- derive deterministic paths for prepared manifest, runs/checkpoints, eval pack, logs, and metrics;
- run `prepare_data` once;
- for each epoch, run a one-epoch SFT command and expect a `checkpoint-epoch-0` inside the per-epoch work dir, then publish/record it as `checkpoint-epoch-N`;
- record `init_model_path` for every epoch; epoch 0 starts from the configured base model, and epoch N>0 must start from the previous checkpoint by default unless the user explicitly selects a fresh-candidate mode;
- after each checkpoint, run five inference commands with stable filenames:
  - `01_en_short.wav`
  - `02_en_long.wav`
  - `03_en_calm.wav`
  - `04_ru_short.wav`
  - `05_ru_long.wav`
- append JSONL rows to `metrics.jsonl` for prepare, train, checkpoint, and eval events.

For verification, add a stub mode or command-template mode so `bash scripts/run_train_voice_candidates_smoke.sh` can prove the sequence without loading Qwen models.

## Top Risks

1. Upstream SFT does not support true optimizer-state resume.
   - Likelihood: high.
   - Mitigation: make Stage 2 explicit: one epoch job per candidate checkpoint; epoch N>0 defaults to previous-checkpoint initialization, records that path in metrics, and fails clearly if the previous checkpoint cannot be used. A separate explicit fresh-candidate mode may exist, but it must not be the silent default.

2. Smoke tests accidentally launch heavy model downloads/training.
   - Likelihood: medium.
   - Mitigation: require a stub smoke mode or overridable command templates; mandatory smoke must run under `/tmp` and create sentinel checkpoint/WAV files.

3. Generated artifacts get staged accidentally.
   - Likelihood: medium.
   - Mitigation: default real outputs to ignored `experiments/**/runs` and `experiments/**/samples`, smoke outputs to `/tmp`, and update docs with artifact reminders.

## Dependencies

- `scripts/run_prepare_data.sh`
- `external/Qwen3-TTS/finetuning/sft_12hz.py`
- `scripts/run_infer_sample.py`
- Stage 1 `docs/CHECKPOINT_SELECTION_PROTOCOL.md`
- Existing artifact policy and `.gitignore`

## Assumptions

- Script path will be `tools/train_voice_candidates.py` as the user suggested.
- The first ready implementation can verify orchestration with stub commands and can provide real command defaults for production runs.
- Default eval pack includes exactly the five filenames requested by the user, with three English and two Russian prompts.
- Real training continuation beyond one epoch may require a later patch if previous-checkpoint initialization proves incompatible; the orchestrator should make that risk visible instead of hiding it.
