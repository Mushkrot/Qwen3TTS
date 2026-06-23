# Qwen3TTS datasets

This directory is the project-local dataset workspace.

Canonical voice layout:

```text
datasets/
  voices/
    <VoiceName>/
      Input/
      Ready/
```

- `Input/` contains raw source recordings for that voice.
- `Ready/` contains generated or prepared outputs for that voice: processed
  training chunks, manifests, reports, benchmark samples, and listening packs.
- Contents of `Input/` and `Ready/` are ignored local working assets and are not committed.
- Only scaffolds (`.gitkeep`) and small documentation/metadata files belong in Git.

For human browsing, start here. The `experiments/` tree is only a technical
scratch area for training runs/checkpoints and can be cleaned after important
audio is copied into the relevant `Ready/` folder.

Use this workspace only inside `/ai/Qwen3TTS`. The separate `/ai/whisper1`
project is an external transcription tool/source and is not the Qwen3TTS
dataset home.
