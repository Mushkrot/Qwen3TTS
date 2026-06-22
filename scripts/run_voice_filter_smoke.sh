#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${QWEN3TTS_VOICE_FILTER_SMOKE_DIR:-/tmp/qwen3tts_voice_filter_smoke}"
INPUT_DIR="$TMP_DIR/input"
OUTPUT_DIR="$TMP_DIR/output"

VOICE_SOURCE="${QWEN3TTS_SMOKE_VOICE_SOURCE:-${ROOT_DIR}/experiments/qwen3_ru_en_speaker_v1/samples/smoke_1_7b_epoch0_en.wav}"
ASR_MODEL="${QWEN3TTS_SMOKE_ASR_MODEL:-tiny}"
ASR_DEVICE="${QWEN3TTS_SMOKE_DEVICE:-cpu}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg is required for smoke script."
  exit 1
fi

if [ ! -f "$VOICE_SOURCE" ]; then
  echo "ERROR: voice source missing: $VOICE_SOURCE"
  echo "Place a short speech sample at this path, or set QWEN3TTS_SMOKE_VOICE_SOURCE."
  exit 1
fi

rm -rf "$TMP_DIR"
mkdir -p "$INPUT_DIR" "$OUTPUT_DIR"

ffmpeg -hide_banner -loglevel error -y -i "$VOICE_SOURCE" -t 3 -af "atrim=0:3" "$INPUT_DIR/voice.wav"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "sine=frequency=440:duration=2" "$INPUT_DIR/music.wav"
ffmpeg -hide_banner -loglevel error -y -f lavfi -i "anullsrc=r=16000:cl=mono:d=1" "$INPUT_DIR/silence.wav"

cat > "$INPUT_DIR/concat.txt" <<'EOF'
file 'voice.wav'
file 'music.wav'
file 'silence.wav'
file 'voice.wav'
EOF

ffmpeg -hide_banner -loglevel error -y \
  -f concat -safe 0 -i "$INPUT_DIR/concat.txt" \
  -c copy "$INPUT_DIR/mixed.wav"

python "$ROOT_DIR/scripts/build_dataset_from_audio.py" \
  --input_dir "$INPUT_DIR" \
  --output_root "$OUTPUT_DIR" \
  --language en \
  --asr_model "$ASR_MODEL" \
  --device "$ASR_DEVICE" \
  --compute_type int8 \
  --voice_filter_mode silero \
  --voice_filter_export_quarantine \
  --voice_filter_export_quarantine_snippets \
  --voice_filter_min_speech_ms 250 \
  --voice_filter_min_silence_ms 200 \
  --voice_filter_merge_gap_ms 120 \
  --voice_filter_min_coverage 0.75 \
  --report_name smoke_voice_filter \
  --manifest_name smoke_train_raw.jsonl \
  --min_duration 1.0 \
  --min_words 1 \
  --min_chars 1 \
  --min_avg_confidence 0.0 \
  --max_low_conf_ratio 1.0 \
  --max_duration 10 \
  --target_duration 4 \
  --validate_manifest

python - "$OUTPUT_DIR"/reports/smoke_voice_filter.json "$OUTPUT_DIR"/filtered_out/removed_segments.jsonl <<'PY'
import json
import os
import sys

report_path = sys.argv[1]
removed_path = sys.argv[2]

with open(report_path, "r", encoding="utf-8") as f:
    report = json.load(f)

accepted = [row for row in report if row["status"] == "accepted"]
rejected = [row for row in report if row["status"] == "rejected"]

non_voice_reasons = {
    "no_voice_regions_detected",
    "non_voice_ratio_too_high",
    "voice_filter_detection_failed",
    "transcription_empty",
}

has_non_voice_rejection = any(
    any(reason in non_voice_reasons for reason in row.get("reasons", []))
    for row in rejected
)

print(f"[smoke] accepted rows: {len(accepted)}")
print(f"[smoke] rejected rows: {len(rejected)}")
print(f"[smoke] removed segments file: {removed_path} exists={os.path.exists(removed_path)}")
if not has_non_voice_rejection:
    raise SystemExit("[smoke] expected at least one explicit non-voice rejection reason in report")

print("[smoke] Non-voice rejection reason detected. Sample:")
for row in rejected[:3]:
    if any(reason in non_voice_reasons for reason in row.get("reasons", [])):
        print(f"  {os.path.basename(row['source_audio'])}: {row['reasons']}")
        break

print("[smoke] voice-filter smoke test completed")
PY

