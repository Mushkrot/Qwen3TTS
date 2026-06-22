# Applied Memories

- Qwen3TTS dataset structure canonicalized — preserve `datasets/voices/<Voice>/{Input,Ready}` and keep raw `Input/` media out of commit scope.
- Stage 6 semi-auto early stopping plan — Stage 7 should build on `candidate_manifest.json`, `run_stop`, and non-rejected top candidates rather than inventing a separate selection path.
