#!/usr/bin/env python3
"""Build a Qwen3TTS training dataset from raw audio files.

Pipeline:
1) normalize source audio to 16k mono for ASR,
2) detect/pre-filter voice regions,
3) normalize source audio to 24k mono for final training chunks,
4) run word-level ASR,
5) split by pauses + duration constraints,
6) write train_raw.jsonl manifest and detailed reports.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from voice_filter import VoiceRegion, detect_voice_regions, filter_regions_by_duration


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".opus", ".wma", ".aiff"}
PUNCT_NO_SPACE_BEFORE = {".", ",", "!", "?", ":", ";", ")", "]", "}"}
PUNCT_NO_SPACE_AFTER = {"(", "[", "{"}
VOICE_FILTER_VERSION = "2.0.0"


@dataclass
class WordItem:
    token: str
    start: float
    end: float
    confidence: float


@dataclass
class SegmentConfig:
    min_duration: float
    target_duration: float
    max_duration: float
    min_pause: float
    soft_pause: float


@dataclass
class SegmentQuality:
    word_count: int
    avg_confidence: float
    low_conf_ratio: float
    reasons: list[str]

    @property
    def is_valid(self) -> bool:
        return not self.reasons


@dataclass
class SpeechRow:
    source_audio: str
    start_sec: float
    end_sec: float
    duration_sec: float
    reasons: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_dir", required=True, help="Directory with source audio files")
    parser.add_argument(
        "--output_root",
        default="experiments/qwen3_ru_en_speaker_v1/dataset_auto",
        help="Output root for converted files, chunks, and manifests",
    )
    parser.add_argument("--language", default="ru", help="ASR language code, e.g. ru, en")
    parser.add_argument("--asr_model", default="large-v3", help="faster-whisper model size/name")
    parser.add_argument("--device", default="cuda", help="ASR device, e.g. cuda or cpu")
    parser.add_argument("--compute_type", default="float16", help="ASR compute type")
    parser.add_argument(
        "--use_whisperx_align",
        action="store_true",
        help="Refine word start/end timestamps with WhisperX alignment (optional dependency)",
    )
    parser.add_argument(
        "--whisperx_interpolate_method",
        default="linear",
        help="Interpolation method for WhisperX align (e.g. linear, nearest)",
    )
    parser.add_argument("--beam_size", type=int, default=5)
    parser.add_argument("--best_of", type=int, default=5)
    parser.add_argument("--temperature", type=float, default=0.1)
    parser.add_argument("--min_duration", type=float, default=2.0)
    parser.add_argument("--target_duration", type=float, default=8.0)
    parser.add_argument("--max_duration", type=float, default=14.0)
    parser.add_argument("--min_pause", type=float, default=0.45)
    parser.add_argument("--soft_pause", type=float, default=0.25)
    parser.add_argument("--min_chars", type=int, default=8)
    parser.add_argument("--min_words", type=int, default=3)
    parser.add_argument("--low_confidence_threshold", type=float, default=0.5)
    parser.add_argument("--min_avg_confidence", type=float, default=0.45)
    parser.add_argument("--max_low_conf_ratio", type=float, default=0.35)

    parser.add_argument(
        "--voice_filter_mode",
        choices=["off", "whisper", "whisper_only", "vad", "silero", "hybrid", "strict", "legacy"],
        default="silero",
        help=(
            "off: disable pre-ASR filtering; "
            "silero/vad: run voice-region detector; "
            "whisper/whisper_only: use whisper-style fallback; "
            "hybrid/strict: legacy aliases -> silero"
        ),
    )
    parser.add_argument(
        "--voice_filter_min_speech_ms",
        type=int,
        default=300,
        help="Minimum detected speech segment length in milliseconds (primary)",
    )
    parser.add_argument(
        "--voice_filter_min_silence_ms",
        type=int,
        default=250,
        help="Minimum silence gap before segment split in milliseconds (primary)",
    )
    parser.add_argument(
        "--voice_filter_merge_gap_ms",
        type=int,
        default=150,
        help="Gap under which neighboring speech regions are merged, in milliseconds.",
    )
    parser.add_argument(
        "--voice_filter_min_coverage",
        type=float,
        default=0.75,
        help="Minimum required speech coverage ratio per final chunk.",
    )
    parser.add_argument(
        "--voice_filter_export_quarantine",
        action="store_true",
        help="Write removed non-voice regions into output_root/filtered_out/.",
    )
    parser.add_argument(
        "--voice_filter_export_quarantine_snippets",
        action="store_true",
        help="Additionally write snippet wav files under output_root/filtered_out/snippets.",
    )

    # Backward-compatible legacy knobs kept as aliases for existing scripts.
    parser.add_argument(
        "--max_no_speech_prob",
        type=float,
        default=None,
        help="Deprecated alias; retained for script compatibility.",
    )
    parser.add_argument(
        "--min_word_voice_overlap",
        type=float,
        default=None,
        help="Deprecated alias; retained for script compatibility.",
    )
    parser.add_argument(
        "--min_segment_voice_ratio",
        type=float,
        default=None,
        help="Deprecated alias for --voice_filter_min_coverage.",
    )
    parser.add_argument(
        "--legacy_mode",
        action="store_true",
        help="Compatibility alias: equivalent to --voice_filter_mode off.",
    )
    parser.add_argument(
        "--strict_mode",
        action="store_true",
        help="Compatibility alias for strict voice filtering. Equivalent to --voice_filter_mode strict.",
    )

    parser.add_argument(
        "--report_name",
        default="quality_report",
        help="Base name for quality report files in output_root/reports",
    )
    parser.add_argument(
        "--ref_audio",
        default="",
        help="Optional path to a reference audio file. If omitted, first generated chunk is used.",
    )
    parser.add_argument(
        "--manifest_name",
        default="train_raw.jsonl",
        help="Manifest filename inside output_root/manifests",
    )
    parser.add_argument(
        "--validate_manifest",
        action="store_true",
        help="Run scripts/validate_manifest.py after manifest generation",
    )
    return parser.parse_args()


def parse_filter_mode(mode: str, legacy_mode: bool, strict_mode: bool) -> str:
    normalized = mode.lower()
    if legacy_mode:
        return "off"

    if normalized == "legacy":
        return "off"
    if strict_mode:
        return "silero"
    if normalized in {"hybrid", "strict"}:
        return "silero"
    if normalized == "whisper_only":
        return "whisper"
    return normalized


def run_ffmpeg(command: list[str], *, check_result: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        command,
        check=check_result,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def convert_audio(input_path: Path, output_path: Path, sample_rate: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(output_path),
    ]
    run_ffmpeg(cmd)


def extract_segment(input_audio: Path, start_sec: float, end_sec: float, out_wav: Path, sample_rate: int) -> None:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{start_sec:.3f}",
        "-to",
        f"{end_sec:.3f}",
        "-i",
        str(input_audio),
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-c:a",
        "pcm_s16le",
        str(out_wav),
    ]
    run_ffmpeg(cmd)


def audio_duration_seconds(audio_path: Path) -> float:
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
    proc = run_ffmpeg(cmd)
    try:
        payload = json.loads(proc.stdout)
        raw = payload.get("format", {}).get("duration", "0")
        return max(0.0, float(raw))
    except Exception:
        return 0.0


def list_audio_files(input_dir: Path) -> list[Path]:
    return [p for p in sorted(input_dir.iterdir()) if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS]


def clean_token(token: str) -> str:
    token = token.strip()
    return re.sub(r"\s+", " ", token)


def join_tokens(tokens: Iterable[str]) -> str:
    out: list[str] = []
    for token in tokens:
        token = clean_token(token)
        if not token:
            continue

        if not out:
            out.append(token)
            continue

        prev = out[-1]
        if token in PUNCT_NO_SPACE_BEFORE or prev in PUNCT_NO_SPACE_AFTER:
            out[-1] = prev + token
        else:
            out.append(token)

    return " ".join(out).strip()


def segment_overlap_ratio(start_sec: float, end_sec: float, speech_regions: list[VoiceRegion]) -> float:
    if not speech_regions:
        return 0.0

    duration = max(0.0, end_sec - start_sec)
    if duration <= 0.0:
        return 0.0

    overlap = 0.0
    for region in speech_regions:
        overlap_start = max(start_sec, region.start_sec)
        overlap_end = min(end_sec, region.end_sec)
        if overlap_end > overlap_start:
            overlap += overlap_end - overlap_start

    return min(1.0, overlap / duration)


def complement_regions(total_sec: float, voice_regions: list[VoiceRegion]) -> list[VoiceRegion]:
    if total_sec <= 0.0:
        return []

    if not voice_regions:
        return [VoiceRegion(0.0, total_sec)]

    ordered = sorted(voice_regions, key=lambda r: r.start_sec)
    non_voice: list[VoiceRegion] = []
    cursor = 0.0
    for region in ordered:
        if region.start_sec > cursor:
            non_voice.append(VoiceRegion(cursor, min(region.start_sec, total_sec)))
        cursor = max(cursor, region.end_sec)
        if cursor >= total_sec:
            break

    if cursor < total_sec:
        non_voice.append(VoiceRegion(cursor, total_sec))

    return [r for r in non_voice if r.end_sec > r.start_sec]


def transcribe_words(
    model,
    audio_path_16k: Path,
    language: str,
    beam_size: int,
    best_of: int,
    temperature: float,
    use_whisperx_align: bool,
    device: str,
    whisperx_interpolate_method: str,
    segment_offset_sec: float,
) -> list[WordItem]:
    segments, info = model.transcribe(
        str(audio_path_16k),
        language=language,
        beam_size=beam_size,
        best_of=best_of,
        temperature=temperature,
        condition_on_previous_text=False,
        word_timestamps=True,
        vad_filter=True,
        vad_parameters={"min_silence_duration_ms": 400, "speech_pad_ms": 300},
    )

    segments = list(segments)
    words: list[WordItem] = []

    for segment in segments:
        if not getattr(segment, "words", None):
            continue

        for w in segment.words:
            if w.start is None or w.end is None:
                continue
            token = clean_token(w.word)
            if not token:
                continue

            words.append(
                WordItem(
                    token=token,
                    start=float(w.start) + segment_offset_sec,
                    end=float(w.end) + segment_offset_sec,
                    confidence=float(getattr(w, "probability", 1.0) or 1.0),
                )
            )

    if not use_whisperx_align or not words:
        return words

    try:
        import whisperx
    except Exception as exc:
        raise RuntimeError(
            "WhisperX alignment requested but whisperx is not available. "
            "Install it in this environment: pip install whisperx"
        ) from exc

    try:
        audio = whisperx.load_audio(str(audio_path_16k))
        align_model, metadata = whisperx.load_align_model(language_code=info.language, device=device)

        segments_dict = []
        for segment in segments:
            seg = {
                "start": float(segment.start),
                "end": float(segment.end),
                "text": str(segment.text),
            }
            if getattr(segment, "words", None):
                seg["words"] = [
                    {
                        "word": str(w.word),
                        "start": float(w.start) if w.start is not None else None,
                        "end": float(w.end) if w.end is not None else None,
                    }
                    for w in segment.words
                ]
            segments_dict.append(seg)

        aligned = whisperx.align(
            segments_dict,
            align_model,
            metadata,
            audio,
            device,
            return_char_alignments=False,
            interpolate_method=whisperx_interpolate_method,
        )

        aligned_words: list[WordItem] = []
        base_confidences = [w.confidence for w in words]
        conf_idx = 0

        for seg in aligned.get("segments", []):
            for w in seg.get("words", []):
                token = clean_token(str(w.get("word", "")))
                start = w.get("start")
                end = w.get("end")
                if not token or start is None or end is None:
                    continue

                confidence = base_confidences[conf_idx] if conf_idx < len(base_confidences) else 1.0
                conf_idx += 1
                aligned_words.append(
                    WordItem(
                        token=token,
                        start=float(start) + segment_offset_sec,
                        end=float(end) + segment_offset_sec,
                        confidence=float(confidence),
                    )
                )

        if aligned_words:
            print(f"WhisperX alignment applied for {audio_path_16k.name}: {len(aligned_words)} words")
            return aligned_words

        raise RuntimeError(
            f"WhisperX returned no aligned words for {audio_path_16k.name}. "
            "Stopping run because --use_whisperx_align is enabled."
        )
    except Exception as exc:
        raise RuntimeError(
            f"WhisperX alignment failed for {audio_path_16k.name}: {exc}. "
            "Stopping run because --use_whisperx_align is enabled."
        ) from exc


def split_into_segments(words: list[WordItem], cfg: SegmentConfig) -> list[tuple[int, int]]:
    if not words:
        return []

    boundaries: list[tuple[int, int]] = []
    start_idx = 0

    for i in range(len(words) - 1):
        current = words[i]
        nxt = words[i + 1]

        duration = current.end - words[start_idx].start
        pause = max(0.0, nxt.start - current.end)

        hard_cut = duration >= cfg.max_duration
        pause_cut = duration >= cfg.min_duration and pause >= cfg.min_pause
        soft_cut = duration >= cfg.target_duration and pause >= cfg.soft_pause

        if hard_cut or pause_cut or soft_cut:
            boundaries.append((start_idx, i))
            start_idx = i + 1

    if start_idx < len(words):
        boundaries.append((start_idx, len(words) - 1))

    return boundaries


def evaluate_segment_quality(
    seg_words: list[WordItem],
    text: str,
    source_duration: float,
    speech_ratio: float,
    args: argparse.Namespace,
) -> SegmentQuality:
    word_count = len(seg_words)
    avg_confidence = sum(w.confidence for w in seg_words) / max(1, word_count)
    low_conf_count = sum(1 for w in seg_words if w.confidence < args.low_confidence_threshold)
    low_conf_ratio = low_conf_count / max(1, word_count)
    min_coverage = args.voice_filter_min_coverage

    reasons: list[str] = []
    if source_duration < args.min_duration:
        reasons.append("duration_too_short")
    if source_duration > args.max_duration:
        reasons.append("duration_too_long")
    if len(text) < args.min_chars:
        reasons.append("text_too_short")
    if word_count < args.min_words:
        reasons.append("too_few_words")
    if avg_confidence < args.min_avg_confidence:
        reasons.append("avg_confidence_too_low")
    if low_conf_ratio > args.max_low_conf_ratio:
        reasons.append("too_many_low_confidence_words")
    if args.voice_filter_mode != "off" and speech_ratio < min_coverage:
        reasons.append("non_voice_ratio_too_high")
    if args.voice_filter_mode != "off" and source_duration * 1000 < args.voice_filter_min_speech_ms:
        reasons.append("too_few_voice_frames")

    return SegmentQuality(
        word_count=word_count,
        avg_confidence=avg_confidence,
        low_conf_ratio=low_conf_ratio,
        reasons=reasons,
    )


def build_report_row(
    status: str,
    source_audio: str,
    chunk_path: Path | None,
    start_sec: float,
    end_sec: float,
    text: str,
    reasons: list[str],
    seg_words: list[WordItem],
    source_duration_ms: float,
    voice_overlap_ms: float,
    voice_ratio: float,
    args: argparse.Namespace,
) -> dict[str, object]:
    non_voice_ratio = max(0.0, 1.0 - voice_ratio)
    return {
        "status": status,
        "source_audio": source_audio,
        "chunk_audio": str(chunk_path.resolve()) if chunk_path else "",
        "start": round(start_sec, 3),
        "end": round(end_sec, 3),
        "duration": round(end_sec - start_sec, 3),
        "word_count": len(seg_words),
        "avg_confidence": round(sum(w.confidence for w in seg_words) / max(1, len(seg_words)), 4),
        "low_conf_ratio": round(sum(1 for w in seg_words if w.confidence < args.low_confidence_threshold) / max(1, len(seg_words)), 4),
        "voice_regions_used_ms": round(voice_overlap_ms, 3),
        "source_duration_ms": round(source_duration_ms, 3),
        "speech_ratio": round(min(1.0, max(0.0, voice_ratio)), 4),
        "non_voice_ratio": round(max(0.0, min(1.0, non_voice_ratio)), 4),
        "filter_mode": args.voice_filter_mode,
        "filter_version": VOICE_FILTER_VERSION,
        "reasons": reasons,
        "text": text,
    }


def write_quality_reports(output_root: Path, report_name: str, report_rows: list[dict[str, object]]) -> tuple[Path, Path]:
    reports_dir = output_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    json_path = reports_dir / f"{report_name}.json"
    csv_path = reports_dir / f"{report_name}.csv"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(report_rows, f, ensure_ascii=False, indent=2)

    fieldnames = [
        "status",
        "source_audio",
        "chunk_audio",
        "start",
        "end",
        "duration",
        "word_count",
        "avg_confidence",
        "low_conf_ratio",
        "voice_regions_used_ms",
        "source_duration_ms",
        "speech_ratio",
        "non_voice_ratio",
        "filter_mode",
        "filter_version",
        "reasons",
        "text",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in report_rows:
            csv_row = {k: row.get(k, "") for k in fieldnames}
            if isinstance(csv_row["reasons"], list):
                csv_row["reasons"] = ";".join(csv_row["reasons"])
            writer.writerow(csv_row)

    return json_path, csv_path


def ensure_ref_audio(ref_audio_arg: str, output_root: Path, first_chunk: Path | None) -> Path:
    refs_dir = output_root / "refs"
    refs_dir.mkdir(parents=True, exist_ok=True)

    if ref_audio_arg:
        src = Path(ref_audio_arg).expanduser().resolve()
        if not src.exists():
            raise FileNotFoundError(f"ref_audio not found: {src}")
        out = refs_dir / "ref_audio_24k.wav"
        convert_audio(src, out, sample_rate=24000)
        return out.resolve()

    if first_chunk is None:
        raise RuntimeError("No chunks were created. Cannot select default ref_audio.")

    return first_chunk.resolve()


def write_removed_segments(removed_segments: list[SpeechRow], filtered_out_dir: Path) -> Path | None:
    if not removed_segments:
        return None

    filtered_out_dir.mkdir(parents=True, exist_ok=True)
    removed_path = filtered_out_dir / "removed_segments.jsonl"

    with removed_path.open("w", encoding="utf-8") as f:
        for row in removed_segments:
            payload = {
                "source_audio": row.source_audio,
                "start": round(row.start_sec, 3),
                "end": round(row.end_sec, 3),
                "duration": round(row.duration_sec, 3),
                "reason": ";".join(row.reasons),
            }
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")

    return removed_path


def write_run_metadata(output_root: Path, args: argparse.Namespace, summary: dict[str, object]) -> Path:
    metadata_path = output_root / "filtered_out" / "run_metadata.json"
    metadata = {
        "schema": "qwen3tts-voice-filtering-v1",
        "filter_version": VOICE_FILTER_VERSION,
        "voice_filter_mode": args.voice_filter_mode,
        "voice_filter_min_speech_ms": args.voice_filter_min_speech_ms,
        "voice_filter_min_silence_ms": args.voice_filter_min_silence_ms,
        "voice_filter_merge_gap_ms": args.voice_filter_merge_gap_ms,
        "voice_filter_min_coverage": args.voice_filter_min_coverage,
        "input_dir": str(Path(args.input_dir).expanduser().resolve()),
        "output_root": str(output_root),
        "summary": summary,
    }
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    return metadata_path


def add_rejected_segment(
    *,
    report_rows: list[dict[str, object]],
    removed_rows: list[SpeechRow],
    source_audio: str,
    start_sec: float,
    end_sec: float,
    reasons: list[str],
    args: argparse.Namespace,
    seg_words: list[WordItem],
    voice_overlap_ms: float,
    voice_ratio: float,
    filtered_out_dir: Path | None = None,
    source_duration_ms: float | None = None,
) -> float:
    duration_ms = source_duration_ms
    if duration_ms is None:
        duration_ms = max(0.0, end_sec - start_sec) * 1000
    duration_sec = duration_ms / 1000.0

    report_rows.append(
        build_report_row(
            status="rejected",
            source_audio=source_audio,
            chunk_path=None,
            start_sec=start_sec,
            end_sec=end_sec,
            text="",
            reasons=reasons,
            seg_words=seg_words,
            source_duration_ms=duration_ms,
            voice_overlap_ms=voice_overlap_ms,
            voice_ratio=voice_ratio,
            args=args,
        )
    )

    if filtered_out_dir is None:
        return duration_sec

    removed_rows.append(
        SpeechRow(
            source_audio=source_audio,
            start_sec=start_sec,
            end_sec=end_sec,
            duration_sec=duration_sec,
            reasons=reasons,
        )
    )
    return duration_sec


def main() -> int:
    args = parse_args()

    args.voice_filter_mode = parse_filter_mode(
        mode=args.voice_filter_mode,
        legacy_mode=args.legacy_mode,
        strict_mode=args.strict_mode,
    )
    if args.min_segment_voice_ratio is not None:
        args.voice_filter_min_coverage = args.min_segment_voice_ratio

    if args.min_word_voice_overlap and args.min_word_voice_overlap > 0:
        args.voice_filter_min_coverage = min(1.0, max(0.0, args.min_word_voice_overlap))

    # Retain compatibility with old scripts that exposed a no-speech threshold.
    if args.max_no_speech_prob is not None and 0.0 <= args.max_no_speech_prob <= 1.0:
        args.voice_filter_min_coverage = min(1.0, max(0.0, 1.0 - args.max_no_speech_prob))

    try:
        from faster_whisper import WhisperModel
    except Exception as exc:
        print("ERROR: faster-whisper is required for dataset builder.")
        print(f"Details: {exc}")
        print("Install: source .venv/bin/activate && pip install faster-whisper")
        return 1

    root_dir = Path(__file__).resolve().parent.parent
    input_dir = Path(args.input_dir).expanduser().resolve()
    output_root = (root_dir / args.output_root).resolve() if not Path(args.output_root).is_absolute() else Path(args.output_root).resolve()

    if not input_dir.exists():
        print(f"ERROR: input_dir does not exist: {input_dir}")
        return 1

    audio_files = list_audio_files(input_dir)
    if not audio_files:
        print(f"ERROR: no audio files found in {input_dir}")
        return 1

    converted_16k_dir = output_root / "processed_16k"
    converted_24k_dir = output_root / "processed_24k"
    chunks_dir = output_root / "chunks"
    transcripts_dir = output_root / "transcripts"
    manifests_dir = output_root / "manifests"
    filtered_out_dir = output_root / "filtered_out"
    temp_regions_dir = output_root / "tmp_regions"

    for d in (converted_16k_dir, converted_24k_dir, chunks_dir, transcripts_dir, manifests_dir, temp_regions_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"Found input files: {len(audio_files)}")
    print(
        "Voice filter: mode=%s, min_speech_ms=%d, min_silence_ms=%d, merge_gap_ms=%d, min_coverage=%.2f, export_quarantine=%s" %
        (
            args.voice_filter_mode,
            args.voice_filter_min_speech_ms,
            args.voice_filter_min_silence_ms,
            args.voice_filter_merge_gap_ms,
            args.voice_filter_min_coverage,
            args.voice_filter_export_quarantine,
        )
    )

    print("Loading ASR model...")
    model = WhisperModel(args.asr_model, device=args.device, compute_type=args.compute_type)

    seg_cfg = SegmentConfig(
        min_duration=args.min_duration,
        target_duration=args.target_duration,
        max_duration=args.max_duration,
        min_pause=args.min_pause,
        soft_pause=args.soft_pause,
    )

    rows: list[dict[str, str]] = []
    report_rows: list[dict[str, object]] = []
    removed_rows: list[SpeechRow] = []
    global_idx = 0
    first_chunk: Path | None = None
    total_processed_files = 0
    accepted_seconds = 0.0
    rejected_seconds = 0.0
    filtered_seconds = 0.0
    source_seconds_total = 0.0

    for file_idx, src_audio in enumerate(audio_files, start=1):
        total_processed_files += 1
        print(f"[{file_idx}/{len(audio_files)}] Processing: {src_audio.name}")

        base = src_audio.stem
        wav16 = converted_16k_dir / f"{base}.wav"
        wav24 = converted_24k_dir / f"{base}.wav"

        convert_audio(src_audio, wav16, sample_rate=16000)
        convert_audio(src_audio, wav24, sample_rate=24000)
        source_duration = audio_duration_seconds(wav16)
        source_seconds_total += source_duration
        source_audio = str(src_audio.resolve())

        try:
            if args.voice_filter_mode == "off":
                voice_regions = [VoiceRegion(0.0, source_duration)]
            else:
                voice_regions = detect_voice_regions(
                    wav16,
                    backend=args.voice_filter_mode,
                    sample_rate=16000,
                    min_speech_ms=args.voice_filter_min_speech_ms,
                    min_silence_ms=args.voice_filter_min_silence_ms,
                    merge_gap_ms=args.voice_filter_merge_gap_ms,
                    noise_floor_db=-40.0,
                    allow_fallback_to_full=False,
                )
            # Keep explicit minimum duration behavior deterministic per contract.
            voice_regions = filter_regions_by_duration(
                voice_regions,
                min_duration_ms=args.voice_filter_min_speech_ms,
                min_start=0.0,
                min_end=source_duration,
            )
        except ValueError as exc:
            print(f"ERROR: {exc}")
            return 1
        except Exception as exc:
            print(f"WARN: voice filter failed, rejecting file {src_audio.name}: {exc}")
            if not args.voice_filter_mode == "off":
                rejected_seconds += add_rejected_segment(
                    report_rows=report_rows,
                    removed_rows=removed_rows if args.voice_filter_export_quarantine else [],
                    source_audio=source_audio,
                    start_sec=0.0,
                    end_sec=source_duration,
                    reasons=["voice_filter_detection_failed"],
                    args=args,
                    seg_words=[],
                    voice_overlap_ms=0.0,
                    voice_ratio=0.0,
                    filtered_out_dir=filtered_out_dir if args.voice_filter_export_quarantine else None,
                )
            continue

        if not voice_regions:
            rejected_seconds += add_rejected_segment(
                report_rows=report_rows,
                removed_rows=removed_rows if args.voice_filter_export_quarantine else [],
                source_audio=source_audio,
                start_sec=0.0,
                end_sec=source_duration,
                reasons=["no_voice_regions_detected"],
                args=args,
                seg_words=[],
                voice_overlap_ms=0.0,
                voice_ratio=0.0,
                filtered_out_dir=filtered_out_dir if args.voice_filter_export_quarantine else None,
            )
            if args.voice_filter_export_quarantine:
                filtered_seconds += source_duration
            continue

        for region in complement_regions(source_duration, voice_regions):
            if region.end_sec <= region.start_sec:
                continue
            if args.voice_filter_export_quarantine:
                removed_rows.append(SpeechRow(
                    source_audio=source_audio,
                    start_sec=region.start_sec,
                    end_sec=region.end_sec,
                    duration_sec=region.end_sec - region.start_sec,
                    reasons=["filtered_out_region"],
                ))
                filtered_seconds += region.end_sec - region.start_sec
                if args.voice_filter_export_quarantine_snippets:
                    snippet = filtered_out_dir / "snippets" / f"{base}_removed_{int(region.start_sec*1000)}_{int(region.end_sec*1000)}.wav"
                    extract_segment(wav16, region.start_sec, region.end_sec, snippet, sample_rate=16000)

        words: list[WordItem] = []
        regions_to_process = voice_regions
        for region_idx, region in enumerate(regions_to_process, start=1):
            if region.end_sec <= region.start_sec:
                continue

            if (region.end_sec - region.start_sec) * 1000 < args.voice_filter_min_speech_ms:
                reasons = ["too_few_voice_frames", "region_too_short"]
                rejected_seconds += add_rejected_segment(
                    report_rows=report_rows,
                    removed_rows=removed_rows if args.voice_filter_export_quarantine else [],
                    source_audio=source_audio,
                    start_sec=region.start_sec,
                    end_sec=region.end_sec,
                    reasons=reasons,
                    args=args,
                    seg_words=[],
                    voice_overlap_ms=(region.end_sec - region.start_sec) * 1000,
                    voice_ratio=1.0,
                    filtered_out_dir=filtered_out_dir if args.voice_filter_export_quarantine else None,
                )
                continue

            tmp = temp_regions_dir / f"{base}_region_{region_idx:03d}.wav"
            extract_segment(wav16, region.start_sec, region.end_sec, tmp, sample_rate=16000)
            try:
                region_words = transcribe_words(
                    model=model,
                    audio_path_16k=tmp,
                    language=args.language,
                    beam_size=args.beam_size,
                    best_of=args.best_of,
                    temperature=args.temperature,
                    use_whisperx_align=args.use_whisperx_align,
                    device=args.device,
                    whisperx_interpolate_method=args.whisperx_interpolate_method,
                    segment_offset_sec=region.start_sec,
                )
            finally:
                if tmp.exists():
                    tmp.unlink()

            words.extend(region_words)

        if not words:
            rejected_seconds += add_rejected_segment(
                report_rows=report_rows,
                removed_rows=removed_rows if args.voice_filter_export_quarantine else [],
                source_audio=source_audio,
                start_sec=0.0,
                end_sec=source_duration,
                reasons=["transcription_empty"],
                args=args,
                seg_words=[],
                voice_overlap_ms=0.0,
                voice_ratio=0.0,
                filtered_out_dir=filtered_out_dir if args.voice_filter_export_quarantine else None,
            )
            continue

        boundaries = split_into_segments(words, seg_cfg)
        for left, right in boundaries:
            seg_words = words[left : right + 1]
            start_sec = seg_words[0].start
            end_sec = seg_words[-1].end
            text = join_tokens(w.token for w in seg_words)

            duration = end_sec - start_sec
            if not text:
                continue

            voice_overlap = segment_overlap_ratio(start_sec, end_sec, voice_regions)
            voice_overlap_ms = voice_overlap * duration * 1000
            source_duration_ms = duration * 1000

            quality = evaluate_segment_quality(seg_words, text, duration, voice_overlap, args)
            if not quality.is_valid:
                report_rows.append(
                    build_report_row(
                        status="rejected",
                        source_audio=str(src_audio.resolve()),
                        chunk_path=None,
                        start_sec=start_sec,
                        end_sec=end_sec,
                        text=text,
                        reasons=quality.reasons,
                        seg_words=seg_words,
                        source_duration_ms=source_duration_ms,
                        voice_overlap_ms=voice_overlap_ms,
                        voice_ratio=voice_overlap,
                        args=args,
                    )
                )
                rejected_seconds += duration
                continue

            global_idx += 1
            chunk_name = f"chunk_{global_idx:06d}.wav"
            txt_name = f"chunk_{global_idx:06d}.txt"

            chunk_path = chunks_dir / chunk_name
            text_path = transcripts_dir / txt_name

            extract_segment(wav24, start_sec, end_sec, chunk_path, sample_rate=24000)
            text_path.write_text(text, encoding="utf-8")

            if first_chunk is None:
                first_chunk = chunk_path

            rows.append(
                {
                    "audio": str(chunk_path.resolve()),
                    "text": text,
                }
            )
            report_rows.append(
                build_report_row(
                    status="accepted",
                    source_audio=str(src_audio.resolve()),
                    chunk_path=chunk_path,
                    start_sec=start_sec,
                    end_sec=end_sec,
                    text=text,
                    reasons=[],
                    seg_words=seg_words,
                    source_duration_ms=source_duration_ms,
                    voice_overlap_ms=voice_overlap_ms,
                    voice_ratio=voice_overlap,
                    args=args,
                )
            )
            accepted_seconds += duration

    if not rows:
        print("ERROR: no dataset rows produced")
        return 1

    ref_audio = ensure_ref_audio(args.ref_audio, output_root, first_chunk)

    manifest_path = manifests_dir / args.manifest_name
    with manifest_path.open("w", encoding="utf-8") as f:
        for row in rows:
            out = {
                "audio": row["audio"],
                "text": row["text"],
                "ref_audio": str(ref_audio),
            }
            f.write(json.dumps(out, ensure_ascii=False) + "\n")

    print(f"Dataset rows: {len(rows)}")
    print(f"Manifest: {manifest_path}")
    print(f"Reference audio: {ref_audio}")

    report_json, report_csv = write_quality_reports(output_root, args.report_name, report_rows)

    removed_path: Path | None = None
    if args.voice_filter_export_quarantine:
        removed_path = write_removed_segments(removed_rows, filtered_out_dir)

    summary = {
        "total_input_files": total_processed_files,
        "accepted_rows": len(rows),
        "rejected_rows": len([r for r in report_rows if r["status"] == "rejected"]),
        "accepted_seconds": round(accepted_seconds, 3),
        "rejected_seconds": round(rejected_seconds, 3),
        "filtered_seconds": round(filtered_seconds, 3),
        "source_seconds": round(source_seconds_total, 3),
        "manifest": str(manifest_path),
        "report_json": str(report_json),
        "report_csv": str(report_csv),
        "filtered_out_jsonl": str(removed_path) if removed_path else "",
    }
    metadata_path = write_run_metadata(output_root, args, summary)

    accepted_count = len([r for r in report_rows if r.get("status") == "accepted"])
    rejected_count = len([r for r in report_rows if r.get("status") == "rejected"])
    print(f"Accepted segments: {accepted_count}")
    print(f"Rejected segments: {rejected_count}")
    print(f"Quality report (json): {report_json}")
    print(f"Quality report (csv): {report_csv}")
    print(f"Run metadata: {metadata_path}")
    if removed_path:
        print(f"Quarantine rows: {removed_path}")

    if args.validate_manifest:
        validator = root_dir / "scripts" / "validate_manifest.py"
        cmd = [sys.executable, str(validator), "--input_jsonl", str(manifest_path)]
        run_ffmpeg(cmd)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
