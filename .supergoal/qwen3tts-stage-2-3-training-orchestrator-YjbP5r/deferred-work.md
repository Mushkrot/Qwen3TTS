# Deferred Work Checks

These checks are intentionally deferred until the phase that creates their required files.

## Requires Phase 1

- `python tools/train_voice_candidates.py --help`
- `python -m unittest discover -s tests`
- `python -m compileall -q tools`

Phase 1 creates:

- `tools/train_voice_candidates.py`
- `tools/`
- `tests/test_train_voice_candidates.py`
- `tests/`

## Requires Phase 2

- `python -m compileall -q tools scripts`
- expanded `python -m unittest discover -s tests`

Phase 2 expands the orchestrator implementation and metrics behavior.

## Requires Phase 3

- eval-pack unit tests under `python -m unittest discover -s tests`
- `python -m compileall -q tools scripts`

Phase 3 adds eval generation to the orchestrator.

## Requires Phase 4

- `bash scripts/run_train_voice_candidates_smoke.sh`
- `bash -n scripts/run_train_voice_candidates_smoke.sh`

Phase 4 creates the smoke script and docs.

## External / Environment Work

Real non-stub orchestrator runs are not pre-flight checks. They require:

- a ready dataset manifest;
- local model/runtime availability;
- GPU or chosen device configuration;
- enough time for Qwen3-TTS preprocessing, SFT, and inference.

The smoke command remains the safe verification path for this Supergoal run.
