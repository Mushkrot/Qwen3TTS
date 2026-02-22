#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

TRAIN_JSONL="${1:-${ROOT_DIR}/experiments/qwen3_ru_en_speaker_v1/manifests/train_with_codes.jsonl}"
OUTPUT_DIR="${2:-${ROOT_DIR}/experiments/qwen3_ru_en_speaker_v1/runs/sft_0_6b_run1}"
SPEAKER_NAME="${SPEAKER_NAME:-speaker_target}"
INIT_MODEL_PATH="${INIT_MODEL_PATH:-Qwen/Qwen3-TTS-12Hz-0.6B-Base}"
BATCH_SIZE="${BATCH_SIZE:-2}"
LR="${LR:-2e-5}"
NUM_EPOCHS="${NUM_EPOCHS:-3}"

source "${ROOT_DIR}/.venv/bin/activate"

python "${ROOT_DIR}/external/Qwen3-TTS/finetuning/sft_12hz.py" \
  --init_model_path "${INIT_MODEL_PATH}" \
  --output_model_path "${OUTPUT_DIR}" \
  --train_jsonl "${TRAIN_JSONL}" \
  --batch_size "${BATCH_SIZE}" \
  --lr "${LR}" \
  --num_epochs "${NUM_EPOCHS}" \
  --speaker_name "${SPEAKER_NAME}"

echo "SFT completed: ${OUTPUT_DIR}"
