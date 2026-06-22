#!/usr/bin/env python3
"""Select the human-approved Qwen3TTS voice checkpoint.

The module stays standard-library only at import time. It reads the candidate
review pack exported by ``tools/train_voice_candidates.py`` and writes small
metadata pointers; it never copies checkpoint, audio, or metrics artifacts.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


CANDIDATE_LABELS = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
SELECTION_SCHEMA_VERSION = 1


class SelectionError(RuntimeError):
    """Raised when a winner cannot be selected safely."""


@dataclass(frozen=True)
class CandidateTarget:
    rank: int
    label: str
    epoch: int | None = None
    raw: str = ""


@dataclass(frozen=True)
class ReviewContext:
    review_dir: Path
    manifest_path: Path
    manifest: dict[str, object]
    run_dir: Path
    experiment_root: Path | None
    selection_root: Path
    selected_checkpoint_path: Path
    status_path: Path


@dataclass(frozen=True)
class SelectionResult:
    selected_checkpoint_path: Path
    status_path: Path
    manifest_path: Path
    payload: dict[str, object]
    status: dict[str, object]
    manifest: dict[str, object]
    dry_run: bool = False


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def rank_label(rank: int) -> str:
    if rank < 1:
        raise SelectionError("candidate rank must be >= 1")
    if rank <= len(CANDIDATE_LABELS):
        return CANDIDATE_LABELS[rank - 1]
    return str(rank)


def normalize_candidate(raw: str) -> CandidateTarget:
    value = raw.strip()
    if not value:
        raise SelectionError("candidate value is empty")

    label_match = re.fullmatch(r"candidate_([A-Za-z]+|\d+)_epoch(\d+)", value)
    if label_match:
        label_value = label_match.group(1).upper()
        return CandidateTarget(
            rank=rank_from_label(label_value),
            label=label_value,
            epoch=int(label_match.group(2)),
            raw=raw,
        )

    if value.isdigit():
        rank = int(value)
        return CandidateTarget(rank=rank, label=rank_label(rank), raw=raw)

    if re.fullmatch(r"[A-Za-z]", value):
        label_value = value.upper()
        return CandidateTarget(rank=rank_from_label(label_value), label=label_value, raw=raw)

    raise SelectionError(
        "candidate must be a letter, rank number, or label like candidate_B_epoch1"
    )


def rank_from_label(label: str) -> int:
    if label.isdigit():
        return int(label)
    if len(label) == 1 and label in CANDIDATE_LABELS:
        return CANDIDATE_LABELS.index(label) + 1
    raise SelectionError(f"unsupported candidate label: {label}")


def load_json_object(path: Path, description: str) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SelectionError(f"{description} not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SelectionError(f"{description} is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise SelectionError(f"{description} must be a JSON object: {path}")
    return payload


def candidate_list_from_manifest(manifest: dict[str, object]) -> list[dict[str, object]]:
    candidates = manifest.get("candidates", [])
    if not isinstance(candidates, list):
        raise SelectionError("candidate_manifest.json candidates must be a list")
    result: list[dict[str, object]] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise SelectionError("candidate_manifest.json contains a non-object candidate")
        result.append(candidate)
    return result


def rejected_list_from_manifest(manifest: dict[str, object]) -> list[dict[str, object]]:
    rejected = manifest.get("rejected_checkpoints", [])
    if not isinstance(rejected, list):
        raise SelectionError("candidate_manifest.json rejected_checkpoints must be a list")
    return [row for row in rejected if isinstance(row, dict)]


def possible_manifest_paths(review_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    candidates.append(review_dir / "candidate_manifest.json")
    candidates.append(review_dir.parent / "candidate_manifest.json")

    parts = review_dir.parts
    if len(parts) >= 4 and parts[-1] == "candidate_review":
        run_name = parts[-2]
        voice_name = parts[-3]
        marker = parts[-4]
        if marker == "samples":
            experiment_root = Path(*parts[:-4])
            candidates.append(experiment_root / "runs" / voice_name / run_name / "candidate_manifest.json")

    deduped: list[Path] = []
    for path in candidates:
        if path not in deduped:
            deduped.append(path)
    return deduped


def manifest_matches_review(manifest: dict[str, object], review_dir: Path) -> bool:
    review = manifest.get("candidate_review")
    if not isinstance(review, dict):
        return False
    manifest_review_dir = review.get("review_dir")
    if manifest_review_dir is None:
        return False
    return Path(str(manifest_review_dir)).resolve() == review_dir.resolve()


def find_manifest_for_review(review_dir: Path) -> tuple[Path, dict[str, object]]:
    for path in possible_manifest_paths(review_dir):
        if not path.exists():
            continue
        manifest = load_json_object(path, "candidate manifest")
        if manifest_matches_review(manifest, review_dir) or path.parent == review_dir.parent:
            return path, manifest
    searched = ", ".join(str(path) for path in possible_manifest_paths(review_dir))
    raise SelectionError(f"candidate manifest for review dir not found; searched: {searched}")


def looks_like_review_dir(path: Path) -> bool:
    return path.is_dir() and path.name == "candidate_review" and (path / "ranking.md").exists()


def find_review_dirs(root: Path) -> list[Path]:
    if looks_like_review_dir(root):
        return [root]
    if not root.exists() or not root.is_dir():
        return []
    matches: list[Path] = []
    for path in root.rglob("candidate_review"):
        if looks_like_review_dir(path):
            matches.append(path)
    return sorted(matches)


def discover_candidate_review_dir(
    explicit_review_dir: str | None = None,
    search_root: Path | None = None,
) -> Path:
    if explicit_review_dir:
        review_dir = Path(explicit_review_dir).expanduser()
        if not review_dir.is_dir():
            raise SelectionError(f"candidate review directory not found: {review_dir}")
        return review_dir.resolve()

    root = (search_root or Path.cwd()).resolve()
    matches = find_review_dirs(root)
    if not matches:
        raise SelectionError(
            "candidate review directory not found; pass --candidate_review_dir explicitly"
        )
    if len(matches) > 1:
        listed = ", ".join(str(path) for path in matches[:5])
        raise SelectionError(
            "multiple candidate review directories found; pass --candidate_review_dir explicitly: "
            + listed
        )
    return matches[0].resolve()


def infer_experiment_root(manifest_path: Path) -> Path | None:
    parents = manifest_path.resolve().parents
    if len(parents) >= 4 and parents[2].name == "runs":
        return parents[3]
    return None


def resolve_output_paths(
    review_dir: Path,
    manifest_path: Path,
    manifest: dict[str, object],
    experiment_root: str | None = None,
) -> ReviewContext:
    run_dir = manifest_path.parent.resolve()
    explicit_experiment_root = Path(experiment_root).expanduser().resolve() if experiment_root else None
    inferred_experiment_root = infer_experiment_root(manifest_path)
    selection_root = explicit_experiment_root or inferred_experiment_root or run_dir
    return ReviewContext(
        review_dir=review_dir.resolve(),
        manifest_path=manifest_path.resolve(),
        manifest=manifest,
        run_dir=run_dir,
        experiment_root=explicit_experiment_root or inferred_experiment_root,
        selection_root=selection_root,
        selected_checkpoint_path=selection_root / "selected_checkpoint.json",
        status_path=selection_root / "experiment_status.json",
    )


def load_review_context(
    candidate_review_dir: str | None,
    experiment_root: str | None = None,
    search_root: Path | None = None,
) -> ReviewContext:
    review_dir = discover_candidate_review_dir(candidate_review_dir, search_root=search_root)
    manifest_path, manifest = find_manifest_for_review(review_dir)
    return resolve_output_paths(review_dir, manifest_path, manifest, experiment_root=experiment_root)


def candidate_matches_target(candidate: dict[str, object], target: CandidateTarget) -> bool:
    rank = candidate.get("rank")
    label = str(candidate.get("label") or "")
    epoch = candidate.get("epoch")
    if isinstance(rank, int) and rank != target.rank:
        return False
    if not isinstance(rank, int) and not label.startswith(f"candidate_{target.label}_"):
        return False
    if target.epoch is not None and epoch != target.epoch:
        return False
    return True


def rejected_matches_target(rejected: dict[str, object], target: CandidateTarget) -> bool:
    epoch = rejected.get("epoch")
    return target.epoch is not None and epoch == target.epoch


def find_selected_candidate(manifest: dict[str, object], target: CandidateTarget) -> dict[str, object]:
    matches = [
        candidate
        for candidate in candidate_list_from_manifest(manifest)
        if candidate_matches_target(candidate, target)
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SelectionError(f"candidate {target.raw or target.label} is ambiguous in candidates")

    rejected_matches = [
        row
        for row in rejected_list_from_manifest(manifest)
        if rejected_matches_target(row, target)
    ]
    if rejected_matches:
        raise SelectionError(f"candidate {target.raw or target.label} is present only in rejected checkpoints")
    raise SelectionError(f"candidate {target.raw or target.label} is not present in candidates")


def validate_checkpoint_path(candidate: dict[str, object]) -> Path:
    raw_path = candidate.get("checkpoint_path")
    if not raw_path:
        raise SelectionError("selected candidate has no checkpoint_path")
    path = Path(str(raw_path))
    if not path.exists():
        raise SelectionError(f"selected checkpoint path does not exist: {path}")
    return path


def compact_candidate(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "label": candidate.get("label"),
        "rank": candidate.get("rank"),
        "epoch": candidate.get("epoch"),
        "score": candidate.get("score"),
        "checkpoint_path": candidate.get("checkpoint_path"),
        "eval_dir": candidate.get("eval_dir"),
        "warning_reasons": candidate.get("warning_reasons", []),
        "reject_reasons": candidate.get("reject_reasons", []),
    }


def build_selection_payload(
    context: ReviewContext,
    target: CandidateTarget,
    candidate: dict[str, object],
    checkpoint_path: Path,
) -> dict[str, object]:
    selected_at = utc_now()
    label = candidate.get("label") or f"candidate_{target.label}_epoch{candidate.get('epoch')}"
    payload: dict[str, object] = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "selected_at": selected_at,
        "status": "selected",
        "selection_source": "human",
        "candidate_input": target.raw,
        "candidate_label": label,
        "candidate_rank": candidate.get("rank"),
        "candidate_epoch": candidate.get("epoch"),
        "checkpoint_path": str(checkpoint_path),
        "score": candidate.get("score"),
        "voice_name": context.manifest.get("voice_name"),
        "run_name": context.manifest.get("run_name"),
        "review_dir": str(context.review_dir),
        "source_manifest_path": str(context.manifest_path),
        "run_dir": str(context.run_dir),
        "experiment_root": str(context.experiment_root) if context.experiment_root else None,
        "selected_checkpoint_json": str(context.selected_checkpoint_path),
        "experiment_status_path": str(context.status_path),
        "candidate": compact_candidate(candidate),
    }
    return payload


def build_status_payload(selection_payload: dict[str, object]) -> dict[str, object]:
    return {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "updated_at": selection_payload["selected_at"],
        "status": "selected",
        "active_checkpoint": selection_payload["checkpoint_path"],
        "primary_checkpoint": selection_payload["checkpoint_path"],
        "selected_checkpoint": selection_payload["checkpoint_path"],
        "selected_candidate_label": selection_payload["candidate_label"],
        "selected_candidate_rank": selection_payload["candidate_rank"],
        "selected_candidate_epoch": selection_payload["candidate_epoch"],
        "selected_checkpoint_json": selection_payload["selected_checkpoint_json"],
        "source_manifest_path": selection_payload["source_manifest_path"],
        "review_dir": selection_payload["review_dir"],
        "selection_source": selection_payload["selection_source"],
    }


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def select_voice_candidate(args: argparse.Namespace, search_root: Path | None = None) -> SelectionResult:
    target = normalize_candidate(args.candidate)
    context = load_review_context(
        args.candidate_review_dir,
        experiment_root=args.experiment_root,
        search_root=search_root,
    )
    candidate = find_selected_candidate(context.manifest, target)
    checkpoint_path = validate_checkpoint_path(candidate)
    payload = build_selection_payload(context, target, candidate, checkpoint_path)
    status = build_status_payload(payload)

    updated_manifest = dict(context.manifest)
    updated_manifest["winner_selection"] = {
        "schema_version": SELECTION_SCHEMA_VERSION,
        "selected_at": payload["selected_at"],
        "selection_source": payload["selection_source"],
        "candidate_label": payload["candidate_label"],
        "candidate_rank": payload["candidate_rank"],
        "candidate_epoch": payload["candidate_epoch"],
        "checkpoint_path": payload["checkpoint_path"],
        "score": payload["score"],
        "selected_checkpoint_json": str(context.selected_checkpoint_path),
        "experiment_status_path": str(context.status_path),
    }

    if args.dry_run:
        return SelectionResult(
            selected_checkpoint_path=context.selected_checkpoint_path,
            status_path=context.status_path,
            manifest_path=context.manifest_path,
            payload=payload,
            status=status,
            manifest=updated_manifest,
            dry_run=True,
        )

    write_json(context.selected_checkpoint_path, payload)
    write_json(context.status_path, status)
    write_json(context.manifest_path, updated_manifest)
    return SelectionResult(
        selected_checkpoint_path=context.selected_checkpoint_path,
        status_path=context.status_path,
        manifest_path=context.manifest_path,
        payload=payload,
        status=status,
        manifest=updated_manifest,
        dry_run=False,
    )


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Mark a human-reviewed Qwen3TTS candidate checkpoint as the selected voice."
    )
    parser.add_argument(
        "--candidate",
        required=True,
        help="Candidate to select: A, B, C, a numeric rank like 2, or candidate_B_epoch1.",
    )
    parser.add_argument(
        "--candidate_review_dir",
        help="Path to candidate_review exported by train_voice_candidates.py. Required when discovery is ambiguous.",
    )
    parser.add_argument(
        "--experiment_root",
        help="Override where selected_checkpoint.json and experiment_status.json are written.",
    )
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="Validate and show the files that would be updated without writing them.",
    )
    return parser


def emit_result(result: SelectionResult) -> None:
    prefix = "DRY RUN " if result.dry_run else ""
    lines = [
        f"{prefix}selected_candidate={result.payload['candidate_label']}",
        f"{prefix}selected_checkpoint={result.payload['checkpoint_path']}",
        f"{prefix}selected_checkpoint_json={result.selected_checkpoint_path}",
        f"{prefix}experiment_status={result.status_path}",
        f"{prefix}candidate_manifest={result.manifest_path}",
    ]
    sys.stdout.write("\n".join(lines) + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)
    try:
        result = select_voice_candidate(args)
    except SelectionError as exc:
        sys.stderr.write(f"ERROR: {exc}\n")
        return 1
    emit_result(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CandidateTarget",
    "ReviewContext",
    "SelectionError",
    "SelectionResult",
    "candidate_list_from_manifest",
    "create_parser",
    "discover_candidate_review_dir",
    "find_manifest_for_review",
    "find_selected_candidate",
    "load_review_context",
    "main",
    "normalize_candidate",
    "rank_label",
    "resolve_output_paths",
    "select_voice_candidate",
]
