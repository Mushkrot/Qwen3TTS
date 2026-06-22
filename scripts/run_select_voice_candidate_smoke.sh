#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${QWEN3TTS_PYTHON:-python}"
TRAIN_SMOKE_ROOT="${QWEN3TTS_SELECT_TRAIN_SMOKE_ROOT:-/tmp/qwen3tts_train_voice_candidates_smoke_select_voice_candidate}"
SMOKE_ROOT="${QWEN3TTS_SELECT_SMOKE_ROOT:-/tmp/qwen3tts_select_voice_candidate_smoke}"

if [[ "${SMOKE_ROOT}" != /tmp/qwen3tts_select_voice_candidate_smoke* ]]; then
  echo "ERROR: refusing to clean non-smoke path: ${SMOKE_ROOT}" >&2
  exit 2
fi

rm -rf "${SMOKE_ROOT}"
mkdir -p "${SMOKE_ROOT}"

QWEN3TTS_TRAIN_SMOKE_ROOT="${TRAIN_SMOKE_ROOT}" \
  "${ROOT_DIR}/scripts/run_train_voice_candidates_smoke.sh" > "${SMOKE_ROOT}/train_smoke.log"

RUN_DIR="${TRAIN_SMOKE_ROOT}/output/SmokeVoice/smoke"
CANDIDATE_REVIEW_DIR="${RUN_DIR}/candidate_review"
CANDIDATE_MANIFEST="${RUN_DIR}/candidate_manifest.json"
SELECTED_CHECKPOINT_JSON="${RUN_DIR}/selected_checkpoint.json"
EXPERIMENT_STATUS="${RUN_DIR}/experiment_status.json"
HEAVY_FILES_BEFORE="${SMOKE_ROOT}/heavy-files-before.txt"
HEAVY_FILES_AFTER="${SMOKE_ROOT}/heavy-files-after.txt"
CHECKPOINT_DIRS_BEFORE="${SMOKE_ROOT}/checkpoint-dirs-before.txt"
CHECKPOINT_DIRS_AFTER="${SMOKE_ROOT}/checkpoint-dirs-after.txt"

for required in \
  "${CANDIDATE_REVIEW_DIR}" \
  "${CANDIDATE_MANIFEST}" \
  "${CANDIDATE_REVIEW_DIR}/ranking.md" \
  "${CANDIDATE_REVIEW_DIR}/metrics.jsonl"; do
  if [[ ! -e "${required}" ]]; then
    echo "ERROR: missing prerequisite smoke artifact: ${required}" >&2
    exit 1
  fi
done

find "${RUN_DIR}" -type f \( -name '*.wav' -o -name 'metrics.jsonl' \) | sort > "${HEAVY_FILES_BEFORE}"
find "${RUN_DIR}" -type d -name 'checkpoint-*' | sort > "${CHECKPOINT_DIRS_BEFORE}"

"${PYTHON_BIN}" "${ROOT_DIR}/tools/select_voice_candidate.py" \
  --candidate B \
  --candidate_review_dir "${CANDIDATE_REVIEW_DIR}" \
  > "${SMOKE_ROOT}/select_stdout.log"

find "${RUN_DIR}" -type f \( -name '*.wav' -o -name 'metrics.jsonl' \) | sort > "${HEAVY_FILES_AFTER}"
find "${RUN_DIR}" -type d -name 'checkpoint-*' | sort > "${CHECKPOINT_DIRS_AFTER}"

if ! cmp -s "${HEAVY_FILES_BEFORE}" "${HEAVY_FILES_AFTER}"; then
  echo "ERROR: selection changed heavy file set" >&2
  diff -u "${HEAVY_FILES_BEFORE}" "${HEAVY_FILES_AFTER}" >&2 || true
  exit 1
fi

if ! cmp -s "${CHECKPOINT_DIRS_BEFORE}" "${CHECKPOINT_DIRS_AFTER}"; then
  echo "ERROR: selection changed checkpoint directory set" >&2
  diff -u "${CHECKPOINT_DIRS_BEFORE}" "${CHECKPOINT_DIRS_AFTER}" >&2 || true
  exit 1
fi

SELECTION_SUMMARY="$("${PYTHON_BIN}" - "${CANDIDATE_MANIFEST}" "${SELECTED_CHECKPOINT_JSON}" "${EXPERIMENT_STATUS}" <<'PY'
import json
import sys
from pathlib import Path

manifest_path = Path(sys.argv[1])
selected_path = Path(sys.argv[2])
status_path = Path(sys.argv[3])
manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
selected = json.loads(selected_path.read_text(encoding="utf-8"))
status = json.loads(status_path.read_text(encoding="utf-8"))
candidates = manifest.get("candidates")
if not isinstance(candidates, list) or len(candidates) < 2:
    raise SystemExit("ERROR: expected at least candidates A and B")
candidate_by_label = {
    str(candidate.get("label")): candidate
    for candidate in candidates
    if isinstance(candidate, dict)
}
candidate_a = candidate_by_label.get("candidate_A_epoch0")
candidate_b = candidate_by_label.get("candidate_B_epoch1")
if candidate_a is None or candidate_b is None:
    raise SystemExit("ERROR: expected candidate_A_epoch0 and candidate_B_epoch1 in manifest")
selected_checkpoint = selected.get("checkpoint_path")
if selected.get("candidate_label") != "candidate_B_epoch1":
    raise SystemExit("ERROR: selected checkpoint metadata does not point to candidate B")
if selected_checkpoint != candidate_b.get("checkpoint_path"):
    raise SystemExit("ERROR: selected checkpoint does not match candidate B checkpoint")
if selected_checkpoint == candidate_a.get("checkpoint_path"):
    raise SystemExit("ERROR: selected checkpoint unexpectedly matches candidate A")
if status.get("active_checkpoint") != selected_checkpoint:
    raise SystemExit("ERROR: experiment status active_checkpoint mismatch")
if status.get("primary_checkpoint") != selected_checkpoint:
    raise SystemExit("ERROR: experiment status primary_checkpoint mismatch")
winner = manifest.get("winner_selection")
if not isinstance(winner, dict):
    raise SystemExit("ERROR: manifest winner_selection missing")
if winner.get("candidate_label") != "candidate_B_epoch1":
    raise SystemExit("ERROR: manifest winner_selection does not point to candidate B")
for forbidden in ("copied_checkpoint_path", "copied_audio_path", "copied_metrics_path"):
    if forbidden in selected or forbidden in status or forbidden in winner:
        raise SystemExit(f"ERROR: unexpected copied artifact key: {forbidden}")

def emit(message):
    sys.stdout.write(f"{message}\n")

emit(f"Selected candidate: {selected['candidate_label']}")
emit(f"Selected rank: {selected['candidate_rank']}")
emit(f"Selected epoch: {selected['candidate_epoch']}")
emit(f"Selected checkpoint: {selected_checkpoint}")
emit(f"Selected metadata path: {selected_path}")
emit(f"Active status path: {status_path}")
emit(f"Manifest winner candidate: {winner['candidate_label']}")
emit(f"Manifest path: {manifest_path}")
PY
)"

echo "Selection smoke output: ${SMOKE_ROOT}"
echo "Training smoke output: ${RUN_DIR}"
echo "Candidate review directory: ${CANDIDATE_REVIEW_DIR}"
echo "Selection stdout:"
sed -n '1,40p' "${SMOKE_ROOT}/select_stdout.log"
printf '%s\n' "${SELECTION_SUMMARY}"
echo "No heavy files copied by selection: yes"
echo "No checkpoint directories copied by selection: yes"
