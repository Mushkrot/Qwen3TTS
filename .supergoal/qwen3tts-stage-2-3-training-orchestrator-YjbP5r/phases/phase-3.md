SUPERGOAL_PHASE_START
Phase: 3 of 5 — Generate Eval Pack
Task: Generate the fixed five-file eval pack automatically after every checkpoint.
Type: brownfield, Python, ML workflow
Mandatory commands: python -m unittest discover -s tests; python -m compileall -q tools scripts; git diff --check
Acceptance criteria: 6
Evidence required: unit test summary, eval tree listing, eval metrics rows, command exit codes
Depends on phases: 1, 2

## Why

After each checkpoint, the user should get ready-to-listen comparison files without running inference manually.

## Work

- Add eval phrase definitions to `tools/train_voice_candidates.py`.
- Add eval generation after each checkpoint.
- Use `scripts/run_infer_sample.py` as the real inference default.
- Support stub inference for smoke tests.
- Append `eval_sample` metrics rows.

## Acceptance criteria (all must pass — verify each in transcript)

- After every checkpoint, the script creates `eval/epoch-N/`.
- Each epoch eval dir contains or expects exactly these output files: `01_en_short.wav`, `02_en_long.wav`, `03_en_calm.wav`, `04_ru_short.wav`, `05_ru_long.wav`.
- The eval phrase list includes three English prompts and two Russian prompts.
- The script invokes inference once per eval phrase with checkpoint, speaker, text, language, and output path.
- Eval generation appends JSONL metrics rows with `event="eval_sample"` and output paths.
- Unit tests verify eval generation in stub mode without importing Qwen.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`
- `git diff --check`

Command classes:

- `python -m unittest discover -s tests`: requires-phase-1; Phase 3 runs it after adding eval tests.
- `python -m compileall -q tools scripts`: requires-phase-1; Phase 3 runs it after `tools/` already exists.
- `git diff --check`: baseline-safe.

## Evidence required in transcript

- Unit test summary.
- Example eval directory listing from a stub run.
- Example eval metrics rows.
- Command exit codes.

## Notes

- Use exact output filenames from the user request.
- Keep prompts editable in code/config, but make the default deterministic.
- These mandatory commands are phase-local checks, not pre-flight checks.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-2-3-training-orchestrator-YjbP5r/PROTOCOL.md without further
instruction needed here.
