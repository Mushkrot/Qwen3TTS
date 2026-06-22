SUPERGOAL_PHASE_START
Phase: 2 of 5 — Build Orchestrator
Task: Implement prepare_data and one-epoch training orchestration with durable metrics.jsonl logging.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 8
Evidence required: unit test summary, example metrics rows, command exit codes
Depends on phases: 1

## Why

The user needs one command that can drive prepare_data through epoch-0 checkpoint creation without manual intermediate steps.

## Work

- Implement the real command defaults for prepare and training:
  - prepare defaults to `scripts/run_prepare_data.sh`.
  - training defaults to upstream `external/Qwen3-TTS/finetuning/sft_12hz.py` or existing wrappers with `NUM_EPOCHS=1`.
- Implement explicit stub/command-template support for smoke tests.
- Append metrics rows for run start, prepare start/end, train start/end, checkpoint observed, and failure.
- Stop on subprocess failure with non-zero exit and a failure metrics row.
- Keep command logs under the run output directory.

## Acceptance criteria (all must pass — verify each in transcript)

- The script accepts a voice name and ready `train_raw.jsonl` path.
- The script runs prepare once and writes/uses a prepared manifest path.
- The script runs training as one-epoch jobs, one loop iteration per requested epoch.
- The script records `init_model_path` for every epoch; epoch 0 uses the configured base model, and epoch N>0 uses the previous checkpoint by default or fails clearly if that mode is not available.
- After epoch 0, the script records a checkpoint path and appends a JSONL metrics row with `event="checkpoint"`, `epoch=0`, and `checkpoint_path`.
- `metrics.jsonl` is append-only JSONL with run metadata, command exit status, started/finished timestamps, and paths.
- Command failures stop the run with a non-zero exit and a metrics row marking the failed stage.
- Unit tests cover both success and failure without launching real Qwen training.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

Command classes:

- `python -m unittest discover -s tests`: requires-phase-1; Phase 2 runs it after expanding tests.
- `python -m compileall -q tools scripts`: requires-phase-1; Phase 2 runs it after `tools/` already exists.
- `git diff --check`: baseline-safe.

## Evidence required in transcript

- Unit test summary.
- Example `metrics.jsonl` rows from a temporary test/smoke run.
- Command exit codes.

## Notes

- Be explicit in help/docs about epoch semantics: this is project-level one-epoch orchestration around upstream SFT, not upstream native early stopping.
- If previous-checkpoint initialization is supported, make it a documented option; if not proven, fail clearly rather than silently pretending resume is guaranteed.
- These mandatory commands are phase-local checks, not pre-flight checks.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-2-3-training-orchestrator-YjbP5r/PROTOCOL.md without further
instruction needed here.
