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
- `Ready/` contains dataset-builder outputs for that voice.

Use this workspace only inside `/ai/Qwen3TTS`. The separate `/ai/whisper1`
project is an external transcription tool/source and is not the Qwen3TTS
dataset home.

