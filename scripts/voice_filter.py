#!/usr/bin/env python3
"""Reusable voice-region detector for dataset preparation."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class VoiceRegion:
    start_sec: float
    end_sec: float


_VAD_FRAME_MS = 30
_PCM_BYTES_PER_SAMPLE = 2


def _run_command(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


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
    result = _run_command(cmd)
    payload = json.loads(result.stdout or "{}")
    duration_raw = payload.get("format", {}).get("duration", "0")
    try:
        duration = float(duration_raw)
    except (TypeError, ValueError):
        duration = 0.0
    return max(0.0, duration)


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
    result = _run_command(cmd)
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
    for idx, start in enumerate(starts):
        if idx < len(ends):
            silence_regions.append((start, ends[idx]))
    return silence_regions


def _decode_audio_to_pcm16(audio_path: Path, sample_rate: int) -> tuple[bytes, int]:
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostats",
        "-i",
        str(audio_path),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-f",
        "s16le",
        "-",
    ]
    with tempfile.TemporaryFile() as tmp:
        subprocess.run(
            cmd,
            stdout=tmp,
            stderr=subprocess.PIPE,
            check=True,
            text=False,
        )
        tmp.flush()
        tmp.seek(0)
        raw = tmp.read()

    sample_count = len(raw) // _PCM_BYTES_PER_SAMPLE
    if sample_count <= 0:
        raise RuntimeError(f"empty audio frame for {audio_path}")
    if len(raw) % _PCM_BYTES_PER_SAMPLE != 0:
        raise RuntimeError(f"odd byte length in decoded PCM stream from {audio_path}")

    return raw, sample_count


def _detect_with_webrtcvad(
    audio_path: Path,
    *,
    min_speech_ms: int,
    min_silence_ms: int,
    sample_rate: int,
) -> list[VoiceRegion]:
    try:
        import webrtcvad
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("webrtcvad is not installed") from exc

    raw, sample_count = _decode_audio_to_pcm16(audio_path, sample_rate=sample_rate)
    vad = webrtcvad.Vad(1)
    frame_samples = int(sample_rate * _VAD_FRAME_MS / 1000)
    frame_bytes = frame_samples * _PCM_BYTES_PER_SAMPLE
    min_frame_gap = max(0.0, float(min_silence_ms) / 1000.0)
    min_duration_sec = max(0.001, float(min_speech_ms) / 1000.0)
    min_samples = int(sample_rate * min_duration_sec)

    regions: list[VoiceRegion] = []
    current: tuple[float, float] | None = None

    idx = 0
    while idx + frame_samples <= sample_count:
        frame = raw[idx * _PCM_BYTES_PER_SAMPLE : (idx + frame_samples) * _PCM_BYTES_PER_SAMPLE]
        start_sec = idx / sample_rate
        end_sec = start_sec + float(_VAD_FRAME_MS) / 1000.0
        idx += frame_samples

        try:
            is_voice = vad.is_speech(frame, sample_rate)
        except Exception:
            continue

        if not is_voice:
            continue

        if current is None:
            current = (start_sec, end_sec)
            continue

        prev_start, prev_end = current
        if start_sec - prev_end <= min_frame_gap:
            current = (prev_start, end_sec)
        else:
            if (prev_end - prev_start) >= min_duration_sec:
                regions.append(VoiceRegion(prev_start, prev_end))
            current = (start_sec, end_sec)

    if current is not None:
        cur_start, cur_end = current
        if (cur_end - cur_start) >= min_duration_sec:
            regions.append(VoiceRegion(cur_start, cur_end))

    if min_samples > 0:
        regions = [r for r in regions if (r.end_sec - r.start_sec) * sample_rate >= min_samples]

    return regions


def _detect_with_silencedetect(
    audio_path: Path,
    *,
    min_speech_ms: int,
    min_silence_ms: int,
    noise_floor_db: float,
) -> list[VoiceRegion]:
    silence_regions = _run_ffmpeg_silencedetect(
        audio_path,
        min_silence_sec=max(0.001, float(min_silence_ms) / 1000.0),
        noise_floor_db=noise_floor_db,
    )
    return _voice_from_silence(audio_path, silence_regions)


def _detect_with_fallback(audio_path: Path) -> list[VoiceRegion]:
    # Placeholder backend for environments without optional VAD dependency.
    # Returning an empty list keeps the caller in a strict-by-default mode.
    return []


def _voice_from_silence(audio_path: Path, silence_regions: list[tuple[float, float]]) -> list[VoiceRegion]:
    total_sec = _audio_duration_seconds(audio_path)
    if total_sec <= 0:
        return []

    if not silence_regions:
        return [VoiceRegion(0.0, total_sec)]

    silence_sorted = sorted(silence_regions, key=lambda v: v[0])
    merged: list[tuple[float, float]] = []
    for start, end in silence_sorted:
        start = max(0.0, start)
        end = min(total_sec, end)
        if end <= start:
            continue
        if not merged or start > merged[-1][1]:
            merged.append((start, end))
        else:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))

    regions: list[VoiceRegion] = []
    cursor = 0.0
    for start, end in merged:
        if start > cursor:
            regions.append(VoiceRegion(cursor, start))
        cursor = max(cursor, end)

    if cursor < total_sec:
        regions.append(VoiceRegion(cursor, total_sec))

    return [r for r in regions if r.end_sec > r.start_sec]


def merge_voice_regions(
    regions: Iterable[VoiceRegion],
    max_gap_ms: int,
    min_duration_ms: int,
) -> list[VoiceRegion]:
    ordered = sorted(regions, key=lambda r: (r.start_sec, r.end_sec))
    max_gap_sec = max(0.0, float(max_gap_ms) / 1000.0)
    min_duration_sec = max(0.0, float(min_duration_ms) / 1000.0)

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

    return [r for r in merged if (r.end_sec - r.start_sec) >= min_duration_sec]


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


def detect_voice_regions(
    audio_path: str | Path,
    *,
    backend: str = "vad",
    sample_rate: int = 16000,
    min_speech_ms: int = 300,
    min_silence_ms: int = 250,
    merge_gap_ms: int = 150,
    noise_floor_db: float = -40.0,
    allow_fallback_to_full: bool = False,
) -> list[VoiceRegion]:
    if sample_rate not in {8000, 16000, 32000, 48000}:
        raise ValueError("sample_rate must be one of 8000, 16000, 32000, 48000")

    audio = Path(audio_path)
    if not audio.exists():
        raise FileNotFoundError(f"audio file not found: {audio}")

    total_sec = _audio_duration_seconds(audio)
    if total_sec <= 0:
        return []

    mode = backend.lower()
    if mode in {"off", "disabled"}:
        return [VoiceRegion(0.0, total_sec)]

    if mode not in {"silero", "vad", "hybrid", "whisper", "whisper_only"}:
        raise ValueError(f"unsupported voice backend '{backend}'")

    if mode in {"silero", "vad", "hybrid"}:
        detectors = [_detect_with_webrtcvad, _detect_with_silencedetect]
    else:
        detectors = [_detect_with_fallback]

    detected: list[VoiceRegion] = []
    last_error: Exception | None = None

    for detector in detectors:
        try:
            if detector is _detect_with_silencedetect:
                detected = detector(
                    audio,
                    min_speech_ms=min_speech_ms,
                    min_silence_ms=min_silence_ms,
                    noise_floor_db=noise_floor_db,
                )
            elif detector is _detect_with_fallback:
                detected = detector(audio)
            else:
                detected = detector(
                    audio,
                    min_speech_ms=min_speech_ms,
                    min_silence_ms=min_silence_ms,
                    sample_rate=sample_rate,
                )  # type: ignore[misc]
            if detected:
                break
        except Exception as exc:  # pragma: no cover - backend-specific failure path
            last_error = exc

    if not detected:
        if last_error is not None:
            raise RuntimeError(f"voice filtering failed: {last_error}") from last_error
        if not allow_fallback_to_full:
            raise RuntimeError("voice filtering produced no regions and fallback_to_full is disabled")
        return [VoiceRegion(0.0, total_sec)]

    detected = merge_voice_regions(detected, max_gap_ms=merge_gap_ms, min_duration_ms=min_speech_ms)
    return filter_regions_by_duration(detected, min_duration_ms=min_speech_ms, min_start=0.0, min_end=total_sec)


def to_time_spans(regions: Iterable[VoiceRegion], precision: int = 3) -> list[tuple[float, float]]:
    fmt = f"{{:.{precision}f}}"
    return [(float(fmt.format(r.start_sec)), float(fmt.format(r.end_sec))) for r in regions]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("audio_path", help="Input audio path")
    parser.add_argument("--backend", default="vad", choices=["off", "disabled", "silero", "vad", "hybrid", "whisper", "whisper_only"])
    parser.add_argument("--sample_rate", type=int, default=16000)
    parser.add_argument("--min_speech_ms", type=int, default=300)
    parser.add_argument("--min_silence_ms", type=int, default=250)
    parser.add_argument("--merge_gap_ms", type=int, default=150)
    parser.add_argument("--noise_floor_db", type=float, default=-40.0)
    parser.add_argument("--allow_fallback_to_full", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    regions = detect_voice_regions(
        args.audio_path,
        backend=args.backend,
        sample_rate=args.sample_rate,
        min_speech_ms=args.min_speech_ms,
        min_silence_ms=args.min_silence_ms,
        merge_gap_ms=args.merge_gap_ms,
        noise_floor_db=args.noise_floor_db,
        allow_fallback_to_full=args.allow_fallback_to_full,
    )
    print(to_time_spans(regions))
