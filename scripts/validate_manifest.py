#!/usr/bin/env python3
"""Validate Qwen3-TTS training manifest JSONL.

Checks:
- valid JSON per line,
- required keys: audio, text, ref_audio,
- non-empty text,
- existing file paths,
- unique audio paths.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

REQUIRED_KEYS = ("audio", "text", "ref_audio")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_jsonl", required=True, help="Path to raw JSONL manifest")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.input_jsonl)

    if not manifest_path.exists():
        print(f"ERROR: manifest not found: {manifest_path}")
        return 1

    errors: list[str] = []
    seen_audio: set[str] = set()

    with manifest_path.open("r", encoding="utf-8") as f:
        for line_num, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                errors.append(f"line {line_num}: empty line")
                continue

            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_num}: invalid JSON ({exc})")
                continue

            for key in REQUIRED_KEYS:
                if key not in row:
                    errors.append(f"line {line_num}: missing key '{key}'")

            if any(key not in row for key in REQUIRED_KEYS):
                continue

            audio = str(row["audio"]).strip()
            text = str(row["text"]).strip()
            ref_audio = str(row["ref_audio"]).strip()

            if not text:
                errors.append(f"line {line_num}: empty text")

            audio_path = Path(audio)
            if not audio_path.exists() or not audio_path.is_file():
                errors.append(f"line {line_num}: audio path not found: {audio}")

            ref_path = Path(ref_audio)
            if not ref_path.exists() or not ref_path.is_file():
                errors.append(f"line {line_num}: ref_audio path not found: {ref_audio}")

            if audio in seen_audio:
                errors.append(f"line {line_num}: duplicate audio path: {audio}")
            seen_audio.add(audio)

    if errors:
        print("Manifest validation FAILED")
        for err in errors:
            print(f"- {err}")
        print(f"Total errors: {len(errors)}")
        return 1

    print("Manifest validation PASSED")
    print(f"Rows checked: {len(seen_audio)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
