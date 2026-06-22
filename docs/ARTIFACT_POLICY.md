# Artifact and Data Policy

## Commit rule

Commit only files that are dangerous to lose and reasonable for Git:

- source code;
- documentation;
- small configuration files that contain no secrets;
- folder scaffolds such as `.gitkeep`;
- reproducible patch files;
- small manifest templates or tiny reproducible fixtures;
- intentional small selection metadata such as a sanitized
  `selected_checkpoint.json` or `experiment_status.json`.

Do not commit large or private working artifacts:

- raw source audio under `datasets/voices/**/Input/`;
- processed chunks under `datasets/voices/**/Ready/`;
- generated checkpoints under `experiments/**/runs/`;
- generated sample WAVs under `experiments/**/samples/`;
- generated candidate review packs under `experiments/**/samples/**/candidate_review/`;
- generated `metrics.jsonl`, copied review metrics, ranking files, and
  `candidate_manifest.json` files under experiment run/sample directories;
- generated `candidate_review/` audio and copied metrics remain artifacts even
  after a winner is selected; selection metadata may point to them but must not
  duplicate them;
- virtual environments;
- local model caches;
- secrets or environment files.

## Current ignored local assets

The current Baritone input files are local working inputs and are ignored:

```text
datasets/voices/Baritone/Input/Baritone1.mp3
datasets/voices/Baritone/Input/Baritone2.mp3
datasets/voices/Baritone/Input/Baritone3.mp3
```

They must remain available from the original source outside Git.

## Safe cleanup rule

Plain `git clean -fd` must not be used as a recovery habit in this repository.
It can remove untracked project-local state before `.gitignore` rules are reviewed.

Before cleanup, run:

```bash
git status --ignored --short
git clean -nd
git clean -ndX
```

Only remove files after confirming they are generated, backed up, or disposable.
