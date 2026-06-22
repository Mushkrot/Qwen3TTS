#!/usr/bin/env python3
"""Orchestrate Qwen3TTS voice training candidates and eval packs.

The module is intentionally standard-library only at import time. Heavy Qwen,
Torch, and audio dependencies are loaded only by the existing project scripts
when real mode invokes them as subprocesses.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import wave
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_BASE_MODEL = "Qwen/Qwen3-TTS-12Hz-0.6B-Base"
DEFAULT_TOKENIZER_MODEL = "Qwen/Qwen3-TTS-Tokenizer-12Hz"
DEFAULT_DEVICE = "cuda:0"
DEFAULT_RUN_NAME = "train_voice_candidates"
METRIC_EVENT_SAMPLE = "sample_metrics"
METRIC_EVENT_CHECKPOINT_SCORE = "checkpoint_score"
METRIC_EVENT_CHECKPOINT_GATE = "checkpoint_gate"
METRIC_EVENT_CANDIDATE_SELECTION = "candidate_selection"
METRIC_EVENT_CANDIDATE_REVIEW_EXPORT = "candidate_review_export"
METRIC_EVENT_EARLY_STOP_DECISION = "early_stop_decision"
METRIC_EVENT_RUN_STOP = "run_stop"
PCM_SAMPLE_RATE = 16_000
PCM_SILENCE_THRESHOLD = 500
DEFAULT_TEXT_MATCH_MODEL = "large-v3"
DEFAULT_TEXT_MATCH_DEVICE = "cuda"
DEFAULT_TEXT_MATCH_COMPUTE_TYPE = "float16"
DEFAULT_MIN_EPOCHS = 2
DEFAULT_MAX_EPOCHS = 6
DEFAULT_PATIENCE = 2
DEFAULT_TOP_CANDIDATES = 4
DEFAULT_CANDIDATE_FLOOR = 3
DEFAULT_EARLY_STOP_MIN_DELTA = 0.0
CANDIDATE_REVIEW_RANK_NAMES: tuple[str, ...] = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
STOP_REASON_MIN_EPOCHS_PENDING = "min_epochs_pending"
STOP_REASON_SCORE_IMPROVED = "score_improved"
STOP_REASON_PATIENCE_PENDING = "patience_pending"
STOP_REASON_PATIENCE_EXHAUSTED = "patience_exhausted"
STOP_REASON_QUALITY_DEGRADATION = "quality_degradation"
STOP_REASON_MAX_EPOCHS_REACHED = "max_epochs_reached"
STOP_REASON_NO_VIABLE_CHECKPOINT = "no_viable_checkpoint"
QUALITY_DEGRADATION_REJECT_REASONS: tuple[str, ...] = (
    "asr_text_mismatch",
    "audio_clipping",
    "duration_too_short",
    "duration_too_long",
    "pace_accelerated",
    "score_drop",
    "suspected_cut",
)
_TEXT_MATCH_MODELS: dict[tuple[str, str, str], object] = {}


@dataclass(frozen=True)
class MetricThresholds:
    duration_ratio_min: float = 0.70
    duration_ratio_max: float = 1.45
    pace_chars_per_sec_min: float = 7.0
    pace_chars_per_sec_max: float = 24.0
    rms_dbfs_min: float = -42.0
    rms_dbfs_max: float = -6.0
    clipping_ratio_max: float = 0.005
    leading_silence_ms_max: float = 700.0
    trailing_silence_ms_max: float = 900.0
    whisper_text_match_min: float = 0.82


@dataclass(frozen=True)
class MetricWeights:
    text_match: float = 20.0
    pace_duration: float = 25.0
    silence: float = 15.0
    audio_level: float = 10.0
    speaker_similarity: float = 20.0
    loss: float = 10.0


@dataclass(frozen=True)
class MetricBackends:
    metrics_mode: str = "auto"
    text_match_backend: str = "auto"
    speaker_similarity_backend: str = "off"


@dataclass(frozen=True)
class HardRejectThresholds:
    asr_text_match_min: float = 0.70
    pace_acceleration_ratio_max: float = 1.22
    clipping_ratio_max: float = 0.005
    duration_ratio_min: float = 0.70
    duration_ratio_max: float = 1.45
    suspected_cut_duration_ratio_max: float = 0.78
    suspected_cut_trailing_silence_ms_max: float = 90.0
    score_drop_max: float = 18.0


@dataclass(frozen=True)
class EarlyStopPolicy:
    min_epochs: int = DEFAULT_MIN_EPOCHS
    max_epochs: int = DEFAULT_MAX_EPOCHS
    patience: int = DEFAULT_PATIENCE
    min_delta: float = DEFAULT_EARLY_STOP_MIN_DELTA
    candidate_floor: int = DEFAULT_CANDIDATE_FLOOR
    top_candidates: int = DEFAULT_TOP_CANDIDATES


DEFAULT_METRIC_THRESHOLDS = MetricThresholds()
DEFAULT_METRIC_WEIGHTS = MetricWeights()
DEFAULT_METRIC_BACKENDS = MetricBackends()
DEFAULT_HARD_REJECT_THRESHOLDS = HardRejectThresholds()
DEFAULT_EARLY_STOP_POLICY = EarlyStopPolicy()


@dataclass(frozen=True)
class EvalPhrase:
    filename: str
    text: str
    language: str
    label: str


DEFAULT_EVAL_PHRASES: tuple[EvalPhrase, ...] = (
    EvalPhrase(
        filename="01_en_short.wav",
        text="She said she would be here by noon.",
        language="english",
        label="en_short",
    ),
    EvalPhrase(
        filename="02_en_long.wav",
        text=(
            "The old railway station was quiet in the morning, but by evening "
            "it was full of people waiting for the last train."
        ),
        language="english",
        label="en_long",
    ),
    EvalPhrase(
        filename="03_en_calm.wav",
        text="Take a slow breath, relax your shoulders, and speak with calm confidence.",
        language="english",
        label="en_calm",
    ),
    EvalPhrase(
        filename="04_ru_short.wav",
        text="Сегодня хороший день для спокойной и ясной речи.",
        language="russian",
        label="ru_short",
    ),
    EvalPhrase(
        filename="05_ru_long.wav",
        text=(
            "Когда голос звучит естественно, слушатель легко понимает каждую "
            "фразу и не отвлекается на шум или странные паузы."
        ),
        language="russian",
        label="ru_long",
    ),
)


@dataclass(frozen=True)
class RunPaths:
    run_dir: Path
    manifests_dir: Path
    prepared_manifest: Path
    logs_dir: Path
    metrics_jsonl: Path
    train_dir: Path
    checkpoints_dir: Path
    eval_dir: Path
    candidate_manifest: Path

    def epoch_run_dir(self, epoch: int) -> Path:
        return self.train_dir / f"epoch-{epoch}"

    def epoch_checkpoint_path(self, epoch: int) -> Path:
        return self.epoch_run_dir(epoch) / "checkpoint-epoch-0"

    def promoted_checkpoint_path(self, epoch: int) -> Path:
        return self.checkpoints_dir / f"epoch-{epoch}"

    def epoch_eval_dir(self, epoch: int) -> Path:
        return self.eval_dir / f"epoch-{epoch}"

    def command_log_path(self, stage: str, epoch: int | None = None) -> Path:
        suffix = f"epoch-{epoch}" if epoch is not None else "run"
        return self.logs_dir / f"{stage}-{suffix}.log"


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    log_path: Path | None = None


@dataclass(frozen=True)
class LossSummary:
    loss_last: float | None
    loss_min: float | None
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class SampleMetrics:
    epoch: int
    label: str
    output_path: str
    duration_seconds: float
    expected_duration_seconds: float
    duration_ratio: float
    pace_chars_per_sec: float
    pace_words_per_sec: float
    rms_dbfs: float
    clipping_ratio: float
    leading_silence_ms: float
    trailing_silence_ms: float
    whisper_text_match: float | None
    speaker_similarity: float | None
    warnings: tuple[str, ...]
    metric_backend: str

    def to_row(self) -> dict[str, object]:
        return {
            "event": METRIC_EVENT_SAMPLE,
            "epoch": self.epoch,
            "label": self.label,
            "output_path": self.output_path,
            "duration_seconds": self.duration_seconds,
            "expected_duration_seconds": self.expected_duration_seconds,
            "duration_ratio": self.duration_ratio,
            "pace_chars_per_sec": self.pace_chars_per_sec,
            "pace_words_per_sec": self.pace_words_per_sec,
            "rms_dbfs": self.rms_dbfs,
            "clipping_ratio": self.clipping_ratio,
            "leading_silence_ms": self.leading_silence_ms,
            "trailing_silence_ms": self.trailing_silence_ms,
            "whisper_text_match": self.whisper_text_match,
            "speaker_similarity": self.speaker_similarity,
            "warnings": list(self.warnings),
            "metric_backend": self.metric_backend,
        }


@dataclass(frozen=True)
class CheckpointScore:
    epoch: int
    checkpoint_path: str
    sample_count: int
    score: float
    metric_summary: dict[str, object]
    warnings: tuple[str, ...]

    def to_row(self) -> dict[str, object]:
        return {
            "event": METRIC_EVENT_CHECKPOINT_SCORE,
            "epoch": self.epoch,
            "checkpoint_path": self.checkpoint_path,
            "sample_count": self.sample_count,
            "score": self.score,
            "metric_summary": self.metric_summary,
            "warnings": list(self.warnings),
        }


@dataclass(frozen=True)
class CheckpointGate:
    epoch: int
    checkpoint_path: str
    hard_rejected: bool
    reject_reasons: tuple[str, ...]
    warning_reasons: tuple[str, ...]
    score: float
    metric_summary: dict[str, object]
    comparison: dict[str, object]

    def to_row(self) -> dict[str, object]:
        return {
            "event": METRIC_EVENT_CHECKPOINT_GATE,
            "epoch": self.epoch,
            "checkpoint_path": self.checkpoint_path,
            "hard_rejected": self.hard_rejected,
            "reject_reasons": list(self.reject_reasons),
            "warning_reasons": list(self.warning_reasons),
            "score": self.score,
            "metric_summary": self.metric_summary,
            "comparison": self.comparison,
        }


@dataclass(frozen=True)
class CandidateSelection:
    selected_epochs: tuple[int, ...]
    rejected_epochs: tuple[int, ...]
    limited: bool
    candidate_count: int
    rejected_count: int
    manifest_path: str

    def to_row(self) -> dict[str, object]:
        return {
            "event": METRIC_EVENT_CANDIDATE_SELECTION,
            "selected_epochs": list(self.selected_epochs),
            "rejected_epochs": list(self.rejected_epochs),
            "limited": self.limited,
            "candidate_count": self.candidate_count,
            "rejected_count": self.rejected_count,
            "manifest_path": self.manifest_path,
        }


@dataclass(frozen=True)
class CandidateReviewExport:
    review_dir: str
    ranking_path: str
    metrics_path: str
    candidate_count: int
    exported_epochs: tuple[int, ...]
    candidate_dirs: tuple[str, ...] = ()

    def to_row(self) -> dict[str, object]:
        return {
            "event": METRIC_EVENT_CANDIDATE_REVIEW_EXPORT,
            "review_dir": self.review_dir,
            "ranking_path": self.ranking_path,
            "metrics_path": self.metrics_path,
            "candidate_count": self.candidate_count,
            "exported_epochs": list(self.exported_epochs),
            "candidate_dirs": list(self.candidate_dirs),
        }

    def to_manifest(self) -> dict[str, object]:
        row = self.to_row()
        row.pop("event", None)
        return row


@dataclass(frozen=True)
class EarlyStopDecision:
    epoch: int
    should_stop: bool
    reason: str
    best_epoch: int | None
    best_score: float | None
    epochs_without_improvement: int
    min_epochs_reached: bool

    def to_row(self) -> dict[str, object]:
        return {
            "event": METRIC_EVENT_EARLY_STOP_DECISION,
            "epoch": self.epoch,
            "should_stop": self.should_stop,
            "reason": self.reason,
            "best_epoch": self.best_epoch,
            "best_score": self.best_score,
            "epochs_without_improvement": self.epochs_without_improvement,
            "min_epochs_reached": self.min_epochs_reached,
        }


@dataclass(frozen=True)
class RunStop:
    reason: str
    epoch: int
    best_epoch: int | None
    best_score: float | None
    epochs_completed: int

    def to_row(self) -> dict[str, object]:
        return {
            "event": METRIC_EVENT_RUN_STOP,
            "reason": self.reason,
            "epoch": self.epoch,
            "best_epoch": self.best_epoch,
            "best_score": self.best_score,
            "epochs_completed": self.epochs_completed,
        }


class OrchestrationError(RuntimeError):
    """Raised when a mandatory orchestration step fails."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_paths(output_root: Path, voice_name: str, run_name: str) -> RunPaths:
    run_dir = output_root / voice_name / run_name
    manifests_dir = run_dir / "manifests"
    return RunPaths(
        run_dir=run_dir,
        manifests_dir=manifests_dir,
        prepared_manifest=manifests_dir / "train_with_codes.jsonl",
        logs_dir=run_dir / "logs",
        metrics_jsonl=run_dir / "metrics.jsonl",
        train_dir=run_dir / "train",
        checkpoints_dir=run_dir / "checkpoints",
        eval_dir=run_dir / "eval",
        candidate_manifest=run_dir / "candidate_manifest.json",
    )


def candidate_review_rank_name(rank: int) -> str:
    if rank < 1:
        raise ValueError("candidate review rank must be >= 1")
    if rank <= len(CANDIDATE_REVIEW_RANK_NAMES):
        return CANDIDATE_REVIEW_RANK_NAMES[rank - 1]
    return str(rank)


def candidate_review_folder_name(rank: int, epoch: int) -> str:
    return f"candidate_{candidate_review_rank_name(rank)}_epoch{epoch}"


def default_candidate_review_root(args: argparse.Namespace, paths: RunPaths) -> Path:
    output_root = Path(args.output_root)
    if output_root.name == "runs":
        return output_root.parent / "samples" / args.voice_name / args.run_name / "candidate_review"
    return paths.run_dir / "candidate_review"


def resolve_candidate_review_root(args: argparse.Namespace, paths: RunPaths) -> Path:
    if args.candidate_review_root is not None:
        return Path(args.candidate_review_root)
    return default_candidate_review_root(args, paths)


def ensure_run_dirs(paths: RunPaths) -> None:
    for path in (
        paths.run_dir,
        paths.manifests_dir,
        paths.logs_dir,
        paths.train_dir,
        paths.checkpoints_dir,
        paths.eval_dir,
    ):
        path.mkdir(parents=True, exist_ok=True)


def append_metrics(target_metrics_path: Path, **row: object) -> None:
    target_metrics_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"ts": utc_now(), **row}
    with target_metrics_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def read_metrics(metrics_path: Path) -> list[dict[str, object]]:
    if not metrics_path.exists():
        return []
    with metrics_path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def project_python(root_dir: Path) -> str:
    candidate = root_dir / ".venv" / "bin" / "python"
    return str(candidate if candidate.exists() else Path(sys.executable))


def command_to_string(command: Sequence[str]) -> str:
    return " ".join(str(part) for part in command)


def rounded(value: float, digits: int = 4) -> float:
    return round(float(value), digits)


def clamp_score(value: float) -> float:
    return rounded(max(0.0, min(100.0, value)), 2)


def metric_thresholds_row(thresholds: MetricThresholds = DEFAULT_METRIC_THRESHOLDS) -> dict[str, float]:
    return asdict(thresholds)


def metric_weights_row(weights: MetricWeights = DEFAULT_METRIC_WEIGHTS) -> dict[str, float]:
    return asdict(weights)


def hard_reject_thresholds_row(
    thresholds: HardRejectThresholds = DEFAULT_HARD_REJECT_THRESHOLDS,
) -> dict[str, float]:
    return asdict(thresholds)


def hard_reject_thresholds_from_args(args: argparse.Namespace) -> HardRejectThresholds:
    return HardRejectThresholds(
        asr_text_match_min=args.hard_reject_text_match_min,
        pace_acceleration_ratio_max=args.hard_reject_pace_acceleration_max,
        clipping_ratio_max=args.hard_reject_clipping_ratio_max,
        duration_ratio_min=args.hard_reject_duration_ratio_min,
        duration_ratio_max=args.hard_reject_duration_ratio_max,
        suspected_cut_duration_ratio_max=args.hard_reject_suspected_cut_duration_ratio_max,
        suspected_cut_trailing_silence_ms_max=args.hard_reject_suspected_cut_trailing_silence_ms_max,
        score_drop_max=args.hard_reject_score_drop_max,
    )


def early_stop_policy_row(policy: EarlyStopPolicy = DEFAULT_EARLY_STOP_POLICY) -> dict[str, object]:
    return asdict(policy)


def early_stop_policy_from_args(args: argparse.Namespace) -> EarlyStopPolicy:
    return EarlyStopPolicy(
        min_epochs=args.min_epochs,
        max_epochs=args.max_epochs,
        patience=args.patience,
        min_delta=args.early_stop_min_delta,
        candidate_floor=args.candidate_floor,
        top_candidates=args.top_candidates,
    )


def resolve_backend_mode(requested: str, execution_mode: str, stub_value: str = "stub") -> str:
    if requested != "auto":
        return requested
    return stub_value if execution_mode == "stub" else "off"


def estimate_expected_duration_seconds(text: str) -> float:
    chars = len([char for char in text if not char.isspace()])
    return rounded(max(0.9, min(8.0, chars / 13.5)), 3)


def count_words(text: str) -> int:
    words = re.findall(r"[\w']+", text, flags=re.UNICODE)
    return len(words)


def text_match_ratio(expected: str, observed: str) -> float:
    expected_tokens = set(re.findall(r"[\w']+", expected.lower(), flags=re.UNICODE))
    observed_tokens = set(re.findall(r"[\w']+", observed.lower(), flags=re.UNICODE))
    if not expected_tokens:
        return 1.0
    if not observed_tokens:
        return 0.0
    return rounded(len(expected_tokens & observed_tokens) / len(expected_tokens), 4)


def sine_sample(index: int, sample_rate: int, frequency: float, amplitude: int) -> int:
    return int(amplitude * math.sin(2.0 * math.pi * frequency * (index / sample_rate)))


def write_stub_wav(output_path: Path, text: str, sample_rate: int = PCM_SAMPLE_RATE) -> None:
    expected_duration = estimate_expected_duration_seconds(text)
    leading_seconds = 0.18
    trailing_seconds = 0.22
    total_seconds = max(0.9, expected_duration)
    tone_seconds = max(0.2, total_seconds - leading_seconds - trailing_seconds)
    leading_frames = int(leading_seconds * sample_rate)
    tone_frames = int(tone_seconds * sample_rate)
    trailing_frames = int(trailing_seconds * sample_rate)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(output_path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        silence_frame = (0).to_bytes(2, "little", signed=True)
        wav_file.writeframes(silence_frame * leading_frames)
        frames = bytearray()
        for idx in range(tone_frames):
            frames.extend(sine_sample(idx, sample_rate, 220.0, 9000).to_bytes(2, "little", signed=True))
        wav_file.writeframes(bytes(frames))
        wav_file.writeframes(silence_frame * trailing_frames)


def read_pcm16_mono(path: Path) -> tuple[int, list[int]]:
    with wave.open(str(path), "rb") as wav_file:
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        sample_rate = wav_file.getframerate()
        frames = wav_file.readframes(wav_file.getnframes())
    if sample_width != 2:
        raise OrchestrationError(f"Only 16-bit PCM WAV is supported for metrics: {path}")
    samples: list[int] = []
    step = sample_width * channels
    for offset in range(0, len(frames), step):
        sample = int.from_bytes(frames[offset : offset + sample_width], "little", signed=True)
        samples.append(sample)
    return sample_rate, samples


def leading_silence_ms(samples: Sequence[int], sample_rate: int, threshold: int = PCM_SILENCE_THRESHOLD) -> float:
    silent = 0
    for sample in samples:
        if abs(sample) > threshold:
            break
        silent += 1
    return rounded((silent / sample_rate) * 1000.0, 2) if sample_rate else 0.0


def trailing_silence_ms(samples: Sequence[int], sample_rate: int, threshold: int = PCM_SILENCE_THRESHOLD) -> float:
    silent = 0
    for sample in reversed(samples):
        if abs(sample) > threshold:
            break
        silent += 1
    return rounded((silent / sample_rate) * 1000.0, 2) if sample_rate else 0.0


def rms_dbfs(samples: Sequence[int]) -> float:
    if not samples:
        return -120.0
    mean_square = sum(float(sample) * float(sample) for sample in samples) / len(samples)
    if mean_square <= 0.0:
        return -120.0
    rms = math.sqrt(mean_square)
    return rounded(20.0 * math.log10(rms / 32768.0), 3)


def clipping_ratio(samples: Sequence[int]) -> float:
    if not samples:
        return 0.0
    clipped = sum(1 for sample in samples if abs(sample) >= 32760)
    return rounded(clipped / len(samples), 6)


def parse_loss_values(log_path: Path) -> list[float]:
    if not log_path.exists():
        return []
    pattern = re.compile(r"Loss:\s*([0-9]+(?:\.[0-9]+)?)", flags=re.IGNORECASE)
    values: list[float] = []
    for line in log_path.read_text(encoding="utf-8", errors="replace").splitlines():
        for match in pattern.finditer(line):
            values.append(float(match.group(1)))
    return values


def loss_summary_for_epoch(paths: RunPaths, epoch: int) -> LossSummary:
    values = parse_loss_values(paths.command_log_path("train", epoch))
    if not values:
        return LossSummary(loss_last=None, loss_min=None, warnings=("missing_loss",))
    return LossSummary(loss_last=rounded(values[-1], 6), loss_min=rounded(min(values), 6), warnings=())


def language_code(language: str) -> str:
    normalized = language.lower().strip()
    if normalized in {"english", "en"}:
        return "en"
    if normalized in {"russian", "ru"}:
        return "ru"
    return normalized


def faster_whisper_model(args: argparse.Namespace) -> object:
    key = (args.text_match_model, args.text_match_device, args.text_match_compute_type)
    if key not in _TEXT_MATCH_MODELS:
        from faster_whisper import WhisperModel

        _TEXT_MATCH_MODELS[key] = WhisperModel(
            args.text_match_model,
            device=args.text_match_device,
            compute_type=args.text_match_compute_type,
        )
    return _TEXT_MATCH_MODELS[key]


def faster_whisper_text_match(
    args: argparse.Namespace,
    phrase: EvalPhrase,
    output_path: Path,
) -> tuple[float | None, tuple[str, ...]]:
    try:
        model = faster_whisper_model(args)
        segments, _info = model.transcribe(
            str(output_path),
            language=language_code(phrase.language),
            beam_size=args.text_match_beam_size,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
        )
        observed = " ".join(str(getattr(segment, "text", "")).strip() for segment in segments).strip()
        if not observed:
            return 0.0, ("whisper_text_empty",)
        return text_match_ratio(phrase.text, observed), ()
    except Exception as exc:
        return None, (f"whisper_text_match_error:{type(exc).__name__}",)


def text_match_for_phrase(
    args: argparse.Namespace,
    phrase: EvalPhrase,
    output_path: Path,
) -> tuple[float | None, tuple[str, ...]]:
    backend = resolve_backend_mode(args.text_match_backend, args.execution_mode)
    if backend == "stub":
        return text_match_ratio(phrase.text, phrase.text), ()
    if backend == "off":
        return None, ("whisper_text_match_unavailable",)
    if backend == "faster-whisper":
        return faster_whisper_text_match(args, phrase, output_path)
    return None, ("whisper_text_match_unavailable",)


def speaker_similarity_for_sample(args: argparse.Namespace) -> tuple[float | None, tuple[str, ...]]:
    if args.speaker_similarity_backend == "stub":
        return 0.92, ()
    return None, ("speaker_similarity_unavailable",)


def warnings_for_sample(
    metrics: dict[str, float | None],
    thresholds: MetricThresholds = DEFAULT_METRIC_THRESHOLDS,
) -> tuple[str, ...]:
    warnings: list[str] = []
    duration_ratio = metrics.get("duration_ratio")
    if isinstance(duration_ratio, float) and duration_ratio < thresholds.duration_ratio_min:
        warnings.append("duration_ratio_too_low")
    if isinstance(duration_ratio, float) and duration_ratio > thresholds.duration_ratio_max:
        warnings.append("duration_ratio_too_high")
    pace_chars = metrics.get("pace_chars_per_sec")
    if isinstance(pace_chars, float) and pace_chars < thresholds.pace_chars_per_sec_min:
        warnings.append("pace_too_slow")
    if isinstance(pace_chars, float) and pace_chars > thresholds.pace_chars_per_sec_max:
        warnings.append("pace_too_fast")
    rms_value = metrics.get("rms_dbfs")
    if isinstance(rms_value, float) and rms_value < thresholds.rms_dbfs_min:
        warnings.append("audio_too_quiet")
    if isinstance(rms_value, float) and rms_value > thresholds.rms_dbfs_max:
        warnings.append("audio_too_loud")
    clipping_value = metrics.get("clipping_ratio")
    if isinstance(clipping_value, float) and clipping_value > thresholds.clipping_ratio_max:
        warnings.append("clipping_detected")
    leading_value = metrics.get("leading_silence_ms")
    if isinstance(leading_value, float) and leading_value > thresholds.leading_silence_ms_max:
        warnings.append("leading_silence_too_long")
    trailing_value = metrics.get("trailing_silence_ms")
    if isinstance(trailing_value, float) and trailing_value > thresholds.trailing_silence_ms_max:
        warnings.append("trailing_silence_too_long")
    text_match = metrics.get("whisper_text_match")
    if isinstance(text_match, float) and text_match < thresholds.whisper_text_match_min:
        warnings.append("text_match_too_low")
    return tuple(warnings)


def compute_sample_metrics(
    args: argparse.Namespace,
    epoch: int,
    phrase: EvalPhrase,
    output_path: Path,
) -> SampleMetrics:
    metric_backend = resolve_backend_mode(args.metrics_mode, args.execution_mode, stub_value="audio")
    text_match, text_warnings = text_match_for_phrase(args, phrase, output_path)
    speaker_similarity, speaker_warnings = speaker_similarity_for_sample(args)
    if metric_backend == "off":
        warnings = tuple(sorted(set(("audio_metrics_disabled", *text_warnings, *speaker_warnings))))
        return SampleMetrics(
            epoch=epoch,
            label=phrase.label,
            output_path=str(output_path),
            duration_seconds=0.0,
            expected_duration_seconds=estimate_expected_duration_seconds(phrase.text),
            duration_ratio=0.0,
            pace_chars_per_sec=0.0,
            pace_words_per_sec=0.0,
            rms_dbfs=-120.0,
            clipping_ratio=0.0,
            leading_silence_ms=0.0,
            trailing_silence_ms=0.0,
            whisper_text_match=text_match,
            speaker_similarity=speaker_similarity,
            warnings=warnings,
            metric_backend=metric_backend,
        )

    try:
        sample_rate, samples = read_pcm16_mono(output_path)
        duration = len(samples) / sample_rate if sample_rate else 0.0
        expected = estimate_expected_duration_seconds(phrase.text)
        duration_ratio = duration / expected if expected else 0.0
        chars = len([char for char in phrase.text if not char.isspace()])
        words = count_words(phrase.text)
        base_metrics: dict[str, float | None] = {
            "duration_ratio": rounded(duration_ratio, 4),
            "pace_chars_per_sec": rounded(chars / duration, 4) if duration else 0.0,
            "pace_words_per_sec": rounded(words / duration, 4) if duration else 0.0,
            "rms_dbfs": rms_dbfs(samples),
            "clipping_ratio": clipping_ratio(samples),
            "leading_silence_ms": leading_silence_ms(samples, sample_rate),
            "trailing_silence_ms": trailing_silence_ms(samples, sample_rate),
            "whisper_text_match": text_match,
        }
        warning_values = list(warnings_for_sample(base_metrics))
        warning_values.extend(text_warnings)
        warning_values.extend(speaker_warnings)
        return SampleMetrics(
            epoch=epoch,
            label=phrase.label,
            output_path=str(output_path),
            duration_seconds=rounded(duration, 4),
            expected_duration_seconds=expected,
            duration_ratio=base_metrics["duration_ratio"] or 0.0,
            pace_chars_per_sec=base_metrics["pace_chars_per_sec"] or 0.0,
            pace_words_per_sec=base_metrics["pace_words_per_sec"] or 0.0,
            rms_dbfs=base_metrics["rms_dbfs"] or -120.0,
            clipping_ratio=base_metrics["clipping_ratio"] or 0.0,
            leading_silence_ms=base_metrics["leading_silence_ms"] or 0.0,
            trailing_silence_ms=base_metrics["trailing_silence_ms"] or 0.0,
            whisper_text_match=text_match,
            speaker_similarity=speaker_similarity,
            warnings=tuple(sorted(set(warning_values))),
            metric_backend=metric_backend,
        )
    except Exception as exc:
        warnings = tuple(sorted(set(("audio_metrics_unavailable", *text_warnings, *speaker_warnings))))
        return SampleMetrics(
            epoch=epoch,
            label=phrase.label,
            output_path=str(output_path),
            duration_seconds=0.0,
            expected_duration_seconds=estimate_expected_duration_seconds(phrase.text),
            duration_ratio=0.0,
            pace_chars_per_sec=0.0,
            pace_words_per_sec=0.0,
            rms_dbfs=-120.0,
            clipping_ratio=0.0,
            leading_silence_ms=0.0,
            trailing_silence_ms=0.0,
            whisper_text_match=text_match,
            speaker_similarity=speaker_similarity,
            warnings=(*warnings, f"audio_metric_error:{type(exc).__name__}"),
            metric_backend=metric_backend,
        )


def mean(values: Sequence[float]) -> float | None:
    return sum(values) / len(values) if values else None


def metric_rows_for_epoch(metrics_path: Path, event_name: str, epoch: int) -> list[dict[str, object]]:
    rows = read_metrics(metrics_path)
    return [row for row in rows if row.get("event") == event_name and row.get("epoch") == epoch]


def event_rows(metrics_path: Path, event_name: str) -> list[dict[str, object]]:
    rows = read_metrics(metrics_path)
    return [row for row in rows if row.get("event") == event_name]


def numeric(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None


def add_penalty(score: float, warnings: list[str], warning: str, penalty: float) -> float:
    warnings.append(warning)
    return score - penalty


def score_checkpoint(
    paths: RunPaths,
    epoch: int,
    checkpoint_path: Path,
    thresholds: MetricThresholds = DEFAULT_METRIC_THRESHOLDS,
) -> CheckpointScore:
    sample_rows = metric_rows_for_epoch(paths.metrics_jsonl, METRIC_EVENT_SAMPLE, epoch)
    loss_summary = loss_summary_for_epoch(paths, epoch)
    warnings: list[str] = []
    for row in sample_rows:
        warnings.extend(str(item) for item in row.get("warnings", []) if item)
    warnings.extend(loss_summary.warnings)

    duration_ratios = [float(row["duration_ratio"]) for row in sample_rows if isinstance(row.get("duration_ratio"), (int, float))]
    pace_chars = [float(row["pace_chars_per_sec"]) for row in sample_rows if isinstance(row.get("pace_chars_per_sec"), (int, float))]
    rms_values = [float(row["rms_dbfs"]) for row in sample_rows if isinstance(row.get("rms_dbfs"), (int, float))]
    clipping_values = [float(row["clipping_ratio"]) for row in sample_rows if isinstance(row.get("clipping_ratio"), (int, float))]
    leading_values = [float(row["leading_silence_ms"]) for row in sample_rows if isinstance(row.get("leading_silence_ms"), (int, float))]
    trailing_values = [float(row["trailing_silence_ms"]) for row in sample_rows if isinstance(row.get("trailing_silence_ms"), (int, float))]
    text_matches = [
        float(row["whisper_text_match"])
        for row in sample_rows
        if isinstance(row.get("whisper_text_match"), (int, float))
    ]
    speaker_values = [
        float(row["speaker_similarity"])
        for row in sample_rows
        if isinstance(row.get("speaker_similarity"), (int, float))
    ]

    summary: dict[str, object] = {
        "duration_ratio_mean": rounded(mean(duration_ratios) or 0.0, 4),
        "pace_chars_per_sec_mean": rounded(mean(pace_chars) or 0.0, 4),
        "rms_dbfs_mean": rounded(mean(rms_values) or -120.0, 4),
        "clipping_ratio_max": rounded(max(clipping_values) if clipping_values else 0.0, 6),
        "leading_silence_ms_max": rounded(max(leading_values) if leading_values else 0.0, 2),
        "trailing_silence_ms_max": rounded(max(trailing_values) if trailing_values else 0.0, 2),
        "whisper_text_match_mean": rounded(mean(text_matches) or 0.0, 4) if text_matches else None,
        "speaker_similarity_mean": rounded(mean(speaker_values) or 0.0, 4) if speaker_values else None,
        "loss_last": loss_summary.loss_last,
        "loss_min": loss_summary.loss_min,
    }

    score = 100.0
    if not sample_rows:
        score = add_penalty(score, warnings, "missing_sample_metrics", 60.0)
    if summary["duration_ratio_mean"] < thresholds.duration_ratio_min:
        score = add_penalty(score, warnings, "duration_ratio_too_low", 12.0)
    if summary["duration_ratio_mean"] > thresholds.duration_ratio_max:
        score = add_penalty(score, warnings, "duration_ratio_too_high", 12.0)
    if summary["pace_chars_per_sec_mean"] < thresholds.pace_chars_per_sec_min:
        score = add_penalty(score, warnings, "pace_too_slow", 10.0)
    if summary["pace_chars_per_sec_mean"] > thresholds.pace_chars_per_sec_max:
        score = add_penalty(score, warnings, "pace_too_fast", 10.0)
    if summary["rms_dbfs_mean"] < thresholds.rms_dbfs_min:
        score = add_penalty(score, warnings, "audio_too_quiet", 8.0)
    if summary["rms_dbfs_mean"] > thresholds.rms_dbfs_max:
        score = add_penalty(score, warnings, "audio_too_loud", 8.0)
    if summary["clipping_ratio_max"] > thresholds.clipping_ratio_max:
        score = add_penalty(score, warnings, "clipping_detected", 15.0)
    if summary["leading_silence_ms_max"] > thresholds.leading_silence_ms_max:
        score = add_penalty(score, warnings, "leading_silence_too_long", 8.0)
    if summary["trailing_silence_ms_max"] > thresholds.trailing_silence_ms_max:
        score = add_penalty(score, warnings, "trailing_silence_too_long", 8.0)
    text_match_mean = summary["whisper_text_match_mean"]
    if text_match_mean is None:
        score = add_penalty(score, warnings, "whisper_text_match_unavailable", 5.0)
    elif text_match_mean < thresholds.whisper_text_match_min:
        score = add_penalty(score, warnings, "text_match_too_low", 15.0)
    if summary["speaker_similarity_mean"] is None:
        score = add_penalty(score, warnings, "speaker_similarity_unavailable", 3.0)
    if loss_summary.loss_last is None:
        score = add_penalty(score, warnings, "missing_loss", 2.0)

    return CheckpointScore(
        epoch=epoch,
        checkpoint_path=str(checkpoint_path),
        sample_count=len(sample_rows),
        score=clamp_score(score),
        metric_summary=summary,
        warnings=tuple(sorted(set(warnings))),
    )


def append_checkpoint_score(paths: RunPaths, epoch: int, checkpoint_path: Path) -> CheckpointScore:
    score = score_checkpoint(paths, epoch, checkpoint_path)
    append_metrics(paths.metrics_jsonl, **score.to_row())
    return score


def previous_viable_gates(paths: RunPaths, epoch: int) -> list[dict[str, object]]:
    gates = event_rows(paths.metrics_jsonl, METRIC_EVENT_CHECKPOINT_GATE)
    return [
        row
        for row in gates
        if isinstance(row.get("epoch"), int)
        and row["epoch"] < epoch
        and row.get("hard_rejected") is False
    ]


def evaluate_checkpoint_gate(
    args: argparse.Namespace,
    paths: RunPaths,
    checkpoint_score: CheckpointScore,
    thresholds: HardRejectThresholds | None = None,
) -> CheckpointGate:
    thresholds = thresholds or hard_reject_thresholds_from_args(args)
    summary = checkpoint_score.metric_summary
    reject_reasons: list[str] = []
    warning_reasons = list(checkpoint_score.warnings)
    comparison: dict[str, object] = {
        "previous_viable_epoch": None,
        "previous_viable_score": None,
        "previous_viable_pace_chars_per_sec_mean": None,
        "pace_acceleration_ratio": None,
        "score_drop": None,
    }

    text_match = numeric(summary.get("whisper_text_match_mean"))
    if text_match is not None and text_match < thresholds.asr_text_match_min:
        reject_reasons.append("asr_text_mismatch")

    clipping = numeric(summary.get("clipping_ratio_max"))
    if clipping is not None and clipping > thresholds.clipping_ratio_max:
        reject_reasons.append("audio_clipping")

    duration_ratio = numeric(summary.get("duration_ratio_mean"))
    if duration_ratio is not None and duration_ratio < thresholds.duration_ratio_min:
        reject_reasons.append("duration_too_short")
    if duration_ratio is not None and duration_ratio > thresholds.duration_ratio_max:
        reject_reasons.append("duration_too_long")

    trailing_silence = numeric(summary.get("trailing_silence_ms_max"))
    if (
        duration_ratio is not None
        and trailing_silence is not None
        and duration_ratio <= thresholds.suspected_cut_duration_ratio_max
        and trailing_silence <= thresholds.suspected_cut_trailing_silence_ms_max
    ):
        reject_reasons.append("suspected_cut")

    prior_gates = previous_viable_gates(paths, checkpoint_score.epoch)
    if prior_gates:
        previous = prior_gates[-1]
        previous_summary = previous.get("metric_summary")
        if isinstance(previous_summary, dict):
            previous_pace = numeric(previous_summary.get("pace_chars_per_sec_mean"))
            current_pace = numeric(summary.get("pace_chars_per_sec_mean"))
            if previous_pace and current_pace:
                pace_ratio = current_pace / previous_pace
                comparison["previous_viable_pace_chars_per_sec_mean"] = rounded(previous_pace, 4)
                comparison["pace_acceleration_ratio"] = rounded(pace_ratio, 4)
                if pace_ratio > thresholds.pace_acceleration_ratio_max:
                    reject_reasons.append("pace_accelerated")
        previous_score = numeric(previous.get("score"))
        if previous_score is not None:
            score_drop = previous_score - checkpoint_score.score
            comparison["previous_viable_epoch"] = previous.get("epoch")
            comparison["previous_viable_score"] = rounded(previous_score, 4)
            comparison["score_drop"] = rounded(score_drop, 4)
            if score_drop > thresholds.score_drop_max:
                reject_reasons.append("score_drop")

    return CheckpointGate(
        epoch=checkpoint_score.epoch,
        checkpoint_path=checkpoint_score.checkpoint_path,
        hard_rejected=bool(reject_reasons),
        reject_reasons=tuple(sorted(set(reject_reasons))),
        warning_reasons=tuple(sorted(set(warning_reasons))),
        score=checkpoint_score.score,
        metric_summary=summary,
        comparison=comparison,
    )


def append_checkpoint_gate(
    args: argparse.Namespace,
    paths: RunPaths,
    checkpoint_score: CheckpointScore,
) -> CheckpointGate:
    gate = evaluate_checkpoint_gate(args, paths, checkpoint_score)
    append_metrics(paths.metrics_jsonl, **gate.to_row())
    return gate


def best_viable_gate_state(
    gate_rows: Sequence[dict[str, object]],
    min_delta: float,
) -> tuple[int | None, float | None, int]:
    best_epoch: int | None = None
    best_score: float | None = None
    epochs_without_improvement = 0
    for row in gate_rows:
        if row.get("hard_rejected") is not False:
            continue
        score = numeric(row.get("score"))
        if score is None:
            continue
        epoch = int(row["epoch"]) if isinstance(row.get("epoch"), int) else None
        if best_score is None or score > best_score + min_delta:
            best_score = score
            best_epoch = epoch
            epochs_without_improvement = 0
        else:
            epochs_without_improvement += 1
    return best_epoch, rounded(best_score, 4) if best_score is not None else None, epochs_without_improvement


def gate_has_quality_degradation(row: dict[str, object]) -> bool:
    reject_reasons = row.get("reject_reasons", [])
    if not isinstance(reject_reasons, list):
        return False
    return any(str(reason) in QUALITY_DEGRADATION_REJECT_REASONS for reason in reject_reasons)


def evaluate_early_stop_decision(
    args: argparse.Namespace,
    paths: RunPaths,
    current_gate: CheckpointGate | dict[str, object] | None = None,
) -> EarlyStopDecision:
    policy = early_stop_policy_from_args(args)
    gate_rows = sorted_gate_rows(paths)
    if current_gate is None:
        if not gate_rows:
            return EarlyStopDecision(
                epoch=-1,
                should_stop=False,
                reason=STOP_REASON_NO_VIABLE_CHECKPOINT,
                best_epoch=None,
                best_score=None,
                epochs_without_improvement=0,
                min_epochs_reached=False,
            )
        current_row = gate_rows[-1]
    elif isinstance(current_gate, CheckpointGate):
        current_row = current_gate.to_row()
    else:
        current_row = current_gate
    current_epoch = int(current_row["epoch"]) if isinstance(current_row.get("epoch"), int) else 0
    completed_epochs = current_epoch + 1
    min_epochs_reached = completed_epochs >= policy.min_epochs
    best_epoch, best_score, epochs_without_improvement = best_viable_gate_state(
        gate_rows,
        policy.min_delta,
    )

    should_stop = False
    if not min_epochs_reached:
        reason = STOP_REASON_MIN_EPOCHS_PENDING
    elif current_row.get("hard_rejected") is True and gate_has_quality_degradation(current_row):
        should_stop = True
        reason = STOP_REASON_QUALITY_DEGRADATION
    elif best_epoch is not None and epochs_without_improvement >= policy.patience:
        should_stop = True
        reason = STOP_REASON_PATIENCE_EXHAUSTED
    elif completed_epochs >= policy.max_epochs:
        should_stop = True
        reason = STOP_REASON_MAX_EPOCHS_REACHED
    elif best_epoch is None:
        reason = STOP_REASON_NO_VIABLE_CHECKPOINT
    elif epochs_without_improvement > 0:
        reason = STOP_REASON_PATIENCE_PENDING
    else:
        reason = STOP_REASON_SCORE_IMPROVED

    return EarlyStopDecision(
        epoch=current_epoch,
        should_stop=should_stop,
        reason=reason,
        best_epoch=best_epoch,
        best_score=best_score,
        epochs_without_improvement=epochs_without_improvement,
        min_epochs_reached=min_epochs_reached,
    )


def append_early_stop_decision(
    args: argparse.Namespace,
    paths: RunPaths,
    current_gate: CheckpointGate,
) -> EarlyStopDecision:
    decision = evaluate_early_stop_decision(args, paths, current_gate)
    append_metrics(paths.metrics_jsonl, **decision.to_row())
    return decision


def run_stop_from_decision(decision: EarlyStopDecision) -> RunStop:
    return RunStop(
        reason=decision.reason,
        epoch=decision.epoch,
        best_epoch=decision.best_epoch,
        best_score=decision.best_score,
        epochs_completed=max(0, decision.epoch + 1),
    )


def append_run_stop(paths: RunPaths, decision: EarlyStopDecision) -> RunStop:
    stop = run_stop_from_decision(decision)
    append_metrics(paths.metrics_jsonl, **stop.to_row())
    return stop


def sorted_gate_rows(paths: RunPaths) -> list[dict[str, object]]:
    rows = event_rows(paths.metrics_jsonl, METRIC_EVENT_CHECKPOINT_GATE)
    return sorted(
        rows,
        key=lambda row: int(row["epoch"]) if isinstance(row.get("epoch"), int) else 0,
    )


def eval_dir_from_checkpoint_path(checkpoint_path: object, epoch: int) -> str | None:
    if not checkpoint_path:
        return None
    try:
        run_dir = Path(str(checkpoint_path)).parents[2]
    except IndexError:
        return None
    return str(run_dir / "eval" / f"epoch-{epoch}")


def candidate_entry_from_gate(row: dict[str, object], rank: int | None = None) -> dict[str, object]:
    epoch = int(row["epoch"]) if isinstance(row.get("epoch"), int) else 0
    entry: dict[str, object] = {
        "epoch": epoch,
        "checkpoint_path": row.get("checkpoint_path"),
        "eval_dir": eval_dir_from_checkpoint_path(row.get("checkpoint_path"), epoch),
        "score": row.get("score"),
        "reject_reasons": row.get("reject_reasons", []),
        "warning_reasons": row.get("warning_reasons", []),
        "metric_summary": row.get("metric_summary", {}),
    }
    if rank is not None:
        entry["rank"] = rank
        entry["label"] = candidate_review_folder_name(rank, epoch)
    return entry


def candidate_sort_key(row: dict[str, object]) -> tuple[float, int, int]:
    score = numeric(row.get("score")) or 0.0
    warnings = row.get("warning_reasons", [])
    warning_count = len(warnings) if isinstance(warnings, list) else 0
    epoch = int(row["epoch"]) if isinstance(row.get("epoch"), int) else 0
    return (-score, warning_count, epoch)


def select_candidate_rows(args: argparse.Namespace, paths: RunPaths) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    gate_rows = sorted_gate_rows(paths)
    viable = [row for row in gate_rows if row.get("hard_rejected") is False]
    rejected = [row for row in gate_rows if row.get("hard_rejected") is True]
    selected = sorted(viable, key=candidate_sort_key)[: args.top_candidates]
    return selected, rejected


def latest_event_row(paths: RunPaths, event_name: str) -> dict[str, object] | None:
    rows = event_rows(paths.metrics_jsonl, event_name)
    return rows[-1] if rows else None


def stop_summary_from_metrics(paths: RunPaths) -> dict[str, object] | None:
    row = latest_event_row(paths, METRIC_EVENT_RUN_STOP)
    if row is None:
        return None
    return {
        "reason": row.get("reason"),
        "epoch": row.get("epoch"),
        "best_epoch": row.get("best_epoch"),
        "best_score": row.get("best_score"),
        "epochs_completed": row.get("epochs_completed"),
    }


def write_candidate_manifest(
    args: argparse.Namespace,
    paths: RunPaths,
    selected_rows: Sequence[dict[str, object]],
    rejected_rows: Sequence[dict[str, object]],
) -> dict[str, object]:
    candidates = [
        candidate_entry_from_gate(row, rank=index)
        for index, row in enumerate(selected_rows, start=1)
    ]
    rejected = [candidate_entry_from_gate(row) for row in rejected_rows]
    limited_reasons: list[str] = []
    if len(candidates) < args.candidate_floor:
        limited_reasons.append("candidate_count_below_floor")
    manifest: dict[str, object] = {
        "generated_at": utc_now(),
        "voice_name": args.voice_name,
        "run_name": args.run_name,
        "status": "limited" if limited_reasons else "ok",
        "top_candidates": args.top_candidates,
        "candidate_floor": args.candidate_floor,
        "candidate_count": len(candidates),
        "rejected_count": len(rejected),
        "limited_reasons": limited_reasons,
        "stop_summary": stop_summary_from_metrics(paths),
        "candidates": candidates,
        "rejected_checkpoints": rejected,
    }
    paths.candidate_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return manifest


def load_candidate_manifest(paths: RunPaths) -> dict[str, object]:
    if not paths.candidate_manifest.exists():
        raise OrchestrationError(f"candidate manifest not found: {paths.candidate_manifest}")
    manifest = json.loads(paths.candidate_manifest.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise OrchestrationError(f"candidate manifest is not an object: {paths.candidate_manifest}")
    return manifest


def candidate_list_from_manifest(manifest: dict[str, object]) -> list[dict[str, object]]:
    candidates = manifest.get("candidates", [])
    if not isinstance(candidates, list):
        raise OrchestrationError("candidate_manifest.json candidates must be a list")
    result: list[dict[str, object]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise OrchestrationError("candidate_manifest.json contains a non-object candidate")
        result.append(candidate)
    return result


def list_candidate_eval_sources(candidate: dict[str, object]) -> list[Path]:
    epoch = int(candidate["epoch"]) if isinstance(candidate.get("epoch"), int) else 0
    eval_dir_raw = candidate.get("eval_dir")
    if not eval_dir_raw:
        raise OrchestrationError(f"candidate epoch {epoch} has no eval_dir")
    eval_dir = Path(str(eval_dir_raw))
    sources = [eval_dir / phrase.filename for phrase in DEFAULT_EVAL_PHRASES]
    missing = [path for path in sources if not path.exists()]
    if missing:
        missing_text = ", ".join(str(path) for path in missing)
        raise OrchestrationError(f"missing selected eval audio for epoch {epoch}: {missing_text}")
    return sources


def copy_candidate_review_metrics(paths: RunPaths, metrics_path: Path) -> None:
    if not paths.metrics_jsonl.exists():
        raise OrchestrationError(f"metrics jsonl not found: {paths.metrics_jsonl}")
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    if metrics_path != paths.metrics_jsonl:
        shutil.copy2(paths.metrics_jsonl, metrics_path)


def candidate_review_risk_text(candidate: dict[str, object]) -> str:
    warnings = candidate.get("warning_reasons", [])
    rejects = candidate.get("reject_reasons", [])
    risks: list[str] = []
    if isinstance(warnings, list):
        risks.extend(str(item) for item in warnings)
    if isinstance(rejects, list):
        risks.extend(f"reject:{item}" for item in rejects)
    return ", ".join(risks) if risks else "none"


def write_candidate_review_ranking(
    review_root: Path,
    ranking_path: Path,
    metrics_path: Path,
    manifest: dict[str, object],
    candidates: Sequence[dict[str, object]],
    copied_audio: dict[int, list[Path]],
) -> None:
    limited_reasons = manifest.get("limited_reasons", [])
    if not isinstance(limited_reasons, list):
        limited_reasons = []
    lines = [
        "# Candidate Review Ranking",
        "",
        f"Review directory: `{review_root}`",
        f"Metrics copy: `{metrics_path}`",
        f"Candidate count: {len(candidates)}",
        f"Candidate floor: {manifest.get('candidate_floor')}",
        f"Manifest status: {manifest.get('status')}",
        "Limited reasons: " + (", ".join(str(item) for item in limited_reasons) if limited_reasons else "none"),
        "",
    ]
    if not candidates:
        lines.extend(
            [
                "No viable candidates were selected.",
                "",
                "Risks/warnings: no checkpoint passed hard reject gates.",
            ]
        )
    for candidate in candidates:
        epoch = int(candidate["epoch"]) if isinstance(candidate.get("epoch"), int) else 0
        rank = int(candidate["rank"]) if isinstance(candidate.get("rank"), int) else 1
        rank_name = candidate_review_rank_name(rank)
        score = candidate.get("score")
        checkpoint_path = candidate.get("checkpoint_path")
        lines.extend(
            [
                f"## Candidate {rank_name} (epoch {epoch})",
                "",
                f"- Rank: {rank}",
                f"- Checkpoint: `{checkpoint_path}`",
                f"- Score: {score}",
                "- Why selected: selected from non-rejected checkpoints by score and warning count.",
                f"- Risks/warnings: {candidate_review_risk_text(candidate)}",
                "- Audio to listen:",
            ]
        )
        for audio_path in copied_audio.get(epoch, []):
            lines.append(f"  - `{audio_path.relative_to(review_root)}`")
        lines.append("")
    ranking_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def export_candidate_review_pack(args: argparse.Namespace, paths: RunPaths) -> CandidateReviewExport:
    manifest = load_candidate_manifest(paths)
    candidates = candidate_list_from_manifest(manifest)
    candidate_sources = [(candidate, list_candidate_eval_sources(candidate)) for candidate in candidates]
    review_root = resolve_candidate_review_root(args, paths)
    review_root.mkdir(parents=True, exist_ok=True)
    metrics_path = review_root / "metrics.jsonl"
    ranking_path = review_root / "ranking.md"
    copied_audio: dict[int, list[Path]] = {}
    candidate_dirs: list[Path] = []
    exported_epochs: list[int] = []

    for candidate, sources in candidate_sources:
        epoch = int(candidate["epoch"]) if isinstance(candidate.get("epoch"), int) else 0
        rank = int(candidate["rank"]) if isinstance(candidate.get("rank"), int) else len(candidate_dirs) + 1
        folder_name = str(candidate.get("label") or candidate_review_folder_name(rank, epoch))
        candidate_dir = review_root / folder_name
        candidate_dir.mkdir(parents=True, exist_ok=True)
        copied_audio[epoch] = []
        for source in sources:
            target = candidate_dir / source.name
            shutil.copy2(source, target)
            copied_audio[epoch].append(target)
        candidate_dirs.append(candidate_dir)
        exported_epochs.append(epoch)

    write_candidate_review_ranking(review_root, ranking_path, metrics_path, manifest, candidates, copied_audio)
    export = CandidateReviewExport(
        review_dir=str(review_root),
        ranking_path=str(ranking_path),
        metrics_path=str(metrics_path),
        candidate_count=len(candidates),
        exported_epochs=tuple(exported_epochs),
        candidate_dirs=tuple(str(path) for path in candidate_dirs),
    )
    manifest["candidate_review"] = export.to_manifest()
    paths.candidate_manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    append_metrics(paths.metrics_jsonl, **export.to_row())
    copy_candidate_review_metrics(paths, metrics_path)
    return export


def append_candidate_selection(args: argparse.Namespace, paths: RunPaths) -> CandidateSelection:
    selected_rows, rejected_rows = select_candidate_rows(args, paths)
    manifest = write_candidate_manifest(args, paths, selected_rows, rejected_rows)
    selection = CandidateSelection(
        selected_epochs=tuple(int(row["epoch"]) for row in selected_rows if isinstance(row.get("epoch"), int)),
        rejected_epochs=tuple(int(row["epoch"]) for row in rejected_rows if isinstance(row.get("epoch"), int)),
        limited=manifest["status"] == "limited",
        candidate_count=int(manifest["candidate_count"]),
        rejected_count=int(manifest["rejected_count"]),
        manifest_path=str(paths.candidate_manifest),
    )
    append_metrics(paths.metrics_jsonl, **selection.to_row())
    return selection


def build_prepare_command(args: argparse.Namespace, paths: RunPaths) -> list[str]:
    return [
        "bash",
        str(args.prepare_command),
        str(args.train_raw_jsonl),
        str(paths.prepared_manifest),
    ]


def build_train_command(
    args: argparse.Namespace,
    paths: RunPaths,
    epoch: int,
    init_model_path: str,
) -> tuple[list[str], dict[str, str]]:
    output_dir = paths.epoch_run_dir(epoch)
    command = [
        "bash",
        str(args.train_command),
        str(paths.prepared_manifest),
        str(output_dir),
    ]
    env = os.environ.copy()
    env.update(
        {
            "INIT_MODEL_PATH": init_model_path,
            "NUM_EPOCHS": "1",
            "SPEAKER_NAME": args.speaker_name,
            "BATCH_SIZE": str(args.batch_size),
            "LR": str(args.learning_rate),
        }
    )
    return command, env


def build_infer_command(
    args: argparse.Namespace,
    checkpoint_path: Path,
    phrase: EvalPhrase,
    output_path: Path,
) -> list[str]:
    return [
        str(args.python_executable),
        str(args.infer_script),
        "--checkpoint",
        str(checkpoint_path),
        "--speaker",
        args.speaker_name,
        "--text",
        phrase.text,
        "--language",
        phrase.language,
        "--output_wav",
        str(output_path),
        "--device",
        args.device,
    ]


def run_command(
    command: Sequence[str],
    log_path: Path,
    env: dict[str, str] | None = None,
) -> CommandResult:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as log_file:
        log_file.write(f"$ {command_to_string(command)}\n")
        log_file.flush()
        completed = subprocess.run(
            list(command),
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
            env=env,
            check=False,
        )
    return CommandResult(command=list(command), returncode=completed.returncode, log_path=log_path)


def write_stub_prepared_manifest(input_manifest: Path, output_manifest: Path) -> None:
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    if not input_manifest.exists():
        raise OrchestrationError(f"Missing train_raw_jsonl: {input_manifest}")
    with input_manifest.open("r", encoding="utf-8") as src, output_manifest.open(
        "w", encoding="utf-8"
    ) as dst:
        for line_number, line in enumerate(src, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError:
                row = {"text": stripped}
            row.setdefault("audio", f"stub_audio_{line_number}.wav")
            row.setdefault("ref_audio", row["audio"])
            row["audio_codes"] = [0, 1, 2, 3]
            dst.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_stub_checkpoint(checkpoint_path: Path, epoch: int, init_model_path: str) -> None:
    checkpoint_path.mkdir(parents=True, exist_ok=True)
    marker = checkpoint_path / "STUB_CHECKPOINT.txt"
    marker.write_text(
        f"stub checkpoint for epoch {epoch}\ninit_model_path={init_model_path}\n",
        encoding="utf-8",
    )


def promote_checkpoint(observed_checkpoint: Path, promoted_checkpoint: Path) -> None:
    promoted_checkpoint.parent.mkdir(parents=True, exist_ok=True)
    if promoted_checkpoint.exists() or promoted_checkpoint.is_symlink():
        if promoted_checkpoint.is_dir() and not promoted_checkpoint.is_symlink():
            shutil.rmtree(promoted_checkpoint)
        else:
            promoted_checkpoint.unlink()
    try:
        relative_target = os.path.relpath(observed_checkpoint, promoted_checkpoint.parent)
        promoted_checkpoint.symlink_to(relative_target, target_is_directory=True)
    except OSError:
        shutil.copytree(observed_checkpoint, promoted_checkpoint)


def run_prepare(args: argparse.Namespace, paths: RunPaths) -> None:
    started_at = utc_now()
    append_metrics(
        paths.metrics_jsonl,
        event="prepare_start",
        started_at=started_at,
        train_raw_jsonl=str(args.train_raw_jsonl),
        prepared_manifest=str(paths.prepared_manifest),
        mode=args.execution_mode,
    )
    if args.execution_mode == "stub":
        write_stub_prepared_manifest(args.train_raw_jsonl, paths.prepared_manifest)
        append_metrics(
            paths.metrics_jsonl,
            event="prepare_end",
            status="ok",
            returncode=0,
            started_at=started_at,
            finished_at=utc_now(),
            prepared_manifest=str(paths.prepared_manifest),
            mode="stub",
        )
        return
    command = build_prepare_command(args, paths)
    result = run_command(command, paths.command_log_path("prepare"))
    append_metrics(
        paths.metrics_jsonl,
        event="prepare_end",
        status="ok" if result.returncode == 0 else "failed",
        returncode=result.returncode,
        started_at=started_at,
        finished_at=utc_now(),
        command=result.command,
        log_path=str(result.log_path),
        prepared_manifest=str(paths.prepared_manifest),
    )
    if result.returncode != 0:
        raise OrchestrationError(f"prepare_data failed with exit {result.returncode}")


def resolve_init_model_path(args: argparse.Namespace, paths: RunPaths, epoch: int) -> str:
    if epoch == 0:
        return args.base_model
    previous = paths.promoted_checkpoint_path(epoch - 1)
    if previous.exists() or previous.is_symlink():
        return str(previous)
    fallback = paths.epoch_checkpoint_path(epoch - 1)
    if fallback.exists():
        return str(fallback)
    raise OrchestrationError(
        "Cannot continue epoch "
        f"{epoch}: previous checkpoint for epoch {epoch - 1} was not found. "
        "Run earlier epochs first or pass a valid output directory."
    )


def run_train_epoch(args: argparse.Namespace, paths: RunPaths, epoch: int) -> Path:
    init_model_path = resolve_init_model_path(args, paths, epoch)
    started_at = utc_now()
    append_metrics(
        paths.metrics_jsonl,
        event="train_start",
        started_at=started_at,
        epoch=epoch,
        init_model_path=init_model_path,
        mode=args.execution_mode,
    )
    if args.execution_mode == "stub":
        observed_checkpoint = paths.epoch_checkpoint_path(epoch)
        write_stub_checkpoint(observed_checkpoint, epoch, init_model_path)
        promote_checkpoint(observed_checkpoint, paths.promoted_checkpoint_path(epoch))
        append_metrics(
            paths.metrics_jsonl,
            event="train_end",
            status="ok",
            returncode=0,
            started_at=started_at,
            finished_at=utc_now(),
            epoch=epoch,
            init_model_path=init_model_path,
            output_model_path=str(paths.epoch_run_dir(epoch)),
            mode="stub",
        )
        append_metrics(
            paths.metrics_jsonl,
            event="checkpoint",
            epoch=epoch,
            checkpoint_path=str(observed_checkpoint),
            promoted_checkpoint_path=str(paths.promoted_checkpoint_path(epoch)),
            init_model_path=init_model_path,
        )
        return observed_checkpoint
    command, env = build_train_command(args, paths, epoch, init_model_path)
    result = run_command(command, paths.command_log_path("train", epoch), env=env)
    append_metrics(
        paths.metrics_jsonl,
        event="train_end",
        status="ok" if result.returncode == 0 else "failed",
        returncode=result.returncode,
        started_at=started_at,
        finished_at=utc_now(),
        epoch=epoch,
        command=result.command,
        log_path=str(result.log_path),
        init_model_path=init_model_path,
        output_model_path=str(paths.epoch_run_dir(epoch)),
    )
    if result.returncode != 0:
        raise OrchestrationError(f"training epoch {epoch} failed with exit {result.returncode}")
    observed_checkpoint = paths.epoch_checkpoint_path(epoch)
    if not observed_checkpoint.exists():
        raise OrchestrationError(
            f"training epoch {epoch} finished but checkpoint was not found: {observed_checkpoint}"
        )
    promote_checkpoint(observed_checkpoint, paths.promoted_checkpoint_path(epoch))
    append_metrics(
        paths.metrics_jsonl,
        event="checkpoint",
        epoch=epoch,
        checkpoint_path=str(observed_checkpoint),
        promoted_checkpoint_path=str(paths.promoted_checkpoint_path(epoch)),
        init_model_path=init_model_path,
    )
    return observed_checkpoint


def generate_eval_pack(args: argparse.Namespace, paths: RunPaths, epoch: int, checkpoint_path: Path) -> None:
    epoch_eval_dir = paths.epoch_eval_dir(epoch)
    epoch_eval_dir.mkdir(parents=True, exist_ok=True)
    for phrase in DEFAULT_EVAL_PHRASES:
        output_path = epoch_eval_dir / phrase.filename
        command = build_infer_command(args, checkpoint_path, phrase, output_path)
        started_at = utc_now()
        append_metrics(
            paths.metrics_jsonl,
            event="eval_start",
            started_at=started_at,
            epoch=epoch,
            label=phrase.label,
            output_path=str(output_path),
            checkpoint_path=str(checkpoint_path),
            language=phrase.language,
            text=phrase.text,
            mode=args.execution_mode,
        )
        if args.execution_mode == "stub":
            write_stub_wav(output_path, phrase.text)
            append_metrics(
                paths.metrics_jsonl,
                event="eval_sample",
                status="ok",
                returncode=0,
                started_at=started_at,
                finished_at=utc_now(),
                epoch=epoch,
                label=phrase.label,
                output_path=str(output_path),
                checkpoint_path=str(checkpoint_path),
                language=phrase.language,
                command=command,
            )
            append_metrics(paths.metrics_jsonl, **compute_sample_metrics(args, epoch, phrase, output_path).to_row())
            continue
        result = run_command(command, paths.command_log_path(f"eval-{phrase.label}", epoch))
        append_metrics(
            paths.metrics_jsonl,
            event="eval_sample",
            status="ok" if result.returncode == 0 else "failed",
            returncode=result.returncode,
            started_at=started_at,
            finished_at=utc_now(),
            epoch=epoch,
            label=phrase.label,
            output_path=str(output_path),
            checkpoint_path=str(checkpoint_path),
            language=phrase.language,
            command=result.command,
            log_path=str(result.log_path),
        )
        if result.returncode != 0:
            raise OrchestrationError(
                f"eval generation failed for epoch {epoch} / {phrase.filename} "
                f"with exit {result.returncode}"
            )
        append_metrics(paths.metrics_jsonl, **compute_sample_metrics(args, epoch, phrase, output_path).to_row())


def orchestrate(args: argparse.Namespace) -> RunPaths:
    paths = build_paths(args.output_root, args.voice_name, args.run_name)
    ensure_run_dirs(paths)
    last_stop_decision: EarlyStopDecision | None = None
    review_export: CandidateReviewExport | None = None
    append_metrics(
        paths.metrics_jsonl,
        event="run_start",
        voice_name=args.voice_name,
        speaker_name=args.speaker_name,
        train_raw_jsonl=str(args.train_raw_jsonl),
        output_root=str(args.output_root),
        run_name=args.run_name,
        max_epochs=args.max_epochs,
        min_epochs=args.min_epochs,
        patience=args.patience,
        base_model=args.base_model,
        execution_mode=args.execution_mode,
    )
    try:
        run_prepare(args, paths)
        for epoch in range(args.max_epochs):
            checkpoint = run_train_epoch(args, paths, epoch)
            generate_eval_pack(args, paths, epoch, checkpoint)
            checkpoint_score = append_checkpoint_score(paths, epoch, checkpoint)
            checkpoint_gate = append_checkpoint_gate(args, paths, checkpoint_score)
            last_stop_decision = append_early_stop_decision(args, paths, checkpoint_gate)
            if last_stop_decision.should_stop:
                break
        if last_stop_decision is not None:
            if not last_stop_decision.should_stop:
                last_stop_decision = EarlyStopDecision(
                    epoch=last_stop_decision.epoch,
                    should_stop=True,
                    reason=STOP_REASON_MAX_EPOCHS_REACHED,
                    best_epoch=last_stop_decision.best_epoch,
                    best_score=last_stop_decision.best_score,
                    epochs_without_improvement=last_stop_decision.epochs_without_improvement,
                    min_epochs_reached=last_stop_decision.min_epochs_reached,
                )
            append_run_stop(paths, last_stop_decision)
        append_candidate_selection(args, paths)
        review_export = export_candidate_review_pack(args, paths)
    except Exception as exc:
        append_metrics(
            paths.metrics_jsonl,
            event="failure",
            status="failed",
            error_type=type(exc).__name__,
            message=str(exc),
        )
        raise
    append_metrics(paths.metrics_jsonl, event="run_end", status="ok")
    if review_export is not None:
        copy_candidate_review_metrics(paths, Path(review_export.metrics_path))
    return paths


def print_summary(paths: RunPaths) -> None:
    sys.stdout.write(f"run_dir={paths.run_dir}\n")
    sys.stdout.write(f"prepared_manifest={paths.prepared_manifest}\n")
    sys.stdout.write(f"metrics_jsonl={paths.metrics_jsonl}\n")
    sys.stdout.write(f"checkpoints_dir={paths.checkpoints_dir}\n")
    sys.stdout.write(f"eval_dir={paths.eval_dir}\n")
    sys.stdout.write(f"candidate_manifest={paths.candidate_manifest}\n")
    if paths.candidate_manifest.exists():
        manifest = load_candidate_manifest(paths)
        review = manifest.get("candidate_review")
        if isinstance(review, dict) and review.get("review_dir"):
            sys.stdout.write(f"candidate_review_dir={review['review_dir']}\n")


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run Qwen3TTS prepare_data, one-epoch training jobs, checkpoint capture, "
            "and fixed eval-pack generation for a target voice."
        )
    )
    parser.add_argument("--voice_name", required=True, help="Voice name used for output path grouping")
    parser.add_argument("--train_raw_jsonl", type=Path, required=True, help="Ready dataset train_raw.jsonl")
    parser.add_argument("--output_root", type=Path, required=True, help="Root directory for this training run")
    parser.add_argument("--run_name", default=DEFAULT_RUN_NAME, help="Deterministic run name under the voice")
    parser.add_argument(
        "--candidate_review_root",
        type=Path,
        default=None,
        help="Optional output directory for the copied candidate review pack.",
    )
    parser.add_argument(
        "--min_epochs",
        type=int,
        default=DEFAULT_MIN_EPOCHS,
        help="Minimum completed epochs before semi-auto early stopping may stop training.",
    )
    parser.add_argument(
        "--max_epochs",
        type=int,
        default=DEFAULT_MAX_EPOCHS,
        help="Maximum one-epoch jobs to run before stopping.",
    )
    parser.add_argument(
        "--patience",
        type=int,
        default=DEFAULT_PATIENCE,
        help="Stop after this many viable epochs without score improvement.",
    )
    parser.add_argument(
        "--early_stop_min_delta",
        type=float,
        default=DEFAULT_EARLY_STOP_MIN_DELTA,
        help="Minimum score increase required to count as an improvement.",
    )
    parser.add_argument("--top_candidates", type=int, default=DEFAULT_TOP_CANDIDATES, help="Maximum final candidates")
    parser.add_argument(
        "--candidate_floor",
        type=int,
        default=DEFAULT_CANDIDATE_FLOOR,
        help="Minimum viable candidates expected before the manifest is no longer limited.",
    )
    parser.add_argument("--speaker_name", default="speaker_target", help="Speaker name passed to SFT/inference")
    parser.add_argument("--base_model", default=DEFAULT_BASE_MODEL, help="Initial model for epoch 0")
    parser.add_argument("--tokenizer_model_path", default=DEFAULT_TOKENIZER_MODEL)
    parser.add_argument("--device", default=DEFAULT_DEVICE)
    parser.add_argument("--batch_size", default="2")
    parser.add_argument("--learning_rate", default="2e-5")
    parser.add_argument(
        "--execution_mode",
        choices=("real", "stub"),
        default="real",
        help="Use real subprocesses or safe stub artifacts for tests/smoke.",
    )
    parser.add_argument("--prepare_command", type=Path, default=Path("scripts/run_prepare_data.sh"))
    parser.add_argument("--train_command", type=Path, default=Path("scripts/run_sft_0_6b.sh"))
    parser.add_argument("--infer_script", type=Path, default=Path("scripts/run_infer_sample.py"))
    parser.add_argument(
        "--metrics_mode",
        choices=("auto", "stub", "audio", "off"),
        default=DEFAULT_METRIC_BACKENDS.metrics_mode,
        help="Metric extraction backend: auto, stub, audio, or off.",
    )
    parser.add_argument(
        "--text_match_backend",
        choices=("auto", "stub", "off", "faster-whisper"),
        default=DEFAULT_METRIC_BACKENDS.text_match_backend,
        help="Text-match metric backend for whisper_text_match.",
    )
    parser.add_argument(
        "--text_match_model",
        default=os.environ.get("QWEN3TTS_TEXT_MATCH_MODEL", DEFAULT_TEXT_MATCH_MODEL),
        help="faster-whisper model name/path for real whisper_text_match.",
    )
    parser.add_argument(
        "--text_match_device",
        default=os.environ.get("QWEN3TTS_TEXT_MATCH_DEVICE", DEFAULT_TEXT_MATCH_DEVICE),
        help="faster-whisper device for real whisper_text_match, e.g. cuda or cpu.",
    )
    parser.add_argument(
        "--text_match_compute_type",
        default=os.environ.get("QWEN3TTS_TEXT_MATCH_COMPUTE_TYPE", DEFAULT_TEXT_MATCH_COMPUTE_TYPE),
        help="faster-whisper compute type for real whisper_text_match.",
    )
    parser.add_argument(
        "--text_match_beam_size",
        type=int,
        default=5,
        help="Beam size for real faster-whisper text-match transcription.",
    )
    parser.add_argument(
        "--speaker_similarity_backend",
        choices=("off", "stub"),
        default=DEFAULT_METRIC_BACKENDS.speaker_similarity_backend,
        help="Optional speaker similarity backend.",
    )
    parser.add_argument(
        "--reference_audio",
        type=Path,
        default=None,
        help="Optional reference audio for speaker similarity backends.",
    )
    parser.add_argument(
        "--python_executable",
        default=project_python(Path.cwd()),
        help="Python executable for real inference subprocesses.",
    )
    parser.add_argument(
        "--hard_reject_text_match_min",
        type=float,
        default=DEFAULT_HARD_REJECT_THRESHOLDS.asr_text_match_min,
        help="Reject checkpoint when mean whisper_text_match is below this value.",
    )
    parser.add_argument(
        "--hard_reject_pace_acceleration_max",
        type=float,
        default=DEFAULT_HARD_REJECT_THRESHOLDS.pace_acceleration_ratio_max,
        help="Reject checkpoint when pace is this ratio faster than the previous viable checkpoint.",
    )
    parser.add_argument(
        "--hard_reject_clipping_ratio_max",
        type=float,
        default=DEFAULT_HARD_REJECT_THRESHOLDS.clipping_ratio_max,
        help="Reject checkpoint when max clipping_ratio exceeds this value.",
    )
    parser.add_argument(
        "--hard_reject_duration_ratio_min",
        type=float,
        default=DEFAULT_HARD_REJECT_THRESHOLDS.duration_ratio_min,
        help="Reject checkpoint when mean duration_ratio is below this value.",
    )
    parser.add_argument(
        "--hard_reject_duration_ratio_max",
        type=float,
        default=DEFAULT_HARD_REJECT_THRESHOLDS.duration_ratio_max,
        help="Reject checkpoint when mean duration_ratio is above this value.",
    )
    parser.add_argument(
        "--hard_reject_suspected_cut_duration_ratio_max",
        type=float,
        default=DEFAULT_HARD_REJECT_THRESHOLDS.suspected_cut_duration_ratio_max,
        help="Reject suspected cut when duration_ratio is at or below this value with bad tail silence.",
    )
    parser.add_argument(
        "--hard_reject_suspected_cut_trailing_silence_ms_max",
        type=float,
        default=DEFAULT_HARD_REJECT_THRESHOLDS.suspected_cut_trailing_silence_ms_max,
        help="Reject suspected cut when trailing_silence_ms is at or below this value with short duration.",
    )
    parser.add_argument(
        "--hard_reject_score_drop_max",
        type=float,
        default=DEFAULT_HARD_REJECT_THRESHOLDS.score_drop_max,
        help="Reject checkpoint when score drops by more than this from the previous viable/best checkpoint.",
    )
    return parser


def args_to_jsonable(args: argparse.Namespace) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in vars(args).items():
        result[key] = str(value) if isinstance(value, Path) else value
    return result


def validate_args(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    if args.min_epochs < 1:
        parser.error("--min_epochs must be >= 1")
    if args.max_epochs < 1:
        parser.error("--max_epochs must be >= 1")
    if args.patience < 1:
        parser.error("--patience must be >= 1")
    if args.top_candidates < 1:
        parser.error("--top_candidates must be >= 1")
    if args.candidate_floor < 1:
        parser.error("--candidate_floor must be >= 1")
    if args.min_epochs > args.max_epochs:
        parser.error("--min_epochs must be <= --max_epochs")


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    validate_args(args, parser)
    try:
        paths = orchestrate(args)
    except OrchestrationError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
    print_summary(paths)
    return 0


__all__ = [
    "CANDIDATE_REVIEW_RANK_NAMES",
    "DEFAULT_EVAL_PHRASES",
    "DEFAULT_EARLY_STOP_MIN_DELTA",
    "DEFAULT_CANDIDATE_FLOOR",
    "DEFAULT_EARLY_STOP_POLICY",
    "DEFAULT_METRIC_BACKENDS",
    "DEFAULT_HARD_REJECT_THRESHOLDS",
    "DEFAULT_MAX_EPOCHS",
    "DEFAULT_METRIC_THRESHOLDS",
    "DEFAULT_METRIC_WEIGHTS",
    "DEFAULT_MIN_EPOCHS",
    "DEFAULT_PATIENCE",
    "DEFAULT_TOP_CANDIDATES",
    "METRIC_EVENT_CANDIDATE_REVIEW_EXPORT",
    "QUALITY_DEGRADATION_REJECT_REASONS",
    "STOP_REASON_MAX_EPOCHS_REACHED",
    "STOP_REASON_MIN_EPOCHS_PENDING",
    "STOP_REASON_NO_VIABLE_CHECKPOINT",
    "STOP_REASON_PATIENCE_EXHAUSTED",
    "STOP_REASON_PATIENCE_PENDING",
    "STOP_REASON_QUALITY_DEGRADATION",
    "STOP_REASON_SCORE_IMPROVED",
    "CandidateSelection",
    "CandidateReviewExport",
    "CheckpointGate",
    "EarlyStopDecision",
    "EarlyStopPolicy",
    "EvalPhrase",
    "MetricBackends",
    "HardRejectThresholds",
    "MetricThresholds",
    "MetricWeights",
    "OrchestrationError",
    "RunPaths",
    "RunStop",
    "SampleMetrics",
    "CheckpointScore",
    "build_infer_command",
    "build_paths",
    "build_prepare_command",
    "build_train_command",
    "clamp_score",
    "append_candidate_selection",
    "append_early_stop_decision",
    "append_checkpoint_gate",
    "append_run_stop",
    "best_viable_gate_state",
    "candidate_entry_from_gate",
    "candidate_review_folder_name",
    "candidate_review_rank_name",
    "candidate_list_from_manifest",
    "compute_sample_metrics",
    "copy_candidate_review_metrics",
    "create_parser",
    "default_candidate_review_root",
    "evaluate_early_stop_decision",
    "evaluate_checkpoint_gate",
    "export_candidate_review_pack",
    "estimate_expected_duration_seconds",
    "early_stop_policy_row",
    "early_stop_policy_from_args",
    "faster_whisper_text_match",
    "hard_reject_thresholds_row",
    "hard_reject_thresholds_from_args",
    "loss_summary_for_epoch",
    "latest_event_row",
    "list_candidate_eval_sources",
    "load_candidate_manifest",
    "metric_thresholds_row",
    "metric_weights_row",
    "orchestrate",
    "parse_loss_values",
    "read_metrics",
    "run_stop_from_decision",
    "resolve_backend_mode",
    "resolve_candidate_review_root",
    "gate_has_quality_degradation",
    "stop_summary_from_metrics",
    "text_match_for_phrase",
    "text_match_ratio",
    "validate_args",
    "write_candidate_review_ranking",
    "write_stub_wav",
]


if __name__ == "__main__":
    raise SystemExit(main())
