#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${QWEN3TTS_PYTHON:-python}"
SMOKE_ROOT="${QWEN3TTS_TRAIN_SMOKE_ROOT:-/tmp/qwen3tts_train_voice_candidates_smoke}"
INPUT_DIR="${SMOKE_ROOT}/input"
RUN_ROOT="${SMOKE_ROOT}/output"
MANIFEST="${INPUT_DIR}/train_raw.jsonl"

if [[ "${SMOKE_ROOT}" != /tmp/qwen3tts_train_voice_candidates_smoke* ]]; then
  echo "ERROR: refusing to clean non-smoke path: ${SMOKE_ROOT}" >&2
  exit 2
fi

rm -rf "${SMOKE_ROOT}"
mkdir -p "${INPUT_DIR}"

printf '%s\n' \
  '{"audio":"stub_audio.wav","text":"A calm training smoke line.","ref_audio":"stub_audio.wav"}' \
  > "${MANIFEST}"

"${PYTHON_BIN}" "${ROOT_DIR}/tools/train_voice_candidates.py" \
  --voice_name SmokeVoice \
  --train_raw_jsonl "${MANIFEST}" \
  --output_root "${RUN_ROOT}" \
  --run_name smoke \
  --max_epochs 1 \
  --speaker_name speaker_target \
  --execution_mode stub

RUN_DIR="${RUN_ROOT}/SmokeVoice/smoke"
PREPARED="${RUN_DIR}/manifests/train_with_codes.jsonl"
METRICS="${RUN_DIR}/metrics.jsonl"
CHECKPOINT="${RUN_DIR}/train/epoch-0/checkpoint-epoch-0/STUB_CHECKPOINT.txt"
EVAL_DIR="${RUN_DIR}/eval/epoch-0"
CANDIDATE_MANIFEST="${RUN_DIR}/candidate_manifest.json"

for required in \
  "${PREPARED}" \
  "${METRICS}" \
  "${CHECKPOINT}" \
  "${CANDIDATE_MANIFEST}" \
  "${EVAL_DIR}/01_en_short.wav" \
  "${EVAL_DIR}/02_en_long.wav" \
  "${EVAL_DIR}/03_en_calm.wav" \
  "${EVAL_DIR}/04_ru_short.wav" \
  "${EVAL_DIR}/05_ru_long.wav"; do
  if [[ ! -f "${required}" ]]; then
    echo "ERROR: missing smoke artifact: ${required}" >&2
    exit 1
  fi
done

METRIC_SUMMARY="$("${PYTHON_BIN}" - "${METRICS}" "${CANDIDATE_MANIFEST}" <<'PY'
import json
import sys
from pathlib import Path

metrics_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
rows = [json.loads(line) for line in metrics_path.read_text(encoding="utf-8").splitlines() if line.strip()]
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
sample_rows = [row for row in rows if row.get("event") == "sample_metrics"]
score_rows = [row for row in rows if row.get("event") == "checkpoint_score"]
gate_rows = [row for row in rows if row.get("event") == "checkpoint_gate"]
selection_rows = [row for row in rows if row.get("event") == "candidate_selection"]
required_numeric = (
    "duration_seconds",
    "expected_duration_seconds",
    "duration_ratio",
    "pace_chars_per_sec",
    "pace_words_per_sec",
    "rms_dbfs",
    "clipping_ratio",
    "leading_silence_ms",
    "trailing_silence_ms",
)

if len(sample_rows) < 5:
    raise SystemExit(f"ERROR: expected at least 5 sample_metrics rows, found {len(sample_rows)}")
if not score_rows:
    raise SystemExit("ERROR: missing checkpoint_score row")
if not gate_rows:
    raise SystemExit("ERROR: missing checkpoint_gate row")
if not selection_rows:
    raise SystemExit("ERROR: missing candidate_selection row")
if not isinstance(manifest.get("candidates"), list):
    raise SystemExit("ERROR: candidate_manifest.candidates is not a list")
if not isinstance(manifest.get("rejected_checkpoints"), list):
    raise SystemExit("ERROR: candidate_manifest.rejected_checkpoints is not a list")

for row in sample_rows:
    for key in required_numeric:
        if not isinstance(row.get(key), (int, float)):
            raise SystemExit(f"ERROR: sample_metrics.{key} is not numeric for {row.get('label')}")

score = score_rows[-1]
if not isinstance(score.get("score"), (int, float)):
    raise SystemExit("ERROR: checkpoint_score.score is not numeric")
if not isinstance(score.get("warnings"), list):
    raise SystemExit("ERROR: checkpoint_score.warnings is not a list")
if not isinstance(score.get("metric_summary"), dict):
    raise SystemExit("ERROR: checkpoint_score.metric_summary is not an object")

gate = gate_rows[-1]
if not isinstance(gate.get("hard_rejected"), bool):
    raise SystemExit("ERROR: checkpoint_gate.hard_rejected is not boolean")
if not isinstance(gate.get("reject_reasons"), list):
    raise SystemExit("ERROR: checkpoint_gate.reject_reasons is not a list")
if not isinstance(gate.get("warning_reasons"), list):
    raise SystemExit("ERROR: checkpoint_gate.warning_reasons is not a list")

selection = selection_rows[-1]
manifest_candidate_count = manifest.get("candidate_count")
manifest_rejected_count = manifest.get("rejected_count")
if manifest_candidate_count != len(manifest["candidates"]):
    raise SystemExit("ERROR: candidate_manifest.candidate_count does not match candidates")
if manifest_rejected_count != len(manifest["rejected_checkpoints"]):
    raise SystemExit("ERROR: candidate_manifest.rejected_count does not match rejected_checkpoints")
if selection.get("candidate_count") != manifest_candidate_count:
    raise SystemExit("ERROR: candidate_selection.candidate_count does not match manifest")
if selection.get("rejected_count") != manifest_rejected_count:
    raise SystemExit("ERROR: candidate_selection.rejected_count does not match manifest")

rejected_epochs = {
    row["epoch"]
    for row in gate_rows
    if row.get("hard_rejected") is True and isinstance(row.get("epoch"), int)
}
candidate_epochs = {
    row["epoch"]
    for row in manifest["candidates"]
    if isinstance(row.get("epoch"), int)
}
if rejected_epochs & candidate_epochs:
    raise SystemExit(
        "ERROR: rejected checkpoint epoch appeared in candidates: "
        + ",".join(str(epoch) for epoch in sorted(rejected_epochs & candidate_epochs))
    )

print(f"Sample metric rows: {len(sample_rows)}")
print(f"Checkpoint score rows: {len(score_rows)}")
print(f"Checkpoint score: {float(score['score']):.3f}")
print("Checkpoint warnings: " + ",".join(str(item) for item in score["warnings"]))
print(f"Checkpoint gate rows: {len(gate_rows)}")
print(f"Last gate hard rejected: {gate['hard_rejected']}")
print("Last gate reject reasons: " + ",".join(str(item) for item in gate["reject_reasons"]))
print(f"Candidate selection rows: {len(selection_rows)}")
print(f"Selected candidates: {manifest_candidate_count}")
print(f"Rejected checkpoints: {manifest_rejected_count}")
PY
)"

echo "Smoke output: ${RUN_DIR}"
echo "Prepared manifest: ${PREPARED}"
echo "Metrics: ${METRICS}"
echo "Checkpoint sentinel: ${CHECKPOINT}"
echo "Candidate manifest: ${CANDIDATE_MANIFEST}"
printf '%s\n' "${METRIC_SUMMARY}"
echo "Eval files:"
find "${EVAL_DIR}" -maxdepth 1 -type f | sort
