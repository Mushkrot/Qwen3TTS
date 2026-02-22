#!/usr/bin/env python3
"""Build a Qwen3TTS training dataset from raw audio files.

Pipeline:
1) normalize source audio to 16k mono for ASR,
2) normalize source audio to 24k mono for final training chunks,
3) run word-level ASR,
4) split by pauses + duration constraints,
5) extract chunk WAVs,
6) write train_raw.jsonl manifest.
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


SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".opus", ".wma", ".aiff"}
PUNCT_NO_SPACE_BEFORE = {".", ",", "!", "?", ":", ";", ")", "]", "}"}
PUNCT_NO_SPACE_AFTER = {"(", "[", "{"}


@dataclass
class WordItem:
    token: str
    start: float
    end: float
    confidence: float


@dataclass
class SegmentItem:
    start: float
    end: float
    text: str


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


def run_ffmpeg(command: list[str]) -> None:
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def convert_audio(input_path: Path, output_path: Path, sample_rate: int) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
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
    run_ffmpeg(command)


def extract_chunk(master_audio_24k: Path, start_sec: float, end_sec: float, out_wav: Path) -> None:
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    command = [
        "ffmpeg",
        "-y",
        "-ss",
        f"{start_sec:.3f}",
        "-to",
        f"{end_sec:.3f}",
        "-i",
        str(master_audio_24k),
        "-ac",
        "1",
        "-ar",
        "24000",
        "-c:a",
        "pcm_s16le",
        str(out_wav),
    ]
    run_ffmpeg(command)


def list_audio_files(input_dir: Path) -> list[Path]:
    files = [p for p in sorted(input_dir.iterdir()) if p.is_file() and p.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS]
    return files


def clean_token(token: str) -> str:
    token = token.strip()
    token = re.sub(r"\s+", " ", token)
    return token


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
            confidence = float(getattr(w, "probability", 1.0) or 1.0)
            words.append(WordItem(token=token, start=float(w.start), end=float(w.end), confidence=confidence))

    if not use_whisperx_align:
        return words

    try:
        import whisperx

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
                    WordItem(token=token, start=float(start), end=float(end), confidence=float(confidence))
                )

        if aligned_words:
            print(f"WhisperX alignment applied for {audio_path_16k.name}: {len(aligned_words)} words")
            return aligned_words

        print(f"WARNING: WhisperX returned no aligned words for {audio_path_16k.name}; using faster-whisper words")
        return words
    except Exception as exc:
        print(f"WARNING: WhisperX alignment failed for {audio_path_16k.name}: {exc}")
        print("Falling back to faster-whisper word timestamps")

    return words


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
    duration: float,
    args: argparse.Namespace,
) -> SegmentQuality:
    word_count = len(seg_words)
    avg_confidence = sum(w.confidence for w in seg_words) / max(1, word_count)
    low_conf_count = sum(1 for w in seg_words if w.confidence < args.low_confidence_threshold)
    low_conf_ratio = low_conf_count / max(1, word_count)

    reasons: list[str] = []
    if duration < args.min_duration:
        reasons.append("duration_too_short")
    if duration > args.max_duration:
        reasons.append("duration_too_long")
    if len(text) < args.min_chars:
        reasons.append("text_too_short")
    if word_count < args.min_words:
        reasons.append("too_few_words")
    if avg_confidence < args.min_avg_confidence:
        reasons.append("avg_confidence_too_low")
    if low_conf_ratio > args.max_low_conf_ratio:
        reasons.append("too_many_low_confidence_words")

    return SegmentQuality(
        word_count=word_count,
        avg_confidence=avg_confidence,
        low_conf_ratio=low_conf_ratio,
        reasons=reasons,
    )


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


def main() -> int:
    args = parse_args()

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

    for d in (converted_16k_dir, converted_24k_dir, chunks_dir, transcripts_dir, manifests_dir):
        d.mkdir(parents=True, exist_ok=True)

    print(f"Found input files: {len(audio_files)}")
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
    global_idx = 0
    first_chunk: Path | None = None

    for file_idx, src_audio in enumerate(audio_files, start=1):
        print(f"[{file_idx}/{len(audio_files)}] Processing: {src_audio.name}")

        base = src_audio.stem
        wav16 = converted_16k_dir / f"{base}.wav"
        wav24 = converted_24k_dir / f"{base}.wav"

        convert_audio(src_audio, wav16, sample_rate=16000)
        convert_audio(src_audio, wav24, sample_rate=24000)

        words = transcribe_words(
            model=model,
            audio_path_16k=wav16,
            language=args.language,
            beam_size=args.beam_size,
            best_of=args.best_of,
            temperature=args.temperature,
            use_whisperx_align=args.use_whisperx_align,
            device=args.device,
            whisperx_interpolate_method=args.whisperx_interpolate_method,
        )

        if not words:
            print(f"WARNING: no words recognized for {src_audio.name}, skipping")
            continue

        boundaries = split_into_segments(words, seg_cfg)

        for left, right in boundaries:
            seg_words = words[left : right + 1]
            start_sec = seg_words[0].start
            end_sec = seg_words[-1].end
            duration = end_sec - start_sec
            text = join_tokens(w.token for w in seg_words)

            quality = evaluate_segment_quality(seg_words, text, duration, args)
            if not quality.is_valid:
                report_rows.append(
                    {
                        "status": "rejected",
                        "source_audio": str(src_audio.resolve()),
                        "chunk_audio": "",
                        "start": round(start_sec, 3),
                        "end": round(end_sec, 3),
                        "duration": round(duration, 3),
                        "word_count": quality.word_count,
                        "avg_confidence": round(quality.avg_confidence, 4),
                        "low_conf_ratio": round(quality.low_conf_ratio, 4),
                        "reasons": quality.reasons,
                        "text": text,
                    }
                )
                continue

            global_idx += 1
            chunk_name = f"chunk_{global_idx:06d}.wav"
            txt_name = f"chunk_{global_idx:06d}.txt"

            chunk_path = chunks_dir / chunk_name
            text_path = transcripts_dir / txt_name

            extract_chunk(wav24, start_sec, end_sec, chunk_path)
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
                {
                    "status": "accepted",
                    "source_audio": str(src_audio.resolve()),
                    "chunk_audio": str(chunk_path.resolve()),
                    "start": round(start_sec, 3),
                    "end": round(end_sec, 3),
                    "duration": round(duration, 3),
                    "word_count": quality.word_count,
                    "avg_confidence": round(quality.avg_confidence, 4),
                    "low_conf_ratio": round(quality.low_conf_ratio, 4),
                    "reasons": [],
                    "text": text,
                }
            )

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
    accepted_count = sum(1 for r in report_rows if r.get("status") == "accepted")
    rejected_count = sum(1 for r in report_rows if r.get("status") == "rejected")
    print(f"Accepted segments: {accepted_count}")
    print(f"Rejected segments: {rejected_count}")
    print(f"Quality report (json): {report_json}")
    print(f"Quality report (csv): {report_csv}")

    if args.validate_manifest:
        validator = root_dir / "scripts" / "validate_manifest.py"
        cmd = [sys.executable, str(validator), "--input_jsonl", str(manifest_path)]
        subprocess.run(cmd, check=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
