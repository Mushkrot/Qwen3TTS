# Thinking: Stage 8/9 Winner Selection

## Goals

- Let the owner choose one exported candidate as the active voice candidate.
- Persist a small durable pointer to the chosen checkpoint without copying heavy data.
- Update the local experiment status so later inference/training steps know which checkpoint is primary.
- Document a single end-to-end procedure from semi-auto training to candidate listening to winner selection.

## Constraints

- Current Stage 7 changes are in the working tree and are required context for this plan.
- Raw `Input/` audio, generated WAVs, copied review metrics, checkpoints, and run directories remain non-commit artifacts.
- `selected_checkpoint.json` is small metadata and should be intentionally placed where the system can discover it.
- The final winner remains human-selected. The project must not claim automatic final voice choice.

## Proposed contract

`python tools/select_voice_candidate.py --candidate B` should work when the candidate review pack is discoverable from the current directory or uniquely discoverable from known experiment paths.

For safety, the script should also accept:

- `--candidate_review_dir PATH` for explicit selection from a review pack;
- `--experiment_root PATH` only when auto-derivation is ambiguous;
- `--dry_run` to print the planned writes without changing files.

If more than one review pack is discoverable, the command must fail with a clear message asking for `--candidate_review_dir`.

## Selection artifacts

The script should write small metadata only:

- `selected_checkpoint.json` as the primary pointer;
- `experiment_status.json` or equivalent local status metadata;
- a `selected_checkpoint` or `winner_selection` block in `candidate_manifest.json`;
- optionally a copy of `selected_checkpoint.json` in `candidate_review/` for owner-facing review.

It must not copy checkpoint directories, WAV files, metrics blobs, or raw audio.

## Top risks

1. Wrong review pack selected by auto-discovery.
   Mitigation: deterministic discovery order, ambiguity failure, explicit `--candidate_review_dir`.
2. Selected candidate is not actually in `candidate_manifest.json.candidates`.
   Mitigation: validate label/rank against manifest candidates, reject missing/rejected candidates.
3. Status metadata lands only inside ignored run folders and is easy to lose.
   Mitigation: derive experiment root when possible and write a small root-level `selected_checkpoint.json`.

## Dependencies

- Stage 7 review export must exist: `candidate_manifest.json.candidate_review`, `candidate_A_epochN` folders, `ranking.md`, and copied metrics.
- Smoke should run no-GPU and select candidate B from the Stage 7 smoke output.

## Future improvement lane

MVP remains epoch-by-epoch training, eval audio generation, simple metrics, hard rejects, top-4 export, and human winner selection.

Future improvements are explicitly deferred:

- real speaker similarity backend;
- smarter scoring/naturalness model;
- HTML report or richer Markdown report;
- automatic recommended candidate.
