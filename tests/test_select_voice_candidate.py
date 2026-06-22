from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class SelectVoiceCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = importlib.import_module("tools.select_voice_candidate")

    def make_review_fixture(
        self,
        tmp_path: Path,
        *,
        normal_experiment: bool = True,
        candidate_b_in_candidates: bool = True,
    ) -> tuple[Path, Path, Path]:
        if normal_experiment:
            experiment_root = tmp_path / "experiments" / "voice_demo"
            run_dir = experiment_root / "runs" / "SmokeVoice" / "smoke"
            review_dir = experiment_root / "samples" / "SmokeVoice" / "smoke" / "candidate_review"
        else:
            experiment_root = tmp_path / "output"
            run_dir = experiment_root / "SmokeVoice" / "smoke"
            review_dir = run_dir / "candidate_review"
        checkpoint_a = run_dir / "train" / "epoch-0" / "checkpoint-epoch-0"
        checkpoint_b = run_dir / "train" / "epoch-1" / "checkpoint-epoch-0"
        checkpoint_a.mkdir(parents=True)
        checkpoint_b.mkdir(parents=True)
        review_dir.mkdir(parents=True)
        (review_dir / "ranking.md").write_text("# Candidate Review Ranking\n", encoding="utf-8")
        (review_dir / "metrics.jsonl").write_text("", encoding="utf-8")
        candidates = [
            {
                "rank": 1,
                "label": "candidate_A_epoch0",
                "epoch": 0,
                "checkpoint_path": str(checkpoint_a),
                "eval_dir": str(run_dir / "eval" / "epoch-0"),
                "score": 95.0,
                "warning_reasons": [],
                "reject_reasons": [],
            }
        ]
        rejected = []
        b_row = {
            "rank": 2,
            "label": "candidate_B_epoch1",
            "epoch": 1,
            "checkpoint_path": str(checkpoint_b),
            "eval_dir": str(run_dir / "eval" / "epoch-1"),
            "score": 93.0,
            "warning_reasons": ["missing_loss"],
            "reject_reasons": [],
        }
        if candidate_b_in_candidates:
            candidates.append(b_row)
        else:
            rejected.append(
                {
                    "epoch": 1,
                    "checkpoint_path": str(checkpoint_b),
                    "score": 93.0,
                    "reject_reasons": ["asr_text_mismatch"],
                }
            )
        manifest = {
            "generated_at": "2026-06-22T00:00:00+00:00",
            "voice_name": "SmokeVoice",
            "run_name": "smoke",
            "status": "ok",
            "candidate_count": len(candidates),
            "rejected_count": len(rejected),
            "candidate_review": {
                "review_dir": str(review_dir),
                "ranking_path": str(review_dir / "ranking.md"),
                "metrics_path": str(review_dir / "metrics.jsonl"),
                "candidate_count": len(candidates),
                "exported_epochs": [row["epoch"] for row in candidates],
                "candidate_dirs": [str(review_dir / row["label"]) for row in candidates],
            },
            "candidates": candidates,
            "rejected_checkpoints": rejected,
        }
        manifest_path = run_dir / "candidate_manifest.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return experiment_root, run_dir, review_dir

    def test_import_does_not_load_heavy_runtime_modules(self) -> None:
        heavy = {"torch", "qwen_tts", "soundfile", "faster_whisper"}
        before = set(sys.modules)
        importlib.reload(self.module)
        introduced = set(sys.modules) - before
        self.assertFalse(heavy & introduced)

    def test_candidate_inputs_resolve_to_same_rank_target(self) -> None:
        targets = [self.module.normalize_candidate(value) for value in ("B", "b", "2", "candidate_B_epoch1")]
        self.assertEqual({target.rank for target in targets}, {2})
        self.assertEqual({target.label for target in targets}, {"B"})
        self.assertEqual(targets[-1].epoch, 1)

    def test_cli_help_contains_required_options(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/select_voice_candidate.py", "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for option in ("--candidate", "--candidate_review_dir", "--experiment_root", "--dry_run"):
            self.assertIn(option, completed.stdout)

    def test_explicit_review_dir_is_accepted_and_ambiguous_discovery_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _, _, first_review = self.make_review_fixture(root / "one")
            _, _, second_review = self.make_review_fixture(root / "two")
            self.assertEqual(
                self.module.discover_candidate_review_dir(str(first_review)),
                first_review.resolve(),
            )
            with self.assertRaisesRegex(self.module.SelectionError, "multiple candidate review directories"):
                self.module.discover_candidate_review_dir(search_root=root)
            self.assertTrue(second_review.exists())

    def test_manifest_candidates_exclude_rejected_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, _, review_dir = self.make_review_fixture(Path(tmp), candidate_b_in_candidates=False)
            manifest_path, manifest = self.module.find_manifest_for_review(review_dir)
            candidates = self.module.candidate_list_from_manifest(manifest)
            self.assertTrue(manifest_path.exists())
            self.assertEqual([candidate["label"] for candidate in candidates], ["candidate_A_epoch0"])
            with self.assertRaisesRegex(self.module.SelectionError, "present only in rejected"):
                self.module.find_selected_candidate(
                    manifest,
                    self.module.normalize_candidate("candidate_B_epoch1"),
                )

    def test_select_candidate_writes_small_selection_metadata_and_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            experiment_root, _, review_dir = self.make_review_fixture(Path(tmp))
            before_heavy = sorted(
                str(path.relative_to(experiment_root))
                for path in experiment_root.rglob("*")
                if path.name == "metrics.jsonl" or path.suffix.lower() == ".wav" or path.name.startswith("checkpoint-")
            )
            args = self.module.create_parser().parse_args(
                ["--candidate", "B", "--candidate_review_dir", str(review_dir)]
            )
            result = self.module.select_voice_candidate(args)
            selected = json.loads(result.selected_checkpoint_path.read_text(encoding="utf-8"))
            status = json.loads(result.status_path.read_text(encoding="utf-8"))
            manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
            after_heavy = sorted(
                str(path.relative_to(experiment_root))
                for path in experiment_root.rglob("*")
                if path.name == "metrics.jsonl" or path.suffix.lower() == ".wav" or path.name.startswith("checkpoint-")
            )

            self.assertEqual(result.selected_checkpoint_path, experiment_root / "selected_checkpoint.json")
            self.assertEqual(result.status_path, experiment_root / "experiment_status.json")
            self.assertEqual(selected["candidate_label"], "candidate_B_epoch1")
            self.assertEqual(selected["candidate_rank"], 2)
            self.assertEqual(selected["candidate_epoch"], 1)
            self.assertEqual(selected["score"], 93.0)
            self.assertEqual(status["active_checkpoint"], selected["checkpoint_path"])
            self.assertEqual(status["primary_checkpoint"], selected["checkpoint_path"])
            self.assertEqual(manifest["winner_selection"]["candidate_label"], "candidate_B_epoch1")
            self.assertEqual([candidate["label"] for candidate in manifest["candidates"]], ["candidate_A_epoch0", "candidate_B_epoch1"])
            self.assertEqual(before_heavy, after_heavy)
            self.assertFalse((experiment_root / "candidate_B_epoch1").exists())
            self.assertFalse((experiment_root / "metrics.jsonl").exists())

    def test_dry_run_prints_planned_files_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            experiment_root, _, review_dir = self.make_review_fixture(Path(tmp))
            completed = subprocess.run(
                [
                    sys.executable,
                    "tools/select_voice_candidate.py",
                    "--candidate",
                    "B",
                    "--candidate_review_dir",
                    str(review_dir),
                    "--dry_run",
                ],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            manifest = json.loads(
                (experiment_root / "runs" / "SmokeVoice" / "smoke" / "candidate_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("DRY RUN selected_candidate=candidate_B_epoch1", completed.stdout)
            self.assertIn("DRY RUN selected_checkpoint_json=", completed.stdout)
            self.assertIn("DRY RUN experiment_status=", completed.stdout)
            self.assertFalse((experiment_root / "selected_checkpoint.json").exists())
            self.assertFalse((experiment_root / "experiment_status.json").exists())
            self.assertNotIn("winner_selection", manifest)

    def test_bare_candidate_command_auto_discovers_single_review_pack(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            experiment_root, _, _review_dir = self.make_review_fixture(root)
            script_path = Path("tools/select_voice_candidate.py").resolve()
            completed = subprocess.run(
                [sys.executable, str(script_path), "--candidate", "B"],
                cwd=root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            selected_path = experiment_root / "selected_checkpoint.json"
            selected = json.loads(selected_path.read_text(encoding="utf-8"))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            self.assertIn("selected_candidate=candidate_B_epoch1", completed.stdout)
            self.assertEqual(selected["candidate_label"], "candidate_B_epoch1")
            self.assertEqual(selected["candidate_rank"], 2)

    def test_missing_candidate_writes_no_partial_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            experiment_root, _, review_dir = self.make_review_fixture(Path(tmp))
            args = self.module.create_parser().parse_args(
                ["--candidate", "D", "--candidate_review_dir", str(review_dir)]
            )
            with self.assertRaisesRegex(self.module.SelectionError, "not present in candidates"):
                self.module.select_voice_candidate(args)
            self.assertFalse((experiment_root / "selected_checkpoint.json").exists())
            self.assertFalse((experiment_root / "experiment_status.json").exists())

    def test_local_run_without_experiment_root_writes_under_run_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            _, run_dir, review_dir = self.make_review_fixture(Path(tmp), normal_experiment=False)
            args = self.module.create_parser().parse_args(
                ["--candidate", "2", "--candidate_review_dir", str(review_dir)]
            )
            result = self.module.select_voice_candidate(args)
            self.assertEqual(result.selected_checkpoint_path, run_dir / "selected_checkpoint.json")
            self.assertEqual(result.status_path, run_dir / "experiment_status.json")


if __name__ == "__main__":
    unittest.main()
