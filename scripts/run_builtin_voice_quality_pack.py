#!/usr/bin/env python3
"""Generate best-effort built-in Qwen3TTS voice samples for RU/EN text."""

from __future__ import annotations

import argparse
import json
import math
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
DEFAULT_DATASETS_ROOT = "datasets/voices"
DEFAULT_RUN_NAME = "builtin_quality_2026-06-23"
DEFAULT_CHUNKS_PATH: str | None = None
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
class Speaker:
    name: str
    note: str


@dataclass(frozen=True)
class TextCase:
    key: str
    language: str
    text: str
    context_note: str


@dataclass(frozen=True)
class Variant:
    key: str
    max_chars: int
    max_sentences: int
    pause_sentence: float
    pause_para: float
    crossfade_ms: int
    seed: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument(
        "--output-root",
        default=None,
        help=(
            "Optional legacy single-root output. If omitted, audio is written "
            "to datasets/voices/<speaker>/Ready/<run-name>/ and global "
            "metadata is written to datasets/voices/_Benchmarks/Ready/<run-name>/."
        ),
    )
    parser.add_argument("--datasets-root", default=DEFAULT_DATASETS_ROOT)
    parser.add_argument("--run-name", default=DEFAULT_RUN_NAME)
    parser.add_argument("--chunks-jsonl", default=DEFAULT_CHUNKS_PATH)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--attn-implementation", default="sdpa")
    parser.add_argument("--dtype", choices=("bfloat16", "float16", "float32"), default="bfloat16")
    parser.add_argument("--speaker", action="append")
    parser.add_argument("--text-case", choices=("ru", "en"), action="append")
    parser.add_argument("--variant", action="append")
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
    for row in read_jsonl(chunks_path):
        if row.get("id") == 2:
            return str(row["text"])
    raise RuntimeError(f"chunk id 2 not found: {chunks_path}")


def build_text_cases(chunks_path: Path | None) -> list[TextCase]:
    return [
        TextCase(
            key="ru",
            language="Russian",
            text=select_russian_text(chunks_path),
            context_note=(
                "Russian audiobook scene: first-person fantasy/school story. "
                "The narrator wakes up in a younger body, confused and scared. "
                "Needs suspense, clear sentence boundaries, and natural dialogue."
            ),
        ),
        TextCase(
            key="en",
            language="English",
            text=DEFAULT_ENGLISH_TEXT,
            context_note=(
                "English business/nonfiction audiobook passage about workplace "
                "fear, Psychological Safety, Ancient Brain, amygdala hijack, "
                "and Tribal Exile. Needs calm, serious, premium audiobook pacing."
            ),
        ),
    ]


def default_speakers() -> list[Speaker]:
    return [
        Speaker("Aiden", "Native English; sunny American male voice with clear midrange."),
        Speaker("Ryan", "Native English; dynamic male voice with strong rhythmic drive."),
    ]


def default_variants() -> list[Variant]:
    return [
        Variant(
            key="01_quality_medium_chunks",
            max_chars=460,
            max_sentences=3,
            pause_sentence=0.56,
            pause_para=0.82,
            crossfade_ms=35,
            seed=1701,
        ),
        Variant(
            key="02_quality_longer_chunks",
            max_chars=760,
            max_sentences=5,
            pause_sentence=0.68,
            pause_para=0.95,
            crossfade_ms=45,
            seed=2603,
        ),
    ]


def sentence_split(text: str) -> list[str]:
    normalized = re.sub(r"\s+", " ", text.strip())
    pieces = re.split(r"(?<=[.!?])\s+", normalized)
    return [piece.strip() for piece in pieces if piece.strip()]


def group_sentences(text: str, variant: Variant) -> list[dict[str, Any]]:
    sentences = sentence_split(text)
    groups: list[dict[str, Any]] = []
    current: list[str] = []
    for sentence in sentences:
        candidate = " ".join(current + [sentence])
        if current and (len(candidate) > variant.max_chars or len(current) >= variant.max_sentences):
            groups.append({"text": " ".join(current), "pause_after_seconds": variant.pause_sentence})
            current = [sentence]
        else:
            current.append(sentence)
    if current:
        groups.append({"text": " ".join(current), "pause_after_seconds": variant.pause_para})
    for group in groups:
        text = group["text"]
        if text.endswith(("?", "!")):
            group["pause_after_seconds"] = max(float(group["pause_after_seconds"]), variant.pause_sentence + 0.18)
    return groups


def text_chars(text: str) -> int:
    return len([char for char in text if not char.isspace()])


def words_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE))


def rough_max_new_tokens(text: str, language_key: str) -> int:
    chars = text_chars(text)
    if language_key == "ru":
        return max(220, min(1100, int(chars * 2.0) + 120))
    return max(260, min(1300, int(chars * 1.8) + 120))


def torch_dtype(name: str):
    import torch

    return {
        "bfloat16": torch.bfloat16,
        "float16": torch.float16,
        "float32": torch.float32,
    }[name]


def build_instruct(case: TextCase, speaker: Speaker, previous_text: str | None) -> str:
    previous = ""
    if previous_text:
        tail = previous_text[-260:]
        previous = (
            f" Previous context for continuity only, do not read it aloud: {tail!r}."
        )
    if case.key == "en":
        return (
            "Narrate the current English passage as a high-quality audiobook. "
            "Use the same speaker identity throughout, with calm, serious, "
            "measured pacing. Do not hurry. Preserve endings of words. Make "
            "short pauses at clause boundaries and clear pauses between ideas. "
            "Emphasize key concepts naturally, without theatrical overacting."
            f" Speaker target: {speaker.note}.{previous}"
        )
    return (
        "Read the current Russian passage as a careful audiobook narrator. "
        "Use slow, clear pacing and keep the same speaker identity throughout. "
        "Do not hurry. Preserve endings of words. Use suspense for the childlike "
        "confusion and make questions sound like questions. Avoid theatrical "
        "overacting."
        f" Speaker target: {speaker.note}.{previous}"
    )


def gen_kwargs_for(case: TextCase, speaker: Speaker, text: str) -> dict[str, Any]:
    # Aiden is the calmer baseline; Ryan needs slightly tighter sampling because
    # the official description says he has strong rhythmic drive.
    if speaker.name.lower() == "ryan":
        temperature = 0.56
        top_p = 0.8
        top_k = 28
        repetition_penalty = 1.1
    else:
        temperature = 0.62
        top_p = 0.84
        top_k = 34
        repetition_penalty = 1.08
    if case.key == "ru":
        temperature = min(temperature, 0.58)
        top_p = min(top_p, 0.82)
    return {
        "max_new_tokens": rough_max_new_tokens(text, case.key),
        "do_sample": True,
        "temperature": temperature,
        "top_k": top_k,
        "top_p": top_p,
        "repetition_penalty": repetition_penalty,
        "subtalker_dosample": True,
        "subtalker_temperature": temperature,
        "subtalker_top_k": top_k,
        "subtalker_top_p": top_p,
    }


def silence(sample_rate: int, seconds: float):
    import numpy as np

    return np.zeros(int(sample_rate * seconds), dtype="float32")


def apply_fades(wav, sample_rate: int, fade_ms: int):
    import numpy as np

    arr = np.asarray(wav, dtype="float32").copy()
    fade_len = min(len(arr) // 4, int(sample_rate * fade_ms / 1000))
    if fade_len <= 1:
        return arr
    fade_in = np.linspace(0.0, 1.0, fade_len, dtype="float32")
    fade_out = np.linspace(1.0, 0.0, fade_len, dtype="float32")
    arr[:fade_len] *= fade_in
    arr[-fade_len:] *= fade_out
    return arr


def join_parts(parts: list[Any], sample_rate: int, crossfade_ms: int):
    import numpy as np

    if not parts:
        return np.array([], dtype="float32")
    crossfade = int(sample_rate * crossfade_ms / 1000)
    out = np.asarray(parts[0], dtype="float32")
    for part in parts[1:]:
        part = np.asarray(part, dtype="float32")
        if crossfade <= 1 or len(out) < crossfade or len(part) < crossfade:
            out = np.concatenate([out, part])
            continue
        fade_out = np.linspace(1.0, 0.0, crossfade, dtype="float32")
        fade_in = np.linspace(0.0, 1.0, crossfade, dtype="float32")
        overlap = out[-crossfade:] * fade_out + part[:crossfade] * fade_in
        out = np.concatenate([out[:-crossfade], overlap, part[crossfade:]])
    return out


def audio_metrics(wav, sample_rate: int, source_text: str) -> dict[str, Any]:
    import numpy as np

    samples = np.asarray(wav, dtype="float32")
    duration = len(samples) / sample_rate if sample_rate else 0.0
    rms = float(np.sqrt(np.mean(np.square(samples)))) if len(samples) else 0.0
    chars = text_chars(source_text)
    words = words_count(source_text)
    return {
        "duration_seconds": round(duration, 3),
        "chars": chars,
        "words": words,
        "pace_chars_per_sec": round(chars / duration, 4) if duration else 0.0,
        "pace_words_per_sec": round(words / duration, 4) if duration else 0.0,
        "rms_dbfs": round(20.0 * math.log10(max(rms, 1e-9)), 3),
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def run() -> int:
    args = parse_args()

    import numpy as np
    import soundfile as sf
    import torch
    from qwen_tts import Qwen3TTSModel

    if args.output_root:
        metadata_root = Path(args.output_root)
    else:
        metadata_root = Path(args.datasets_root) / "_Benchmarks" / "Ready" / args.run_name
    metadata_root.mkdir(parents=True, exist_ok=True)
    manifest_path = metadata_root / "manifest.jsonl"
    if manifest_path.exists():
        manifest_path.unlink()

    speakers = default_speakers()
    if args.speaker:
        wanted = {speaker.lower() for speaker in args.speaker}
        speakers = [speaker for speaker in speakers if speaker.name.lower() in wanted]

    chunks_path = Path(args.chunks_jsonl) if args.chunks_jsonl else None
    text_cases = build_text_cases(chunks_path)
    if args.text_case:
        wanted_cases = set(args.text_case)
        text_cases = [case for case in text_cases if case.key in wanted_cases]

    variants = default_variants()
    if args.variant:
        wanted_variants = set(args.variant)
        variants = [variant for variant in variants if variant.key in wanted_variants]

    texts_dir = metadata_root / "texts"
    texts_dir.mkdir(parents=True, exist_ok=True)
    for case in text_cases:
        (texts_dir / f"{case.key}.txt").write_text(case.text + "\n", encoding="utf-8")

    write_json(
        metadata_root / "run_config.json",
        {
            "model": args.model,
            "datasets_root": args.datasets_root,
            "run_name": args.run_name,
            "output_root": args.output_root,
            "metadata_root": str(metadata_root),
            "speakers": [speaker.__dict__ for speaker in speakers],
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
            "variants": [variant.__dict__ for variant in variants],
            "device": args.device,
            "attn_implementation": args.attn_implementation,
            "dtype": args.dtype,
            "notes": [
                "Official Qwen docs recommend native-language speakers for best quality.",
                "Aiden and Ryan are the built-in native-English speakers.",
                "Qwen3TTS has no built-in native-Russian speaker in the documented list.",
            ],
        },
    )

    print(f"Loading built-in CustomVoice model: {args.model}", flush=True)
    tts = Qwen3TTSModel.from_pretrained(
        args.model,
        device_map=args.device,
        dtype=torch_dtype(args.dtype),
        attn_implementation=args.attn_implementation,
    )
    supported = tts.get_supported_speakers()
    print(f"Supported speakers: {supported}", flush=True)

    rows: list[dict[str, Any]] = []
    for speaker in speakers:
        for case in text_cases:
            for variant in variants:
                groups = group_sentences(case.text, variant)
                if args.output_root:
                    output_dir = Path(args.output_root) / speaker.name / case.key
                else:
                    output_dir = (
                        Path(args.datasets_root)
                        / speaker.name
                        / "Ready"
                        / args.run_name
                        / case.key
                    )
                output_dir.mkdir(parents=True, exist_ok=True)
                output_path = output_dir / f"{variant.key}.wav"
                segment_rows: list[dict[str, Any]] = []
                parts = []
                sample_rate = None
                previous_text: str | None = None
                started = time.monotonic()
                print(
                    f"Generating speaker={speaker.name} text={case.key} variant={variant.key} "
                    f"segments={len(groups)}",
                    flush=True,
                )
                error = None
                try:
                    for index, group in enumerate(groups, start=1):
                        text = str(group["text"])
                        torch.manual_seed(variant.seed + index)
                        if torch.cuda.is_available():
                            torch.cuda.manual_seed_all(variant.seed + index)
                        instruct = build_instruct(case, speaker, previous_text)
                        kwargs = gen_kwargs_for(case, speaker, text)
                        seg_started = time.monotonic()
                        wavs, sr = tts.generate_custom_voice(
                            text=text,
                            language=case.language,
                            speaker=speaker.name,
                            instruct=instruct,
                            **kwargs,
                        )
                        elapsed = time.monotonic() - seg_started
                        sample_rate = sr
                        wav = apply_fades(wavs[0], sr, variant.crossfade_ms)
                        parts.append(wav)
                        pause = float(group["pause_after_seconds"])
                        parts.append(silence(sr, pause))
                        segment_rows.append(
                            {
                                "index": index,
                                "text": text,
                                "pause_after_seconds": pause,
                                "instruct": instruct,
                                "generation_kwargs": kwargs,
                                "elapsed_seconds": round(elapsed, 3),
                                **audio_metrics(wav, sr, text),
                            }
                        )
                        previous_text = text
                    if sample_rate is None:
                        raise RuntimeError("no audio generated")
                    final = join_parts(parts, sample_rate, variant.crossfade_ms)
                    sf.write(str(output_path), np.asarray(final, dtype="float32"), sample_rate)
                    row = {
                        "speaker": speaker.name,
                        "speaker_note": speaker.note,
                        "text_case": case.key,
                        "language": case.language,
                        "variant": variant.key,
                        "output_path": str(output_path),
                        "segment_count": len(groups),
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                        "segments": segment_rows,
                        "error": None,
                        **audio_metrics(final, sample_rate, case.text),
                    }
                except Exception as exc:
                    error = repr(exc)
                    row = {
                        "speaker": speaker.name,
                        "speaker_note": speaker.note,
                        "text_case": case.key,
                        "language": case.language,
                        "variant": variant.key,
                        "output_path": str(output_path),
                        "segment_count": len(groups),
                        "elapsed_seconds": round(time.monotonic() - started, 3),
                        "segments": segment_rows,
                        "error": error,
                    }
                    print(f"ERROR: {error}", flush=True)
                append_jsonl(manifest_path, row)
                rows.append(row)

    write_json(
        metadata_root / "summary.json",
        {
            "metadata_root": str(metadata_root),
            "manifest_path": str(manifest_path),
            "sample_count": len([row for row in rows if row.get("error") is None]),
            "failed_count": len([row for row in rows if row.get("error") is not None]),
            "rows": rows,
        },
    )
    print(f"Wrote manifest: {manifest_path}", flush=True)
    print(f"Wrote summary: {metadata_root / 'summary.json'}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
