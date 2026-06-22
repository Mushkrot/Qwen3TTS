SUPERGOAL_PHASE_START
Phase: 1 of 5 — Define Contract
Task: Define the CLI contract and testable path model for the Qwen3TTS training orchestrator.
Type: brownfield, Python, ML workflow
Mandatory commands: python tools/train_voice_candidates.py --help; python -m unittest discover -s tests; python -m compileall -q tools; git diff --check
Acceptance criteria: 5
Evidence required: CLI help excerpt, unit test summary, path model evidence, command exit codes
Depends on phases: none

## Why

The orchestrator must be testable without real GPU training before it starts running heavy subprocesses.

## Work

- Create `tools/train_voice_candidates.py` with argparse-based CLI and no heavy imports at import time.
- Create `tools/__init__.py` if needed for importable tests.
- Create `tests/test_train_voice_candidates.py` using only standard-library `unittest`.
- Define a deterministic run path model: prepared manifest, epoch run dirs, checkpoint path, eval dirs, command logs, and `metrics.jsonl`.
- Define the default eval phrase filenames requested by the user.

## Acceptance criteria (all must pass — verify each in transcript)

- `python tools/train_voice_candidates.py --help` exits 0 and shows `--voice_name`, `--train_raw_jsonl`, `--output_root`, `--run_name`, `--max_epochs`, and `--speaker_name`.
- The CLI has a stub or command-template mode that can be used by tests without importing `torch`, `qwen_tts`, or `soundfile`.
- The script defines deterministic paths for prepared manifest, per-epoch run dirs, checkpoint paths, eval dirs, logs, and `metrics.jsonl`.
- The initial unit tests assert the path model and default eval phrase filenames.
- `python -m unittest discover -s tests` exits 0.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools`
- `git diff --check`

Command classes:

- `python tools/train_voice_candidates.py --help`: requires-phase-1; run after this phase creates `tools/train_voice_candidates.py`.
- `python -m unittest discover -s tests`: requires-phase-1; run after this phase creates `tests/`.
- `python -m compileall -q tools`: requires-phase-1; run after this phase creates `tools/`.
- `git diff --check`: baseline-safe.

## Evidence required in transcript

- CLI help excerpt.
- Unit test summary.
- Path model excerpt from tests or script.
- Command exit codes.

## Notes

- Do not import Qwen, Torch, or soundfile at module import time.
- Do not create real checkpoints or WAV files in this phase.
- These mandatory commands are phase-local checks, not pre-flight checks.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-2-3-training-orchestrator-YjbP5r/PROTOCOL.md without further
instruction needed here.
