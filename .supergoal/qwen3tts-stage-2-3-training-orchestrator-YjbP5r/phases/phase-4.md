SUPERGOAL_PHASE_START
Phase: 4 of 5 — Wire Smoke Docs
Task: Add a safe smoke command and document the real/stub orchestrator workflow.
Type: brownfield, Python, ML workflow
Mandatory commands: bash scripts/run_train_voice_candidates_smoke.sh; python -m unittest discover -s tests; git diff --check
Acceptance criteria: 5
Evidence required: smoke output summary, smoke tree listing, metrics rows, docs grep output
Depends on phases: 1, 2, 3

## Why

The workflow must be discoverable and safely verifiable without launching a real long GPU training job.

## Work

- Create `scripts/run_train_voice_candidates_smoke.sh`.
- The smoke should run the orchestrator in stub mode under `/tmp/qwen3tts_train_voice_candidates_smoke`.
- Update `scripts/README.md` with real and smoke commands.
- Update `docs/RUNBOOK.md` with orchestrator usage and heavy-training warning.
- Update `docs/CHECKPOINT_SELECTION_PROTOCOL.md` if needed to mark Stage 2/3 implementation status.

## Acceptance criteria (all must pass — verify each in transcript)

- `bash scripts/run_train_voice_candidates_smoke.sh` exits 0 and writes output under `/tmp/qwen3tts_train_voice_candidates_smoke`.
- The smoke output contains a prepared manifest, `metrics.jsonl`, an epoch-0 checkpoint sentinel, and five eval WAV/sentinel files under `eval/epoch-0/`.
- `scripts/README.md` documents the real orchestrator command and the smoke command.
- `docs/RUNBOOK.md` documents when to use the orchestrator and warns that real training is GPU-heavy.
- Docs state generated checkpoints/eval WAVs are ignored working artifacts and must not be committed.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m unittest discover -s tests`
- `git diff --check`

Command classes:

- `bash scripts/run_train_voice_candidates_smoke.sh`: requires-phase-4; run after this phase creates the smoke script.
- `python -m unittest discover -s tests`: requires-phase-1.
- `git diff --check`: baseline-safe.

## Evidence required in transcript

- Smoke command output summary.
- `/tmp/...` smoke tree listing.
- Metrics rows from smoke.
- Documentation grep output.

## Notes

- Smoke output must stay in `/tmp`, not under committed repo paths.
- The smoke may create sentinel `.wav` text files if documented as stub artifacts; real mode must call inference.
- These mandatory commands are phase-local checks, not pre-flight checks.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-2-3-training-orchestrator-YjbP5r/PROTOCOL.md without further
instruction needed here.
