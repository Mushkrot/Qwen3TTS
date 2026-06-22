#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="${QWEN3TTS_VOICE_FILTER_SMOKE_DIR:-/tmp/qwen3tts_voice_filter_smoke}"
INPUT_DIR="$TMP_DIR/input"
OUTPUT_DIR="$TMP_DIR/output"
REQUIRE_ASR="${QWEN3TTS_SMOKE_REQUIRE_ASR:-0}"

VOICE_SOURCE="${QWEN3TTS_SMOKE_VOICE_SOURCE:-${ROOT_DIR}/experiments/qwen3_ru_en_speaker_v1/samples/smoke_1_7b_epoch0_en.wav}"
ASR_MODEL="${QWEN3TTS_SMOKE_ASR_MODEL:-tiny}"
ASR_DEVICE="${QWEN3TTS_SMOKE_DEVICE:-cpu}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ERROR: ffmpeg is required for smoke script."
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "ERROR: python is required for smoke script."
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

HAS_FASTER_WHISPER="$(python - <<'PY'
import importlib.util

print("1" if importlib.util.find_spec("faster_whisper") else "0")
PY
)"

if [ "$HAS_FASTER_WHISPER" = "0" ]; then
  if [ "$REQUIRE_ASR" = "1" ]; then
    echo "ERROR: faster-whisper is not available and QWEN3TTS_SMOKE_REQUIRE_ASR=1."
    echo "Install faster-whisper and rerun smoke command."
    exit 1
  fi

  echo "[smoke] faster-whisper not available; running filter-only smoke."
  python - "$OUTPUT_DIR" "$INPUT_DIR" "$ROOT_DIR" <<'PY'
import json
import subprocess
import sys
from pathlib import Path

output_root = Path(sys.argv[1])
input_dir = Path(sys.argv[2])
root_dir = Path(sys.argv[3])
scripts_dir = root_dir / "scripts"
sys.path.insert(0, str(scripts_dir))

from voice_filter import detect_voice_regions

report_dir = output_root / "reports"
report_path = report_dir / "smoke_voice_filter.json"
removed_path = output_root / "filtered_out" / "removed_segments.jsonl"
report_dir.mkdir(parents=True, exist_ok=True)


def audio_duration(path: Path) -> float:
    proc = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    payload = json.loads(proc.stdout or "{}")
    raw = payload.get("format", {}).get("duration", "0")
    try:
        return max(0.0, float(raw))
    except (TypeError, ValueError):
        return 0.0


report_rows = []
removed_rows = []

for audio_name in ["voice.wav", "music.wav", "silence.wav", "mixed.wav"]:
    path = input_dir / audio_name
    regions = detect_voice_regions(
        path,
        backend="silero",
        sample_rate=16000,
        min_speech_ms=250,
        min_silence_ms=200,
        merge_gap_ms=120,
        allow_fallback_to_full=False,
    )
    duration = audio_duration(path)

    if regions:
        voice_seconds = sum(max(0.0, r.end_sec - r.start_sec) for r in regions)
        speech_ratio = voice_seconds / duration if duration > 0 else 0.0
        status = "accepted"
        reasons = []
        if speech_ratio < 0.75:
            status = "rejected"
            reasons = ["non_voice_ratio_too_high"]
    else:
        status = "rejected"
        speech_ratio = 0.0
        reasons = ["no_voice_regions_detected"]

    row = {
        "status": status,
        "source_audio": str(path),
        "chunk_audio": "",
        "start": 0.0,
        "end": round(duration, 3),
        "duration": round(duration, 3),
        "word_count": 0,
        "avg_confidence": 0.0,
        "low_conf_ratio": 0.0,
        "voice_regions_used_ms": round(voice_seconds * 1000.0, 3) if regions else 0.0,
        "source_duration_ms": round(duration * 1000.0, 3),
        "speech_ratio": round(min(1.0, max(0.0, speech_ratio)), 4),
        "non_voice_ratio": round(max(0.0, min(1.0, 1.0 - speech_ratio)), 4),
        "filter_mode": "silero",
        "filter_version": "2.0.0",
        "reasons": reasons,
        "text": "voice" if status == "accepted" else "",
    }
    report_rows.append(row)

    if status == "rejected":
        removed_rows.append(
            {
                "source_audio": str(path),
                "start": 0.0,
                "end": round(duration, 3),
                "duration": round(duration, 3),
                "reason": ";".join(reasons),
            }
        )

with report_path.open("w", encoding="utf-8") as f:
    json.dump(report_rows, f, ensure_ascii=False, indent=2)

if removed_rows:
    removed_path.parent.mkdir(parents=True, exist_ok=True)
    with removed_path.open("w", encoding="utf-8") as f:
        for row in removed_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

accepted = [r for r in report_rows if r["status"] == "accepted"]
rejected = [r for r in report_rows if r["status"] == "rejected"]
has_non_voice = any("non_voice_ratio_too_high" in r["reasons"] or "no_voice_regions_detected" in r["reasons"] for r in rejected)

if not accepted or not rejected:
    raise SystemExit("[smoke] expected mixed voice/non-voice results in filter-only mode")
if not has_non_voice:
    raise SystemExit("[smoke] expected explicit non-voice rejection reason in filter-only mode")

print(f"[smoke] accepted rows: {len(accepted)}")
print(f"[smoke] rejected rows: {len(rejected)}")
print(f"[smoke] removed segments file: {removed_path} exists={removed_path.exists()}")
print(f"[smoke] voice-filter smoke test (filter-only) completed")
PY

  exit 0
fi

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
