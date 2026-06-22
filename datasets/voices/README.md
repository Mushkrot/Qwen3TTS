# Voice folders

Each voice has its own folder with the same two-subfolder structure:

```text
<VoiceName>/
  Input/
  Ready/
```

Put new raw recordings in `Input/`. Write generated chunks, transcripts,
reports, manifests, and quarantine output under `Ready/`.

Do not commit raw `Input/` audio or generated `Ready/` outputs. Commit only the
voice folder scaffold and small docs/metadata that are dangerous to lose.
