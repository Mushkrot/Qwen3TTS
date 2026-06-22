# Applied Memories

- Qwen3TTS dataset structure canonicalized — keep `datasets/voices/<Voice>/{Input,Ready}` as the local dataset convention, preserve raw `Input/` audio as ignored local assets, and do not treat `/ai/whisper1` as the Qwen3TTS dataset home.
- Recallant attach bootstrap — use Recallant as the durable memory/checkpoint layer and keep `PROJECT_LOG.md` as fallback via Recallant sync.
- Stage 2/3 checkpoint from Recallant — build Stage 4 on top of current `tools/train_voice_candidates.py`, tests, smoke script, and docs; do not rerun real GPU training during planning or smoke.
