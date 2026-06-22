# Thinking: Stage 7 Candidate Review Export

## Goals

- Export only selected non-rejected checkpoints after semi-auto stopping.
- Give the owner a small listening pack: 3-4 candidate folders, a copied `metrics.jsonl`, and a readable `ranking.md`.
- Keep the final winner human-selected; this stage prepares review material only.

## Constraints

- Build on Stage 6 `candidate_manifest.json`, `run_stop`, `checkpoint_gate`, and eval-pack rows.
- Do not commit generated review WAVs, metrics copies, checkpoints, or raw `Input/` audio.
- Keep implementation project-local in `tools/train_voice_candidates.py`.
- Keep pre-flight mandatory commands baseline-safe; do not require files/options before the phase that creates them.
- Standard-library only at import time; no heavy runtime imports from the orchestrator module.

## Risks

1. Exporting rejected checkpoints by accident.
   - Mitigation: export only from manifest `candidates`, test rejected high-score history, and assert review folders do not overlap rejected epochs.
2. Review pack path ambiguity.
   - Mitigation: add optional `--candidate_review_root`; default to a deterministic sibling `samples/<voice>/<run_name>/candidate_review` for normal `runs` output and record the resolved path in manifest/export event.
3. Ranking report is technically present but not useful to a listener.
   - Mitigation: require checkpoint path, score, why selected, risks/warnings, copied audio paths, stop summary, and review instructions in `ranking.md`.

## Dependencies

- Stage 6 must remain intact: selection, rejected filtering, stop summary, and smoke early stop.
- Export should run after `append_candidate_selection`, because the manifest is the source of truth.
- Smoke must stay no-GPU and use temp paths only.

## Open Questions Assumed

- Default review path will be deterministic and overridable rather than asking the user for a path now.
- Candidate folder letters map rank 1..4 to `candidate_A`, `candidate_B`, `candidate_C`, `candidate_D`.
- Copied eval WAV export is now in scope; selected-checkpoint persistence remains out of scope.

## Memory Hits Applied

- Qwen3TTS dataset structure is `datasets/voices/<Voice>/{Input,Ready}` and raw `Input/` media is not a commit target.
- Stage 6 already established semi-auto stopping and candidate manifest semantics.

## Tools Relied On

- Supergoal scripts for run namespace and phase validation.
- Recallant context pack for project memory.
- Local repo tests and smoke scripts for verification.

## Best Practices Applied

- Treat generated audio and metrics as ignored run artifacts.
- Verify exported material with smoke artifacts, not real GPU training.
- Keep ranking markdown deterministic so tests can assert useful text without brittle formatting.
