# Thinking: Qwen3TTS Stage 1 Checkpoint Selection Protocol

## Goal

Document the protocol that defines what this project should consider a "good checkpoint" during semi-automatic Qwen3-TTS voice training. The result must include eval phrases, metrics, rejection rules, stopping rules, and final report format so later implementation can choose 3-4 candidate voices instead of asking the user to inspect every epoch.

## Constraints

- This is Stage 1 only: documentation and protocol definition, not implementation of the training orchestrator.
- The protocol must preserve the current project mission: single-speaker Qwen3-TTS adaptation from Russian source recordings, with English generation quality as the product priority.
- Dataset purity is a precondition. No checkpoint score can compensate for music/noise/non-speech entering the training manifest.
- Raw audio, generated chunks, generated samples, and checkpoints remain uncommitted working artifacts per `docs/ARTIFACT_POLICY.md`.
- Upstream `sft_12hz.py` remains fixed-epoch only; any early stopping described here is project-level policy for a future orchestrator.

## Best Practices Applied

- Keep a fixed phrase set so candidate comparisons are reproducible.
- Separate hard rejection gates from soft ranking scores.
- Prefer earlier checkpoints when scores tie, because local project history and upstream issue reports show later epochs can improve some aspects while degrading naturalness or pace.
- Include automatic metrics only where they are defensible: ASR text match, duration/pace, clipping/RMS, silence/onset/offset, and speaker similarity if an embedding backend is present.
- Keep a human listening gate for the final 3-4 candidates because TTS naturalness and identity cannot be fully reduced to loss or ASR metrics.

## Top Risks

1. False confidence in automatic scoring.
   - Likelihood: high.
   - Mitigation: document automatic hard gates plus a human final choice; explicitly state that loss is supporting evidence only.

2. Protocol conflicts with existing `docs/EVAL_PHRASE_SET.md`.
   - Likelihood: medium.
   - Mitigation: extend the existing eval document and make the new protocol reference it instead of creating a competing phrase policy.

3. Later epochs sound worse despite better loss.
   - Likelihood: high for this project.
   - Mitigation: stopping rules must watch pace/naturalness regressions, cap max epochs, prefer earliest acceptable checkpoint, and cite upstream issue `QwenLM/Qwen3-TTS#179`.

## Dependencies

- Existing docs: `docs/EVAL_PHRASE_SET.md`, `docs/PROJECT_STATUS.md`, `docs/RUNBOOK.md`, `docs/ARCHITECTURE.md`, `docs/DATASET_CONTRACT.md`, `docs/VOICE_FILTERING_POLICY.md`, `docs/ARTIFACT_POLICY.md`.
- Existing command-level checks: `git diff --check`, `python -m compileall -q ...`, `bash -n ...`.
- Future implementation dependency: a training orchestrator will later consume this documented protocol.

## Key Assumptions

- The canonical new protocol file should be `docs/CHECKPOINT_SELECTION_PROTOCOL.md`.
- A small Markdown report template is acceptable under `docs/templates/CANDIDATE_REVIEW_REPORT.md`.
- The protocol should select up to 4 candidates, with conservative defaults: `min_epochs=2`, `max_epochs=6`, `patience=2`, and earliest-checkpoint tie break.
- English eval phrases remain primary; optional Russian sanity phrases may be included for identity/voice stability but must not override the English product objective.

## Open Questions Treated As Assumptions

- Whether speaker-similarity backend is already chosen. Assumption: protocol defines it as optional/pluggable for Stage 1 and does not require a new dependency.
- Whether final candidate report should be Markdown or JSON. Assumption: Markdown report for humans plus a future `metrics.jsonl` schema section for automation.
