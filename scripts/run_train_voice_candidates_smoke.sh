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
  --speaker_name speaker_target \
  --execution_mode stub

RUN_DIR="${RUN_ROOT}/SmokeVoice/smoke"
PREPARED="${RUN_DIR}/manifests/train_with_codes.jsonl"
METRICS="${RUN_DIR}/metrics.jsonl"
CHECKPOINT="${RUN_DIR}/train/epoch-0/checkpoint-epoch-0/STUB_CHECKPOINT.txt"
EVAL_DIR="${RUN_DIR}/eval/epoch-0"
EVAL_ROOT="${RUN_DIR}/eval"
CANDIDATE_MANIFEST="${RUN_DIR}/candidate_manifest.json"
CANDIDATE_REVIEW_DIR="${RUN_DIR}/candidate_review"
RANKING="${CANDIDATE_REVIEW_DIR}/ranking.md"
COPIED_METRICS="${CANDIDATE_REVIEW_DIR}/metrics.jsonl"

for required in \
  "${PREPARED}" \
  "${METRICS}" \
  "${CHECKPOINT}" \
  "${CANDIDATE_MANIFEST}" \
  "${RANKING}" \
  "${COPIED_METRICS}" \
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

if [[ ! -d "${CANDIDATE_REVIEW_DIR}" ]]; then
  echo "ERROR: missing candidate review directory: ${CANDIDATE_REVIEW_DIR}" >&2
  exit 1
fi

METRIC_SUMMARY="$("${PYTHON_BIN}" - "${METRICS}" "${CANDIDATE_MANIFEST}" "${CANDIDATE_REVIEW_DIR}" "${RANKING}" "${COPIED_METRICS}" <<'PY'
import json
import sys
from pathlib import Path

metrics_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
review_dir = Path(sys.argv[3])
ranking_path = Path(sys.argv[4])
copied_metrics_path = Path(sys.argv[5])
rows = [json.loads(line) for line in metrics_path.read_text(encoding="utf-8").splitlines() if line.strip()]
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
ranking_text = ranking_path.read_text(encoding="utf-8")
sample_rows = [row for row in rows if row.get("event") == "sample_metrics"]
score_rows = [row for row in rows if row.get("event") == "checkpoint_score"]
gate_rows = [row for row in rows if row.get("event") == "checkpoint_gate"]
decision_rows = [row for row in rows if row.get("event") == "early_stop_decision"]
run_stop_rows = [row for row in rows if row.get("event") == "run_stop"]
selection_rows = [row for row in rows if row.get("event") == "candidate_selection"]
review_export_rows = [row for row in rows if row.get("event") == "candidate_review_export"]
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
if not decision_rows:
    raise SystemExit("ERROR: missing early_stop_decision row")
if not run_stop_rows:
    raise SystemExit("ERROR: missing run_stop row")
if not selection_rows:
    raise SystemExit("ERROR: missing candidate_selection row")
if not review_export_rows:
    raise SystemExit("ERROR: missing candidate_review_export row")
if not isinstance(manifest.get("candidates"), list):
    raise SystemExit("ERROR: candidate_manifest.candidates is not a list")
if not isinstance(manifest.get("rejected_checkpoints"), list):
    raise SystemExit("ERROR: candidate_manifest.rejected_checkpoints is not a list")
if manifest.get("candidate_floor") != 3:
    raise SystemExit("ERROR: candidate_manifest.candidate_floor does not match default")
if not isinstance(manifest.get("limited_reasons"), list):
    raise SystemExit("ERROR: candidate_manifest.limited_reasons is not a list")
if not isinstance(manifest.get("stop_summary"), dict):
    raise SystemExit("ERROR: candidate_manifest.stop_summary is not an object")
if not isinstance(manifest.get("candidate_review"), dict):
    raise SystemExit("ERROR: candidate_manifest.candidate_review is not an object")

for row in sample_rows:
    for key in required_numeric:
        if not isinstance(row.get(key), (int, float)):
            raise SystemExit(f"ERROR: sample_metrics.{key} is not numeric for {row.get('label')}")

run_stop = run_stop_rows[-1]
epochs_completed = run_stop.get("epochs_completed")
if not isinstance(epochs_completed, int):
    raise SystemExit("ERROR: run_stop.epochs_completed is not an integer")
if not 1 < epochs_completed < 6:
    raise SystemExit(f"ERROR: expected smoke to complete 2-5 epochs, got {epochs_completed}")
if len(decision_rows) != epochs_completed:
    raise SystemExit("ERROR: early_stop_decision count does not match completed epochs")
if len(score_rows) != epochs_completed:
    raise SystemExit("ERROR: checkpoint_score count does not match completed epochs")
if len(gate_rows) != epochs_completed:
    raise SystemExit("ERROR: checkpoint_gate count does not match completed epochs")
if len(sample_rows) < epochs_completed * 5:
    raise SystemExit("ERROR: not enough sample_metrics rows for completed epochs")
if manifest["stop_summary"].get("reason") != run_stop.get("reason"):
    raise SystemExit("ERROR: manifest stop reason does not match run_stop")
if manifest["stop_summary"].get("epochs_completed") != epochs_completed:
    raise SystemExit("ERROR: manifest epochs_completed does not match run_stop")
for key in ("reason", "best_epoch", "best_score", "epochs_completed"):
    if key not in manifest["stop_summary"]:
        raise SystemExit(f"ERROR: stop_summary missing {key}")

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
review_export = review_export_rows[-1]
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
if not 1 < manifest_candidate_count <= manifest.get("top_candidates", 0):
    raise SystemExit(
        "ERROR: expected smoke to export 2..top_candidates candidates, got "
        f"{manifest_candidate_count}"
    )

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

review = manifest["candidate_review"]
if Path(str(review.get("review_dir"))) != review_dir:
    raise SystemExit("ERROR: candidate_review.review_dir does not match smoke path")
if Path(str(review.get("ranking_path"))) != ranking_path:
    raise SystemExit("ERROR: candidate_review.ranking_path does not match smoke path")
if Path(str(review.get("metrics_path"))) != copied_metrics_path:
    raise SystemExit("ERROR: candidate_review.metrics_path does not match smoke path")
if review.get("candidate_count") != manifest_candidate_count:
    raise SystemExit("ERROR: candidate_review candidate count does not match manifest")
if review_export.get("candidate_count") != manifest_candidate_count:
    raise SystemExit("ERROR: candidate_review_export candidate count does not match manifest")
if review.get("exported_epochs") != [row["epoch"] for row in manifest["candidates"]]:
    raise SystemExit("ERROR: candidate_review exported_epochs does not match selected candidates")
if review_export.get("exported_epochs") != review.get("exported_epochs"):
    raise SystemExit("ERROR: candidate_review_export epochs do not match manifest review metadata")
if not copied_metrics_path.exists():
    raise SystemExit("ERROR: copied candidate review metrics.jsonl is missing")
if copied_metrics_path.read_bytes() != metrics_path.read_bytes():
    raise SystemExit("ERROR: copied candidate review metrics.jsonl differs from run metrics")
if not ranking_path.exists():
    raise SystemExit("ERROR: candidate review ranking.md is missing")

fixed_eval_names = [
    "01_en_short.wav",
    "02_en_long.wav",
    "03_en_calm.wav",
    "04_ru_short.wav",
    "05_ru_long.wav",
]
rank_names = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
for candidate in manifest["candidates"]:
    rank = candidate.get("rank")
    epoch = candidate.get("epoch")
    if not isinstance(rank, int) or rank < 1:
        raise SystemExit("ERROR: candidate rank is invalid")
    if not isinstance(epoch, int):
        raise SystemExit("ERROR: candidate epoch is invalid")
    expected_label = f"candidate_{rank_names[rank - 1]}_epoch{epoch}"
    if candidate.get("label") != expected_label:
        raise SystemExit(f"ERROR: candidate label mismatch: {candidate.get('label')} != {expected_label}")
    candidate_dir = review_dir / expected_label
    if not candidate_dir.is_dir():
        raise SystemExit(f"ERROR: missing candidate review folder: {candidate_dir}")
    copied_names = sorted(path.name for path in candidate_dir.iterdir() if path.is_file())
    if copied_names != fixed_eval_names:
        raise SystemExit(f"ERROR: candidate review files mismatch for {candidate_dir}: {copied_names}")
    for filename in fixed_eval_names:
        if filename not in ranking_text:
            raise SystemExit(f"ERROR: ranking.md does not mention {filename}")
if "Checkpoint:" not in ranking_text:
    raise SystemExit("ERROR: ranking.md does not include checkpoint path text")
if "Why selected" not in ranking_text:
    raise SystemExit("ERROR: ranking.md does not include selected reason text")
if "Risks/warnings" not in ranking_text:
    raise SystemExit("ERROR: ranking.md does not include risk text")

def emit(message):
    sys.stdout.write(f"{message}\n")


emit(f"Sample metric rows: {len(sample_rows)}")
emit(f"Checkpoint score rows: {len(score_rows)}")
emit(f"Checkpoint score: {float(score['score']):.3f}")
emit("Checkpoint warnings: " + ",".join(str(item) for item in score["warnings"]))
emit(f"Checkpoint gate rows: {len(gate_rows)}")
emit(f"Last gate hard rejected: {gate['hard_rejected']}")
emit("Last gate reject reasons: " + ",".join(str(item) for item in gate["reject_reasons"]))
emit(f"Early stop decision rows: {len(decision_rows)}")
emit(f"Run stop reason: {run_stop['reason']}")
emit(f"Epochs completed: {epochs_completed}")
emit(f"Candidate selection rows: {len(selection_rows)}")
emit(f"Candidate review export rows: {len(review_export_rows)}")
emit(f"Selected candidates: {manifest_candidate_count}")
emit(f"Rejected checkpoints: {manifest_rejected_count}")
emit(f"Candidate review directory: {review_dir}")
emit(f"Exported candidate count: {review['candidate_count']}")
emit(f"Ranking path: {ranking_path}")
emit(f"Copied metrics path: {copied_metrics_path}")
PY
)"

echo "Smoke output: ${RUN_DIR}"
echo "Prepared manifest: ${PREPARED}"
echo "Metrics: ${METRICS}"
echo "Checkpoint sentinel: ${CHECKPOINT}"
echo "Candidate manifest: ${CANDIDATE_MANIFEST}"
echo "Candidate review directory: ${CANDIDATE_REVIEW_DIR}"
echo "Ranking path: ${RANKING}"
echo "Copied metrics path: ${COPIED_METRICS}"
printf '%s\n' "${METRIC_SUMMARY}"
echo "Eval files:"
find "${EVAL_ROOT}" -maxdepth 2 -type f | sort
echo "Candidate review tree:"
find "${CANDIDATE_REVIEW_DIR}" -maxdepth 2 -type f | sort
echo "Ranking excerpt:"
sed -n '1,80p' "${RANKING}"
