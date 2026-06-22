SUPERGOAL_PHASE_START
Phase: 1 of 4 — Draft Protocol
Task: Create the canonical checkpoint selection protocol document for Qwen3TTS semi-automatic candidate review.
Type: brownfield, documentation, ML workflow
Mandatory commands: git diff --check
Acceptance criteria: 7
Evidence required: document path, section headings, stopping defaults, hard reject list, command exit code
Depends on phases: none

## Why

The project needs one documented source of truth for deciding which checkpoints become the 3-4 voice candidates a human will review.

## Work

- Create `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- Define the protocol scope and explicitly separate this documentation stage from later orchestration implementation.
- Reuse the existing fixed English phrase policy from `docs/EVAL_PHRASE_SET.md`; add optional Russian sanity phrases only if clearly marked as secondary.
- Define automatic metrics with clear directionality and limitations.
- Define hard reject gates separately from soft ranking.
- Define early stopping defaults and top-candidate export rules.
- Define the final report fields and future artifact layout.
- Reference `docs/DATASET_CONTRACT.md`, `docs/VOICE_FILTERING_POLICY.md`, and `docs/ARTIFACT_POLICY.md` where relevant.

## Acceptance criteria (all must pass — verify each in transcript)

- `docs/CHECKPOINT_SELECTION_PROTOCOL.md` exists.
- The protocol document defines scope and explicitly says Stage 1 is documentation, not an orchestrator implementation.
- The protocol lists the fixed eval phrase set or points to the exact canonical phrase source.
- The protocol defines automatic metrics, including ASR/text match, duration/pace, clipping/RMS, leading/trailing silence, onset/offset, training loss trend, and optional speaker similarity.
- The protocol separates hard reject gates from soft ranking scores.
- The protocol defines stopping defaults: minimum epochs, maximum epochs, patience, degradation stop, tie-break behavior, and number of final candidates.
- The protocol defines the candidate export shape and final report fields, and states that dataset purity is a pre-training gate.

## Mandatory commands (run each, surface last ~10 lines + exit code)

- `git diff --check`

## Evidence required in transcript

- Print the new document path.
- Print the section headings from the new document.
- Print the stopping defaults and hard reject list.
- Print `git diff --check` exit code.

## Notes

- Do not implement training orchestration code in this phase.
- Do not create generated audio/checkpoint artifacts.
- Mention upstream pace-regression risk from `QwenLM/Qwen3-TTS#179` without over-quoting.

---

The agent will, during execution, print SUPERGOAL_PHASE_START (above),
do the work, then print SUPERGOAL_PHASE_VERIFY, MEMORY_SAVED, and
SUPERGOAL_PHASE_DONE in order. On failure, the agent follows the
3-strike recovery protocol in .supergoal/qwen3tts-stage-1-checkpoint-selection-pr-KHbXIj/PROTOCOL.md without further
instruction needed here.
