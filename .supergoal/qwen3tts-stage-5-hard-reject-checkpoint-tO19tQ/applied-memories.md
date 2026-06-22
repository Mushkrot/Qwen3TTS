# Applied Memories

- `/ai/Qwen3TTS dataset scaffold, built-in dataset builder, and Recallant working context` — keep the existing Qwen3TTS dataset/training workflow instead of inventing an unrelated pipeline.
- `datasets/voices/<Voice>/{Input,Ready}` convention — raw `Input/` audio is ignored local asset, not commit material.
- Recallant Qwen3TTS startup/context pattern — use Recallant checkpointing as continuity, with `PROJECT_LOG.md` as compact fallback.

