# Tooling

## Available

- Local shell with unrestricted filesystem access.
- Python standard library tests.
- Recallant CLI available and session started for this task:
  - `session_id=c7b6a541-9e76-4679-9728-eaa84d83e44b`
  - `project_id=f6ead963-0af2-4d00-bfda-01d5e124e4d8`
- Supergoal helper scripts:
  - `scripts/validate-phase.sh`
  - `scripts/repo-state.sh`

## Not Required

- Real GPU training is not required for planning or smoke.
- Real `faster-whisper` transcription is optional/env; hard reject smoke must remain deterministic.
- Real speaker embedding is optional/env.

