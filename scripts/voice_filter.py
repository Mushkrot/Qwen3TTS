#!/usr/bin/env python3
"""Reusable voice-region detector for dataset preparation."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class VoiceRegion:
    start_sec: float
    end_sec: float


def _run_ffmpeg_silencedetect(
    audio_path: Path,
    min_silence_sec: float,
    noise_floor_db: float,
) -> list[tuple[float, float]]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(audio_path),
        "-af",
        f"silencedetect=noise={noise_floor_db}dB:d={min_silence_sec:.3f}",
        "-f",
        "null",
        "-",
    ]
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    log = result.stderr or ""

    starts: list[float] = []
    ends: list[float] = []

    start_re = re.compile(r"silence_start:\s*([0-9]+(?:\.[0-9]+)?)")
    end_re = re.compile(r"silence_end:\s*([0-9]+(?:\.[0-9]+)?)")

    for line in log.splitlines():
        m = start_re.search(line)
        if m:
            starts.append(float(m.group(1)))
            continue

        m = end_re.search(line)
        if m:
            ends.append(float(m.group(1)))

    silence_regions: list[tuple[float, float]] = []

    for idx, s in enumerate(starts):
        e = ends[idx] if idx < len(ends) else None
        if e is None:
            continue
        silence_regions.append((s, e))

    return silence_regions


def _audio_duration_seconds(audio_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "json",
        str(audio_path),
    ]
    result = subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    payload = json.loads(result.stdout or "{}")
    duration_raw = payload.get("format", {}).get("duration", "0")
    try:
        duration = float(duration_raw)
    except (TypeError, ValueError):
        duration = 0.0
    return max(0.0, duration)


def detect_voice_regions(
    audio_path: str | Path,
    *,
    backend: str = "silero",
    sample_rate: int = 16000,
    min_speech_ms: int = 300,
    min_silence_ms: int = 250,
    merge_gap_ms: int = 150,
    noise_floor_db: float = -40.0,
) -> list[VoiceRegion]:
    audio = Path(audio_path)
    if not audio.exists():
        raise FileNotFoundError(f"audio file not found: {audio}")

    total_sec = _audio_duration_seconds(audio)
    if total_sec <= 0:
        return []

    mode = backend.lower()
    if mode in {"off", "disabled"}:
        return [VoiceRegion(0.0, total_sec)]

    if mode not in {"silero", "whisper", "vad", "whisper_only"}:
        raise ValueError(f"unsupported voice backend '{backend}'")

    if mode in {"silero", "vad"}:
        try:
            regions = _detect_with_silero(audio, min_speech_ms=min_speech_ms, min_silence_ms=min_silence_ms, noise_floor_db=noise_floor_db)
        except Exception:
            regions = _detect_with_fallback(audio, min_speech_ms=min_speech_ms, min_silence_ms=min_silence_ms)
    else:
        regions = _detect_with_fallback(audio, min_speech_ms=min_speech_ms, min_silence_ms=min_silence_ms)

    regions = merge_voice_regions(regions, max_gap_ms=merge_gap_ms, min_duration_ms=min_speech_ms)
    return filter_regions_by_duration(regions, min_duration_ms=min_speech_ms, min_start=0.0, min_end=total_sec)


def _detect_with_silero(
    audio_path: Path,
    *,
    min_speech_ms: int,
    min_silence_ms: int,
    noise_floor_db: float,
) -> list[VoiceRegion]:
    # Primary backend is represented as silencedetect to avoid optional heavy runtime deps.
    # If a true silero model is present in the environment, this function can be swapped by
    # changing the helper implementation.
    min_speech_sec = max(0.001, float(min_speech_ms) / 1000.0)
    min_silence_sec = max(0.001, float(min_silence_ms) / 1000.0)
    silence_regions = _run_ffmpeg_silencedetect(audio_path, min_silence_sec=min_silence_sec, noise_floor_db=noise_floor_db)
    return _voice_from_silence(audio_path, silence_regions)


def _detect_with_fallback(
    audio_path: Path,
    *,
    min_speech_ms: int,
    min_silence_ms: int,
) -> list[VoiceRegion]:
    # Whisper-style no-vad fallback: keep audio intact when detector cannot run.
    total_sec = _audio_duration_seconds(audio_path)
    if total_sec <= 0:
        return []
    return [VoiceRegion(0.0, total_sec)]


def _voice_from_silence(
    audio_path: Path,
    silence_regions: list[tuple[float, float]],
) -> list[VoiceRegion]:
    total_sec = _audio_duration_seconds(audio_path)
    if total_sec <= 0:
        return []

    if not silence_regions:
        return [VoiceRegion(0.0, total_sec)]

    sorted_silence = sorted(silence_regions, key=lambda x: x[0])
    merged_silence: list[tuple[float, float]] = []
    for start, end in sorted_silence:
        if end < 0 or start < 0:
            continue
        if end > total_sec:
            end = total_sec
        if not merged_silence or start > merged_silence[-1][1]:
            merged_silence.append((start, end))
        else:
            merged_silence[-1] = (merged_silence[-1][0], max(merged_silence[-1][1], end))

    voice: list[VoiceRegion] = []
    cursor = 0.0
    for silence_start, silence_end in merged_silence:
        if silence_end <= cursor:
            continue
        if silence_start > cursor:
            voice.append(VoiceRegion(cursor, silence_start))
        cursor = max(cursor, silence_end)

    if cursor < total_sec:
        voice.append(VoiceRegion(cursor, total_sec))

    return [v for v in voice if v.end_sec > v.start_sec]


def merge_voice_regions(
    regions: Iterable[VoiceRegion],
    max_gap_ms: int,
    min_duration_ms: int,
) -> list[VoiceRegion]:
    ordered = sorted(regions, key=lambda r: (r.start_sec, r.end_sec))
    max_gap_sec = max(0.0, float(max_gap_ms) / 1000.0)
    min_dur_sec = max(0.0, float(min_duration_ms) / 1000.0)

    merged: list[VoiceRegion] = []
    for region in ordered:
        if region.end_sec <= region.start_sec:
            continue

        if not merged:
            merged.append(region)
            continue

        prev = merged[-1]
        if region.start_sec - prev.end_sec <= max_gap_sec:
            merged[-1] = VoiceRegion(prev.start_sec, max(prev.end_sec, region.end_sec))
        else:
            merged.append(region)

    return [r for r in merged if (r.end_sec - r.start_sec) >= min_dur_sec]


def filter_regions_by_duration(
    regions: list[VoiceRegion],
    min_duration_ms: int,
    min_start: float,
    min_end: float,
) -> list[VoiceRegion]:
    min_duration_sec = max(0.0, float(min_duration_ms) / 1000.0)
    out: list[VoiceRegion] = []

    for region in regions:
        if region.end_sec <= region.start_sec:
            continue

        if region.end_sec < min_start or region.start_sec > min_end:
            continue

        start = max(region.start_sec, min_start)
        end = min(region.end_sec, min_end)
        if end - start >= min_duration_sec:
            out.append(VoiceRegion(start, end))

    return out


def to_time_spans(regions: Iterable[VoiceRegion], precision: int = 3) -> list[tuple[float, float]]:
    fmt = f"{{:.{precision}f}}"
    return [(float(fmt.format(r.start_sec)), float(fmt.format(r.end_sec))) for r in regions]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path", help="Audio file path")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    regions = detect_voice_regions(args.audio_path)
    print(to_time_spans(regions))
