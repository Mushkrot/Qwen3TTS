#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

INPUT_JSONL="${1:-${ROOT_DIR}/experiments/qwen3_ru_en_speaker_v1/manifests/train_raw.jsonl}"
OUTPUT_JSONL="${2:-${ROOT_DIR}/experiments/qwen3_ru_en_speaker_v1/manifests/train_with_codes.jsonl}"
DEVICE="${DEVICE:-cuda:0}"
TOKENIZER_MODEL_PATH="${TOKENIZER_MODEL_PATH:-Qwen/Qwen3-TTS-Tokenizer-12Hz}"

if [ ! -f "${ROOT_DIR}/.venv/bin/activate" ]; then
  echo "ERROR: missing virtualenv: ${ROOT_DIR}/.venv"
  echo "Create it with: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source "${ROOT_DIR}/.venv/bin/activate"
python "${ROOT_DIR}/scripts/validate_manifest.py" --input_jsonl "${INPUT_JSONL}"

python "${ROOT_DIR}/external/Qwen3-TTS/finetuning/prepare_data.py" \
  --device "${DEVICE}" \
  --tokenizer_model_path "${TOKENIZER_MODEL_PATH}" \
  --input_jsonl "${INPUT_JSONL}" \
  --output_jsonl "${OUTPUT_JSONL}"

echo "prepare_data completed: ${OUTPUT_JSONL}"
