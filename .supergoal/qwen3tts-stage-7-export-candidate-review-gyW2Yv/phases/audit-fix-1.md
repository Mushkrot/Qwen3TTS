AUDIT_FIX
Round: 1
Gap: Phase 2 roadmap deliverable asks for metrics event plus manifest metadata pointing to the review pack.
Scope:
- Append `candidate_review_export` to the run metrics when a review pack is exported.
- Keep copied review `metrics.jsonl` byte-identical to final run metrics.
- Add focused test/smoke coverage for the event.
Verification:
- `python -m unittest discover -s tests`
- `bash scripts/run_train_voice_candidates_smoke.sh`
- `python -m compileall -q tools scripts external/Qwen3-TTS/finetuning external/Qwen3-TTS/qwen_tts`
- `git diff --check`
