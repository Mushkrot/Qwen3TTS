#!/usr/bin/env python3
"""Generate a controlled prosody comparison pack for Qwen3TTS checkpoints."""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_OUTPUT_ROOT = (
    "datasets/voices/Baritone/Ready/"
    "prosody_control_2026-06-23"
)
DEFAULT_CHUNKS_PATH: str | None = None
DEFAULT_VOICE_A_CHECKPOINT = (
    "experiments/qwen3_ru_en_speaker_v1/runs/Baritone/"
    "baritone_full_gpu_005_clean_text_lr2e6/train/epoch-0/"
    "checkpoint-epoch-0"
)
DEFAULT_VOICE_C_CHECKPOINT = (
    "experiments/qwen3_ru_en_speaker_v1/runs/Baritone/"
    "baritone_full_gpu_005_clean_text_lr2e6/train/epoch-2/"
    "checkpoint-epoch-0"
)
DEFAULT_RUSSIAN_TEXT = (
    "Начало учебного года. Мне — в восьмой класс. Каникулы закончились. "
    "Солнце било прямо в глаза. Я зажмурился, перевернулся на другой бок и… "
    "замер. Что-то было не так. Кровать что ли больше. Или я стал меньше? "
    "Медленно открыл глаза. Потолок. Белый. На нём люстра — три круглых "
    "плафона, как в детстве. Но ведь у меня сейчас современная лампа… Сел, "
    "огляделся. Комната моя, но… другая. Обои с гоночными машинками. Я таких "
    "лет пять не видел! На стуле — коричневый пиджак и серые брюки. Школьная "
    "форма из начальной школы. Сердце забилось чаще. Руки. Это не мои руки! — "
    "Маленькие. Вскочил, кинулся к зеркалу на шкафу. Из зеркала смотрел "
    "мальчишка. Знакомый до боли. Круглое лицо, вихры торчат во все стороны, "
    "глаза огромные от испуга. Это был я. Десятилетний. А мне четырнадцать. "
    "Я в восьмом классе!"
)
DEFAULT_ENGLISH_TEXT = (
    "In the contemporary corporate landscape, fear is rarely a response to "
    "physical danger, yet the neurobiological response it elicits is no less "
    "potent. I have come to realize through my own personal discovery path and "
    "professional findings that what we often dismiss as \"office stress\" is "
    "actually a \"complex cocktail of professional stakes and deep-seated "
    "psychological triggers\". At its core, workplace anxiety signals a "
    "fundamental breakdown in Psychological Safety--the shared belief that an "
    "environment is secure enough for individuals to speak up, admit errors, or "
    "propose dissenting ideas without the threat of punishment or humiliation. "
    "When this safety evaporates, our \"Ancient Brain\" takes precedence over "
    "the executive functions of the prefrontal cortex. This \"amygdala hijack\" "
    "shifts our focus from innovation and collaboration to primal survival. The "
    "workplace is no longer a site of professional contribution; it becomes a "
    "minefield of psychological triggers where a missed deadline is perceived "
    "not as a business metric, but as a precursor to \"Tribal Exile\"."
)


@dataclass(frozen=True)
class Voice:
    label: str
    checkpoint: Path
    speaker: str = "speaker_target"


@dataclass(frozen=True)
class TextCase:
    key: str
    language: str
    text: str
    context_note: str


@dataclass(frozen=True)
class Variant:
    key: str
    mode: str
    kwargs: dict[str, Any]
    instruct_by_text: dict[str, str | None]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate RU/EN prosody-control samples for voice A/C."
    )
    parser.add_argument("--output-root", default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--chunks-jsonl", default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--voice-a-checkpoint", default=DEFAULT_VOICE_A_CHECKPOINT)
    parser.add_argument("--voice-c-checkpoint", default=DEFAULT_VOICE_C_CHECKPOINT)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--attn-implementation", default="sdpa")
    parser.add_argument("--dtype", default="bfloat16", choices=("bfloat16", "float16", "float32"))
    parser.add_argument("--voice", action="append", choices=("A", "C"))
    parser.add_argument("--variant", action="append")
    parser.add_argument("--text-case", action="append", choices=("ru", "en"))
    return parser.parse_args()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def select_russian_text(chunks_path: Path | None) -> str:
    if chunks_path is None or not chunks_path.exists():
        return DEFAULT_RUSSIAN_TEXT
    rows = read_jsonl(chunks_path)
    for row in rows:
        if row.get("id") == 2:
            return str(row["text"])
    raise RuntimeError(f"chunk id 2 not found in {chunks_path}")


def text_chars(text: str) -> int:
    return len([char for char in text if not char.isspace()])


def rough_max_new_tokens(text: str) -> int:
    return max(1200, min(6200, int(text_chars(text) * 5.4)))


def words_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def build_text_cases(chunks_path: Path | None) -> list[TextCase]:
    russian_text = select_russian_text(chunks_path)
    return [
        TextCase(
            key="ru",
            language="russian",
            text=russian_text,
            context_note=(
                "Russian first-person fantasy/school audiobook scene: a "
                "teenager wakes in his ten-year-old body, frightened and "
                "confused. Needs suspense, clear sentence breaks, and dialogue "
                "intonation."
            ),
        ),
        TextCase(
            key="en",
            language="english",
            text=DEFAULT_ENGLISH_TEXT,
            context_note=(
                "English analytical nonfiction about workplace fear, "
                "psychological safety, and amygdala hijack. Needs calm, serious "
                "business-audiobook pacing with conceptual emphasis."
            ),
        ),
    ]


def build_variants() -> list[Variant]:
    ru_balanced = (
        "Narrate this Russian audiobook passage in a calm, deliberate style. "
        "The speaker is confused and frightened but controlled. Read slower "
        "than normal, preserve the suspense, use clear pauses after each "
        "sentence, and make questions sound like questions. Do not rush."
    )
    ru_heavy = (
        "Read this Russian text as a careful audiobook narrator. Speak very "
        "slowly and clearly. Insert short pauses at commas and dashes, clear "
        "pauses between sentences, and longer pauses before surprising or "
        "frightening realizations. Keep the voice natural and do not race."
    )
    en_balanced = (
        "Narrate this English business-audiobook passage in a calm, serious, "
        "analytical voice. Speak slower than normal, with confident pacing. "
        "Pause clearly between sentences and emphasize key concepts such as "
        "Psychological Safety, Ancient Brain, amygdala hijack, and Tribal Exile."
    )
    en_heavy = (
        "Read this English nonfiction passage very deliberately, as a premium "
        "audiobook narrator. Use slow pacing, thoughtful pauses after complex "
        "clauses, clear pauses between sentences, and measured emphasis on "
        "technical concepts. Do not hurry."
    )
    return [
        Variant(
            key="01_control_default",
            mode="single",
            kwargs={
                "do_sample": True,
                "temperature": 0.9,
                "top_k": 50,
                "top_p": 1.0,
                "repetition_penalty": 1.05,
                "subtalker_temperature": 0.9,
                "subtalker_top_k": 50,
                "subtalker_top_p": 1.0,
            },
            instruct_by_text={"ru": None, "en": None},
        ),
        Variant(
            key="02_context_audiobook_balanced",
            mode="single",
            kwargs={
                "do_sample": True,
                "temperature": 0.75,
                "top_k": 40,
                "top_p": 0.9,
                "repetition_penalty": 1.08,
                "subtalker_temperature": 0.75,
                "subtalker_top_k": 40,
                "subtalker_top_p": 0.9,
            },
            instruct_by_text={"ru": ru_balanced, "en": en_balanced},
        ),
        Variant(
            key="03_slow_pause_heavy_single",
            mode="single",
            kwargs={
                "do_sample": True,
                "temperature": 0.6,
                "top_k": 30,
                "top_p": 0.82,
                "repetition_penalty": 1.12,
                "subtalker_temperature": 0.6,
                "subtalker_top_k": 30,
                "subtalker_top_p": 0.82,
            },
            instruct_by_text={"ru": ru_heavy, "en": en_heavy},
        ),
        Variant(
            key="04_segmented_slow_stitched",
            mode="segmented",
            kwargs={
                "do_sample": True,
                "temperature": 0.65,
                "top_k": 35,
                "top_p": 0.86,
                "repetition_penalty": 1.1,
                "subtalker_temperature": 0.65,
                "subtalker_top_k": 35,
                "subtalker_top_p": 0.86,
            },
            instruct_by_text={"ru": ru_heavy, "en": en_heavy},
        ),
    ]


def split_sentences(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    pieces = re.split(r"(?<=[.!?])\s+", normalized)
    return [piece.strip() for piece in pieces if piece.strip()]


def split_long_piece(piece: str, max_chars: int = 220) -> list[str]:
    if len(piece) <= max_chars:
        return [piece]
    tokens = re.split(r"([,;:—-]\s+)", piece)
    out: list[str] = []
    current = ""
    for token in tokens:
        candidate = current + token
        if len(candidate) > max_chars and current.strip():
            out.append(current.strip())
            current = token.lstrip()
        else:
            current = candidate
    if current.strip():
        out.append(current.strip())
    return out


def split_for_stitch(text: str) -> list[dict[str, Any]]:
    segments: list[dict[str, Any]] = []
    for sentence in split_sentences(text):
        pieces = split_long_piece(sentence)
        for index, piece in enumerate(pieces):
            is_final_piece = index == len(pieces) - 1
            pause = 0.72 if is_final_piece else 0.42
            if piece.endswith(("!", "?")):
                pause += 0.18
            segments.append({"text": piece, "pause_after_seconds": pause})
    return segments


def silence(sample_rate: int, seconds: float):
    import numpy as np

    return np.zeros(int(sample_rate * seconds), dtype="float32")


def audio_metrics(wav, sample_rate: int, source_text: str) -> dict[str, Any]:
    import numpy as np

    samples = np.asarray(wav, dtype="float32")
    if samples.ndim > 1:
        mono = samples.mean(axis=1)
    else:
        mono = samples
    duration = len(mono) / sample_rate if sample_rate else 0.0
    rms = float(np.sqrt(np.mean(np.square(mono)))) if len(mono) else 0.0
    rms_dbfs = 20.0 * math.log10(max(rms, 1e-9))
    threshold = max(0.01, rms * 0.08)
    voiced = np.flatnonzero(np.abs(mono) > threshold)
    if len(voiced):
        leading = voiced[0] / sample_rate
        trailing = (len(mono) - voiced[-1] - 1) / sample_rate
    else:
        leading = duration
        trailing = duration
    chars = text_chars(source_text)
    words = words_count(source_text)
    return {
        "duration_seconds": round(duration, 3),
        "chars": chars,
        "words": words,
        "pace_chars_per_sec": round(chars / duration, 4) if duration else 0.0,
        "pace_words_per_sec": round(words / duration, 4) if duration else 0.0,
        "rms_dbfs": round(rms_dbfs, 3),
        "leading_silence_seconds": round(leading, 3),
        "trailing_silence_seconds": round(trailing, 3),
    }


def torch_dtype(name: str):
    import torch

    return {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }[name]


def generate_single(model, case: TextCase, variant: Variant):
    kwargs = dict(variant.kwargs)
    kwargs["max_new_tokens"] = rough_max_new_tokens(case.text)
    return model.generate_custom_voice(
        text=case.text,
        speaker="speaker_target",
        language=case.language,
        instruct=variant.instruct_by_text.get(case.key),
        **kwargs,
    )


def generate_segmented(model, case: TextCase, variant: Variant):
    import numpy as np

    parts = []
    segment_rows: list[dict[str, Any]] = []
    sample_rate = None
    chunks = split_for_stitch(case.text)
    base_kwargs = dict(variant.kwargs)
    instruct = variant.instruct_by_text.get(case.key)
    for index, chunk in enumerate(chunks, start=1):
        text = str(chunk["text"])
        kwargs = dict(base_kwargs)
        kwargs["max_new_tokens"] = rough_max_new_tokens(text)
        started = time.monotonic()
        wavs, sr = model.generate_custom_voice(
            text=text,
            speaker="speaker_target",
            language=case.language,
            instruct=instruct,
            **kwargs,
        )
        elapsed = time.monotonic() - started
        sample_rate = sr
        wav = np.asarray(wavs[0], dtype="float32")
        parts.append(wav)
        pause = float(chunk["pause_after_seconds"])
        parts.append(silence(sr, pause))
        segment_rows.append(
            {
                "index": index,
                "text": text,
                "pause_after_seconds": pause,
                "elapsed_seconds": round(elapsed, 3),
                **audio_metrics(wav, sr, text),
            }
        )
    if sample_rate is None:
        raise RuntimeError("segmented generation produced no segments")
    return [np.concatenate(parts)], sample_rate, segment_rows


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run() -> int:
    args = parse_args()

    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    all_voices = {
        "A": Voice(
            label="A",
            checkpoint=Path(args.voice_a_checkpoint),
        ),
        "C": Voice(
            label="C",
            checkpoint=Path(args.voice_c_checkpoint),
        ),
    }
    voice_keys = args.voice or ["A", "C"]
    voices = [all_voices[key] for key in voice_keys]
    missing = [voice for voice in voices if not voice.checkpoint.exists()]
    if missing:
        details = ", ".join(f"{voice.label}: {voice.checkpoint}" for voice in missing)
        raise RuntimeError(
            "Missing Qwen3TTS checkpoint(s). Regenerate the Baritone run or "
            f"pass explicit --voice-a-checkpoint/--voice-c-checkpoint paths: {details}"
        )

    chunks_path = Path(args.chunks_jsonl) if args.chunks_jsonl else None
    text_cases = build_text_cases(chunks_path)
    if args.text_case:
        wanted = set(args.text_case)
        text_cases = [case for case in text_cases if case.key in wanted]

    variants = build_variants()
    if args.variant:
        wanted_variants = set(args.variant)
        variants = [variant for variant in variants if variant.key in wanted_variants]

    texts_dir = output_root / "texts"
    texts_dir.mkdir(parents=True, exist_ok=True)
    for case in text_cases:
        (texts_dir / f"{case.key}.txt").write_text(case.text + "\n", encoding="utf-8")

    write_json(
        output_root / "run_config.json",
        {
            "voices": [
                {
                    "label": voice.label,
                    "checkpoint": str(voice.checkpoint),
                    "speaker": voice.speaker,
                }
                for voice in voices
            ],
            "text_cases": [
                {
                    "key": case.key,
                    "language": case.language,
                    "chars": text_chars(case.text),
                    "words": words_count(case.text),
                    "context_note": case.context_note,
                }
                for case in text_cases
            ],
            "variants": [
                {
                    "key": variant.key,
                    "mode": variant.mode,
                    "kwargs": variant.kwargs,
                    "instruct_by_text": variant.instruct_by_text,
                }
                for variant in variants
            ],
            "device": args.device,
            "attn_implementation": args.attn_implementation,
            "dtype": args.dtype,
        },
    )

    manifest_path = output_root / "manifest.jsonl"
    if manifest_path.exists():
        manifest_path.unlink()

    summary_rows: list[dict[str, Any]] = []
    for voice in voices:
        print(f"Loading voice {voice.label}: {voice.checkpoint}", flush=True)
        model = Qwen3TTSModel.from_pretrained(
            str(voice.checkpoint),
            device_map=args.device,
            dtype=torch_dtype(args.dtype),
            attn_implementation=args.attn_implementation,
        )
        for case in text_cases:
            for variant in variants:
                output_dir = output_root / f"voice_{voice.label}" / case.key
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{variant.key}.wav"
                segment_rows: list[dict[str, Any]] = []
                started = time.monotonic()
                print(
                    f"Generating voice={voice.label} text={case.key} "
                    f"variant={variant.key}",
                    flush=True,
                )
                try:
                    if variant.mode == "segmented":
                        wavs, sr, segment_rows = generate_segmented(model, case, variant)
                    else:
                        wavs, sr = generate_single(model, case, variant)
                    elapsed = time.monotonic() - started
                    sf.write(str(output_path), wavs[0], sr)
                    metrics = audio_metrics(wavs[0], sr, case.text)
                    row = {
                        "voice": voice.label,
                        "checkpoint": str(voice.checkpoint),
                        "speaker": voice.speaker,
                        "text_case": case.key,
                        "language": case.language,
                        "variant": variant.key,
                        "mode": variant.mode,
                        "output_path": str(output_path),
                        "elapsed_seconds": round(elapsed, 3),
                        "instruct": variant.instruct_by_text.get(case.key),
                        "generation_kwargs": {
                            **variant.kwargs,
                            "max_new_tokens": rough_max_new_tokens(case.text),
                        },
                        "segments": segment_rows,
                        "error": None,
                        **metrics,
                    }
                except Exception as exc:
                    row = {
                        "voice": voice.label,
                        "checkpoint": str(voice.checkpoint),
                        "speaker": voice.speaker,
                        "text_case": case.key,
                        "language": case.language,
                        "variant": variant.key,
                        "mode": variant.mode,
                        "output_path": str(output_path),
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                        "instruct": variant.instruct_by_text.get(case.key),
                        "generation_kwargs": {
                            **variant.kwargs,
                            "max_new_tokens": rough_max_new_tokens(case.text),
                        },
                        "segments": segment_rows,
                        "error": repr(exc),
                    }
                    print(f"ERROR: {row['error']}", flush=True)
                append_jsonl(manifest_path, row)
                summary_rows.append(row)
        del model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    write_json(
        output_root / "summary.json",
        {
            "output_root": str(output_root),
            "manifest_path": str(manifest_path),
            "sample_count": len([row for row in summary_rows if row.get("error") is None]),
            "failed_count": len([row for row in summary_rows if row.get("error") is not None]),
            "rows": summary_rows,
        },
    )
    print(f"Wrote manifest: {manifest_path}", flush=True)
    print(f"Wrote summary: {output_root / 'summary.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
