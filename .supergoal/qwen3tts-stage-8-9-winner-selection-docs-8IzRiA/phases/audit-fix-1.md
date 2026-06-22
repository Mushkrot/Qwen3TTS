# Audit Fix 1 - Prove bare candidate command auto-discovery

## Gap

Final audit found that the user-facing bare command shape
`python tools/select_voice_candidate.py --candidate B` was supported by code but
only indirectly verified. Existing tests covered explicit review-dir selection
and ambiguous discovery rejection; smoke used the explicit path equivalent.

## Fix

- Add a unit test that creates exactly one review pack under a temporary
  experiment root.
- Run `tools/select_voice_candidate.py --candidate B` as a subprocess with
  `cwd` set to that temporary root and no `--candidate_review_dir`.
- Assert that selected metadata is written and candidate B is selected.

## Success Gate

- `python -m unittest discover -s tests`
- `bash scripts/run_select_voice_candidate_smoke.sh`
- `python -m compileall -q tools scripts`
- `git diff --check`
