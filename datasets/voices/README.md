# Voice folders

Each voice has its own folder with the same two-subfolder structure:

```text
<VoiceName>/
  Input/
  Ready/
```

Put new raw recordings in `Input/`. Write generated chunks, transcripts,
reports, manifests, benchmark samples, and listening outputs under `Ready/`.

Recommended `Ready/` shape for generated audio:

```text
<VoiceName>/
  Ready/
    <purpose-or-project>/
      en/
      ru/
      manifest.jsonl
      run_config.json
      summary.json
```

Examples from the 2026-06-23 long-form tests:

```text
Aiden/Ready/builtin_quality_2026-06-23/
Ryan/Ready/builtin_quality_2026-06-23/
Baritone/Ready/prosody_control_2026-06-23/
```

Do not commit raw `Input/` audio or generated `Ready/` outputs. Commit only the
voice folder scaffold and small docs/metadata that are dangerous to lose.
