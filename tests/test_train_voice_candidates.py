from __future__ import annotations

import importlib
import json
import subprocess
import sys
import tempfile
import types
import unittest
import wave
from pathlib import Path


class TrainVoiceCandidatesContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = importlib.import_module("tools.train_voice_candidates")

    def test_import_does_not_load_heavy_runtime_modules(self) -> None:
        heavy = {"torch", "qwen_tts", "soundfile", "faster_whisper"}
        before = set(sys.modules)
        importlib.reload(self.module)
        introduced = set(sys.modules) - before
        self.assertFalse(heavy & introduced)

    def test_metric_schema_thresholds_weights_and_backend_modes(self) -> None:
        thresholds = self.module.metric_thresholds_row()
        gate_thresholds = self.module.hard_reject_thresholds_row()
        weights = self.module.metric_weights_row()
        for key in (
            "duration_ratio_min",
            "duration_ratio_max",
            "pace_chars_per_sec_min",
            "pace_chars_per_sec_max",
            "rms_dbfs_min",
            "rms_dbfs_max",
            "clipping_ratio_max",
            "leading_silence_ms_max",
            "trailing_silence_ms_max",
            "whisper_text_match_min",
        ):
            self.assertIn(key, thresholds)
            self.assertIsInstance(thresholds[key], float)
        for key in ("text_match", "pace_duration", "silence", "audio_level", "speaker_similarity", "loss"):
            self.assertIn(key, weights)
            self.assertIsInstance(weights[key], float)
        for key in (
            "asr_text_match_min",
            "pace_acceleration_ratio_max",
            "clipping_ratio_max",
            "duration_ratio_min",
            "duration_ratio_max",
            "suspected_cut_duration_ratio_max",
            "suspected_cut_trailing_silence_ms_max",
            "score_drop_max",
        ):
            self.assertIn(key, gate_thresholds)
            self.assertIsInstance(gate_thresholds[key], float)
        self.assertEqual(self.module.METRIC_EVENT_SAMPLE, "sample_metrics")
        self.assertEqual(self.module.METRIC_EVENT_CHECKPOINT_SCORE, "checkpoint_score")
        self.assertEqual(self.module.METRIC_EVENT_CHECKPOINT_GATE, "checkpoint_gate")
        self.assertEqual(self.module.METRIC_EVENT_CANDIDATE_SELECTION, "candidate_selection")
        self.assertEqual(self.module.resolve_backend_mode("auto", "stub"), "stub")
        self.assertEqual(self.module.resolve_backend_mode("auto", "real"), "off")
        self.assertEqual(self.module.resolve_backend_mode("faster-whisper", "real"), "faster-whisper")
        self.assertEqual(self.module.clamp_score(123.4), 100.0)
        self.assertEqual(self.module.clamp_score(-2.0), 0.0)

    def test_metric_rows_serialize_required_contract_fields(self) -> None:
        sample = self.module.SampleMetrics(
            epoch=0,
            label="en_short",
            output_path="/tmp/01.wav",
            duration_seconds=1.0,
            expected_duration_seconds=1.1,
            duration_ratio=0.91,
            pace_chars_per_sec=12.0,
            pace_words_per_sec=3.0,
            rms_dbfs=-18.0,
            clipping_ratio=0.0,
            leading_silence_ms=100.0,
            trailing_silence_ms=120.0,
            whisper_text_match=1.0,
            speaker_similarity=None,
            warnings=("speaker_similarity_unavailable",),
            metric_backend="stub",
        ).to_row()
        for key in (
            "event",
            "duration_seconds",
            "expected_duration_seconds",
            "duration_ratio",
            "pace_chars_per_sec",
            "pace_words_per_sec",
            "rms_dbfs",
            "clipping_ratio",
            "leading_silence_ms",
            "trailing_silence_ms",
            "whisper_text_match",
            "speaker_similarity",
            "warnings",
        ):
            self.assertIn(key, sample)
        score = self.module.CheckpointScore(
            epoch=0,
            checkpoint_path="/tmp/checkpoint",
            sample_count=1,
            score=88.0,
            metric_summary={"duration_ratio_mean": 0.91},
            warnings=("missing_loss",),
        ).to_row()
        self.assertEqual(score["event"], "checkpoint_score")
        self.assertIsInstance(score["score"], float)
        self.assertIsInstance(score["warnings"], list)
        gate = self.module.CheckpointGate(
            epoch=0,
            checkpoint_path="/tmp/checkpoint",
            hard_rejected=True,
            reject_reasons=("text_mismatch",),
            warning_reasons=("missing_loss",),
            score=42.0,
            metric_summary={"whisper_text_match_mean": 0.2},
            comparison={"previous_viable_epoch": None},
        ).to_row()
        for key in (
            "event",
            "epoch",
            "checkpoint_path",
            "hard_rejected",
            "reject_reasons",
            "warning_reasons",
            "score",
            "metric_summary",
        ):
            self.assertIn(key, gate)
        self.assertEqual(gate["event"], "checkpoint_gate")
        self.assertIsInstance(gate["reject_reasons"], list)
        selection = self.module.CandidateSelection(
            selected_epochs=(1, 3),
            rejected_epochs=(0, 2),
            limited=False,
            candidate_count=2,
            rejected_count=2,
            manifest_path="/tmp/candidate_manifest.json",
        ).to_row()
        self.assertEqual(selection["event"], "candidate_selection")
        self.assertEqual(selection["selected_epochs"], [1, 3])
        self.assertEqual(selection["rejected_epochs"], [0, 2])

    def test_path_model_is_deterministic(self) -> None:
        paths = self.module.build_paths(Path("/tmp/out"), "Baritone", "smoke")
        self.assertEqual(paths.run_dir, Path("/tmp/out/Baritone/smoke"))
        self.assertEqual(paths.prepared_manifest, Path("/tmp/out/Baritone/smoke/manifests/train_with_codes.jsonl"))
        self.assertEqual(paths.metrics_jsonl, Path("/tmp/out/Baritone/smoke/metrics.jsonl"))
        self.assertEqual(paths.candidate_manifest, Path("/tmp/out/Baritone/smoke/candidate_manifest.json"))
        self.assertEqual(paths.epoch_run_dir(0), Path("/tmp/out/Baritone/smoke/train/epoch-0"))
        self.assertEqual(
            paths.epoch_checkpoint_path(0),
            Path("/tmp/out/Baritone/smoke/train/epoch-0/checkpoint-epoch-0"),
        )
        self.assertEqual(paths.promoted_checkpoint_path(0), Path("/tmp/out/Baritone/smoke/checkpoints/epoch-0"))
        self.assertEqual(paths.epoch_eval_dir(0), Path("/tmp/out/Baritone/smoke/eval/epoch-0"))
        self.assertEqual(paths.command_log_path("train", 0), Path("/tmp/out/Baritone/smoke/logs/train-epoch-0.log"))

    def test_default_eval_phrase_filenames(self) -> None:
        filenames = [phrase.filename for phrase in self.module.DEFAULT_EVAL_PHRASES]
        self.assertEqual(
            filenames,
            [
                "01_en_short.wav",
                "02_en_long.wav",
                "03_en_calm.wav",
                "04_ru_short.wav",
                "05_ru_long.wav",
            ],
        )

    def test_eval_phrases_have_three_english_and_two_russian_prompts(self) -> None:
        languages = [phrase.language for phrase in self.module.DEFAULT_EVAL_PHRASES]
        self.assertEqual(languages.count("english"), 3)
        self.assertEqual(languages.count("russian"), 2)
        self.assertTrue(all(phrase.text for phrase in self.module.DEFAULT_EVAL_PHRASES))

    def test_inference_command_includes_checkpoint_speaker_text_language_and_output(self) -> None:
        parser = self.module.create_parser()
        args = parser.parse_args(
            [
                "--voice_name",
                "Baritone",
                "--train_raw_jsonl",
                "/tmp/train_raw.jsonl",
                "--output_root",
                "/tmp/out",
                "--speaker_name",
                "speaker_target",
                "--python_executable",
                "/tmp/python",
            ]
        )
        phrase = self.module.DEFAULT_EVAL_PHRASES[0]
        command = self.module.build_infer_command(
            args,
            Path("/tmp/checkpoint"),
            phrase,
            Path("/tmp/out/01_en_short.wav"),
        )
        self.assertIn("--checkpoint", command)
        self.assertIn("/tmp/checkpoint", command)
        self.assertIn("--speaker", command)
        self.assertIn("speaker_target", command)
        self.assertIn("--text", command)
        self.assertIn(phrase.text, command)
        self.assertIn("--language", command)
        self.assertIn(phrase.language, command)
        self.assertIn("--output_wav", command)
        self.assertIn("/tmp/out/01_en_short.wav", command)

    def test_cli_help_contains_required_options(self) -> None:
        completed = subprocess.run(
            [sys.executable, "tools/train_voice_candidates.py", "--help"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        for option in (
            "--voice_name",
            "--train_raw_jsonl",
            "--output_root",
            "--run_name",
            "--max_epochs",
            "--top_candidates",
            "--speaker_name",
            "--hard_reject_text_match_min",
            "--hard_reject_pace_acceleration_max",
            "--hard_reject_score_drop_max",
        ):
            self.assertIn(option, completed.stdout)

    def test_stub_run_creates_checkpoint_eval_pack_and_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_manifest = tmp_path / "train_raw.jsonl"
            raw_manifest.write_text(
                json.dumps(
                    {
                        "audio": "sample.wav",
                        "text": "hello",
                        "ref_audio": "sample.wav",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    str(raw_manifest),
                    "--output_root",
                    str(tmp_path / "out"),
                    "--run_name",
                    "smoke",
                    "--max_epochs",
                    "1",
                    "--speaker_name",
                    "speaker_target",
                    "--execution_mode",
                    "stub",
                ]
            )
            paths = self.module.orchestrate(args)
            self.assertTrue(paths.prepared_manifest.exists())
            self.assertTrue((paths.epoch_checkpoint_path(0) / "STUB_CHECKPOINT.txt").exists())
            eval_files = sorted(path.name for path in paths.epoch_eval_dir(0).iterdir())
            self.assertEqual(
                eval_files,
                [
                    "01_en_short.wav",
                    "02_en_long.wav",
                    "03_en_calm.wav",
                    "04_ru_short.wav",
                    "05_ru_long.wav",
                ],
            )
            rows = self.module.read_metrics(paths.metrics_jsonl)
            events = [row["event"] for row in rows]
            self.assertIn("prepare_end", events)
            self.assertIn("train_start", events)
            self.assertIn("checkpoint", events)
            self.assertIn("checkpoint_score", events)
            self.assertIn("checkpoint_gate", events)
            self.assertIn("candidate_selection", events)
            self.assertTrue(paths.candidate_manifest.exists())
            eval_rows = [row for row in rows if row["event"] == "eval_sample"]
            sample_metric_rows = [row for row in rows if row["event"] == "sample_metrics"]
            self.assertEqual(len(eval_rows), 5)
            self.assertEqual(len(sample_metric_rows), 5)
            self.assertEqual(
                sorted(Path(row["output_path"]).name for row in eval_rows),
                [
                    "01_en_short.wav",
                    "02_en_long.wav",
                    "03_en_calm.wav",
                    "04_ru_short.wav",
                    "05_ru_long.wav",
                ],
            )
            checkpoint_rows = [row for row in rows if row["event"] == "checkpoint"]
            self.assertEqual(checkpoint_rows[0]["epoch"], 0)
            self.assertIn("checkpoint_path", checkpoint_rows[0])
            score_rows = [row for row in rows if row["event"] == "checkpoint_score"]
            self.assertEqual(len(score_rows), 1)
            self.assertIsInstance(score_rows[0]["score"], float)
            self.assertGreaterEqual(score_rows[0]["score"], 0.0)
            self.assertLessEqual(score_rows[0]["score"], 100.0)
            self.assertEqual(score_rows[0]["sample_count"], 5)
            self.assertIsInstance(score_rows[0]["warnings"], list)
            self.assertIn("metric_summary", score_rows[0])
            gate_rows = [row for row in rows if row["event"] == "checkpoint_gate"]
            self.assertEqual(len(gate_rows), 1)
            self.assertFalse(gate_rows[0]["hard_rejected"])
            self.assertEqual(gate_rows[0]["reject_reasons"], [])
            selection_rows = [row for row in rows if row["event"] == "candidate_selection"]
            self.assertEqual(selection_rows[0]["selected_epochs"], [0])
            manifest = json.loads(paths.candidate_manifest.read_text(encoding="utf-8"))
            self.assertEqual([candidate["epoch"] for candidate in manifest["candidates"]], [0])
            self.assertEqual(manifest["rejected_checkpoints"], [])
            for row in sample_metric_rows:
                for key in (
                    "duration_seconds",
                    "expected_duration_seconds",
                    "duration_ratio",
                    "pace_chars_per_sec",
                    "pace_words_per_sec",
                    "rms_dbfs",
                    "clipping_ratio",
                    "leading_silence_ms",
                    "trailing_silence_ms",
                ):
                    self.assertIsInstance(row[key], float)

    def test_audio_metrics_detect_clipping_and_silence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            wav_path = tmp_path / "clipped.wav"
            sample_rate = 16000
            with wave.open(str(wav_path), "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                frames = bytearray()
                for _ in range(int(sample_rate * 0.8)):
                    frames.extend((0).to_bytes(2, "little", signed=True))
                for _ in range(int(sample_rate * 0.2)):
                    frames.extend((32767).to_bytes(2, "little", signed=True))
                for _ in range(int(sample_rate * 1.0)):
                    frames.extend((0).to_bytes(2, "little", signed=True))
                wav_file.writeframes(bytes(frames))
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    "/tmp/train_raw.jsonl",
                    "--output_root",
                    "/tmp/out",
                    "--execution_mode",
                    "stub",
                ]
            )
            metrics = self.module.compute_sample_metrics(
                args,
                0,
                self.module.DEFAULT_EVAL_PHRASES[0],
                wav_path,
            )
            self.assertGreater(metrics.clipping_ratio, 0.0)
            self.assertGreaterEqual(metrics.leading_silence_ms, 700.0)
            self.assertIn("clipping_detected", metrics.warnings)
            self.assertIn("leading_silence_too_long", metrics.warnings)

    def test_loss_summary_parses_loss_values_and_warns_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.module.build_paths(Path(tmp) / "out", "Baritone", "loss")
            paths.logs_dir.mkdir(parents=True)
            paths.command_log_path("train", 0).write_text(
                "Epoch 0 | Step 0 | Loss: 2.5000\nEpoch 0 | Step 10 | Loss: 1.2500\n",
                encoding="utf-8",
            )
            summary = self.module.loss_summary_for_epoch(paths, 0)
            self.assertEqual(summary.loss_last, 1.25)
            self.assertEqual(summary.loss_min, 1.25)
            self.assertEqual(summary.warnings, ())
            missing = self.module.loss_summary_for_epoch(paths, 1)
            self.assertIsNone(missing.loss_last)
            self.assertIsNone(missing.loss_min)
            self.assertIn("missing_loss", missing.warnings)

    def test_checkpoint_score_bounds_and_warning_generation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = self.module.build_paths(tmp_path / "out", "Baritone", "score")
            self.module.ensure_run_dirs(paths)
            self.module.append_metrics(
                paths.metrics_jsonl,
                event="sample_metrics",
                epoch=0,
                label="bad",
                output_path="/tmp/bad.wav",
                duration_seconds=0.25,
                expected_duration_seconds=2.0,
                duration_ratio=0.125,
                pace_chars_per_sec=80.0,
                pace_words_per_sec=20.0,
                rms_dbfs=-3.0,
                clipping_ratio=0.5,
                leading_silence_ms=1000.0,
                trailing_silence_ms=1200.0,
                whisper_text_match=0.1,
                speaker_similarity=None,
                warnings=["speaker_similarity_unavailable"],
                metric_backend="audio",
            )
            score = self.module.score_checkpoint(paths, 0, Path("/tmp/checkpoint"))
            self.assertGreaterEqual(score.score, 0.0)
            self.assertLessEqual(score.score, 100.0)
            self.assertLess(score.score, 100.0)
            for warning in (
                "duration_ratio_too_low",
                "pace_too_fast",
                "audio_too_loud",
                "clipping_detected",
                "leading_silence_too_long",
                "trailing_silence_too_long",
                "text_match_too_low",
                "missing_loss",
                "speaker_similarity_unavailable",
            ):
                self.assertIn(warning, score.warnings)

    def test_checkpoint_gate_rejects_user_requested_bad_conditions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            paths = self.module.build_paths(tmp_path / "out", "Baritone", "gates")
            self.module.ensure_run_dirs(paths)
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    "/tmp/train_raw.jsonl",
                    "--output_root",
                    "/tmp/out",
                    "--execution_mode",
                    "stub",
                ]
            )
            previous = self.module.CheckpointGate(
                epoch=0,
                checkpoint_path="/tmp/checkpoint-0",
                hard_rejected=False,
                reject_reasons=(),
                warning_reasons=(),
                score=96.0,
                metric_summary={
                    "duration_ratio_mean": 1.0,
                    "pace_chars_per_sec_mean": 10.0,
                    "clipping_ratio_max": 0.0,
                    "trailing_silence_ms_max": 220.0,
                    "whisper_text_match_mean": 1.0,
                },
                comparison={},
            )
            self.module.append_metrics(paths.metrics_jsonl, **previous.to_row())
            bad_score = self.module.CheckpointScore(
                epoch=1,
                checkpoint_path="/tmp/checkpoint-1",
                sample_count=5,
                score=60.0,
                metric_summary={
                    "duration_ratio_mean": 0.75,
                    "pace_chars_per_sec_mean": 13.0,
                    "clipping_ratio_max": 0.2,
                    "leading_silence_ms_max": 120.0,
                    "trailing_silence_ms_max": 20.0,
                    "whisper_text_match_mean": 0.2,
                    "speaker_similarity_mean": None,
                    "loss_last": 1.0,
                    "loss_min": 1.0,
                },
                warnings=("text_match_too_low", "clipping_detected"),
            )
            gate = self.module.evaluate_checkpoint_gate(args, paths, bad_score)
            for reason in (
                "asr_text_mismatch",
                "audio_clipping",
                "pace_accelerated",
                "suspected_cut",
                "score_drop",
            ):
                self.assertIn(reason, gate.reject_reasons)
            self.assertTrue(gate.hard_rejected)
            self.assertEqual(gate.comparison["previous_viable_epoch"], 0)

    def test_checkpoint_gate_rejects_duration_too_short_and_too_long(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.module.build_paths(Path(tmp) / "out", "Baritone", "duration")
            self.module.ensure_run_dirs(paths)
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    "/tmp/train_raw.jsonl",
                    "--output_root",
                    "/tmp/out",
                    "--execution_mode",
                    "stub",
                ]
            )
            short_score = self.module.CheckpointScore(
                epoch=0,
                checkpoint_path="/tmp/short",
                sample_count=5,
                score=88.0,
                metric_summary={
                    "duration_ratio_mean": 0.5,
                    "pace_chars_per_sec_mean": 10.0,
                    "clipping_ratio_max": 0.0,
                    "trailing_silence_ms_max": 220.0,
                    "whisper_text_match_mean": 1.0,
                },
                warnings=(),
            )
            long_score = self.module.CheckpointScore(
                epoch=1,
                checkpoint_path="/tmp/long",
                sample_count=5,
                score=88.0,
                metric_summary={
                    "duration_ratio_mean": 1.8,
                    "pace_chars_per_sec_mean": 10.0,
                    "clipping_ratio_max": 0.0,
                    "trailing_silence_ms_max": 220.0,
                    "whisper_text_match_mean": 1.0,
                },
                warnings=(),
            )
            self.assertIn("duration_too_short", self.module.evaluate_checkpoint_gate(args, paths, short_score).reject_reasons)
            self.assertIn("duration_too_long", self.module.evaluate_checkpoint_gate(args, paths, long_score).reject_reasons)

    def test_candidate_selection_excludes_rejected_high_score_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.module.build_paths(Path(tmp) / "out", "Baritone", "selection")
            self.module.ensure_run_dirs(paths)
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    "/tmp/train_raw.jsonl",
                    "--output_root",
                    "/tmp/out",
                    "--execution_mode",
                    "stub",
                    "--top_candidates",
                    "4",
                ]
            )
            rejected = self.module.CheckpointGate(
                epoch=0,
                checkpoint_path="/tmp/run/train/epoch-0/checkpoint-epoch-0",
                hard_rejected=True,
                reject_reasons=("asr_text_mismatch",),
                warning_reasons=(),
                score=99.0,
                metric_summary={"pace_chars_per_sec_mean": 10.0},
                comparison={},
            )
            viable = self.module.CheckpointGate(
                epoch=1,
                checkpoint_path="/tmp/run/train/epoch-1/checkpoint-epoch-0",
                hard_rejected=False,
                reject_reasons=(),
                warning_reasons=("missing_loss",),
                score=80.0,
                metric_summary={"pace_chars_per_sec_mean": 10.0},
                comparison={},
            )
            self.module.append_metrics(paths.metrics_jsonl, **rejected.to_row())
            self.module.append_metrics(paths.metrics_jsonl, **viable.to_row())
            selection = self.module.append_candidate_selection(args, paths)
            manifest = json.loads(paths.candidate_manifest.read_text(encoding="utf-8"))
            self.assertEqual(selection.selected_epochs, (1,))
            self.assertEqual(selection.rejected_epochs, (0,))
            self.assertEqual([candidate["epoch"] for candidate in manifest["candidates"]], [1])
            self.assertEqual([row["epoch"] for row in manifest["rejected_checkpoints"]], [0])

    def test_candidate_selection_limited_when_no_viable_checkpoint_exists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            paths = self.module.build_paths(Path(tmp) / "out", "Baritone", "empty")
            self.module.ensure_run_dirs(paths)
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    "/tmp/train_raw.jsonl",
                    "--output_root",
                    "/tmp/out",
                    "--execution_mode",
                    "stub",
                ]
            )
            rejected = self.module.CheckpointGate(
                epoch=0,
                checkpoint_path="/tmp/run/train/epoch-0/checkpoint-epoch-0",
                hard_rejected=True,
                reject_reasons=("audio_clipping",),
                warning_reasons=(),
                score=50.0,
                metric_summary={},
                comparison={},
            )
            self.module.append_metrics(paths.metrics_jsonl, **rejected.to_row())
            selection = self.module.append_candidate_selection(args, paths)
            manifest = json.loads(paths.candidate_manifest.read_text(encoding="utf-8"))
            self.assertTrue(selection.limited)
            self.assertEqual(selection.selected_epochs, ())
            self.assertEqual(manifest["status"], "limited")
            self.assertEqual(manifest["candidates"], [])
            self.assertEqual([row["epoch"] for row in manifest["rejected_checkpoints"]], [0])

    def test_speaker_similarity_stub_contributes_numeric_value(self) -> None:
        args = self.module.create_parser().parse_args(
            [
                "--voice_name",
                "Baritone",
                "--train_raw_jsonl",
                "/tmp/train_raw.jsonl",
                "--output_root",
                "/tmp/out",
                "--execution_mode",
                "stub",
                "--speaker_similarity_backend",
                "stub",
            ]
        )
        similarity, warnings = self.module.speaker_similarity_for_sample(args)
        self.assertIsInstance(similarity, float)
        self.assertEqual(warnings, ())

    def test_faster_whisper_text_match_backend_is_lazy_and_numeric(self) -> None:
        phrase_text = self.module.DEFAULT_EVAL_PHRASES[0].text

        class FakeSegment:
            text = phrase_text

        class FakeWhisperModel:
            def __init__(self, model_name: str, device: str, compute_type: str) -> None:
                self.model_name = model_name
                self.device = device
                self.compute_type = compute_type

            def transcribe(self, *_args, **_kwargs):
                return [FakeSegment()], object()

        previous_module = sys.modules.get("faster_whisper")
        sys.modules["faster_whisper"] = types.SimpleNamespace(WhisperModel=FakeWhisperModel)
        self.module._TEXT_MATCH_MODELS.clear()
        try:
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    "/tmp/train_raw.jsonl",
                    "--output_root",
                    "/tmp/out",
                    "--execution_mode",
                    "real",
                    "--text_match_backend",
                    "faster-whisper",
                    "--text_match_model",
                    "fake-model",
                    "--text_match_device",
                    "cpu",
                    "--text_match_compute_type",
                    "int8",
                ]
            )
            match, warnings = self.module.text_match_for_phrase(
                args,
                self.module.DEFAULT_EVAL_PHRASES[0],
                Path("/tmp/eval.wav"),
            )
        finally:
            self.module._TEXT_MATCH_MODELS.clear()
            if previous_module is None:
                sys.modules.pop("faster_whisper", None)
            else:
                sys.modules["faster_whisper"] = previous_module

        self.assertEqual(match, 1.0)
        self.assertEqual(warnings, ())

    def test_epoch_one_uses_previous_checkpoint_in_stub_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_manifest = tmp_path / "train_raw.jsonl"
            raw_manifest.write_text('{"audio":"a.wav","text":"hello","ref_audio":"a.wav"}\n', encoding="utf-8")
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    str(raw_manifest),
                    "--output_root",
                    str(tmp_path / "out"),
                    "--run_name",
                    "two_epochs",
                    "--max_epochs",
                    "2",
                    "--execution_mode",
                    "stub",
                ]
            )
            paths = self.module.orchestrate(args)
            train_start_rows = [
                row for row in self.module.read_metrics(paths.metrics_jsonl) if row["event"] == "train_start"
            ]
            self.assertEqual(train_start_rows[0]["init_model_path"], self.module.DEFAULT_BASE_MODEL)
            self.assertIn("checkpoints/epoch-0", train_start_rows[1]["init_model_path"])

    def test_command_failure_stops_run_and_records_failure_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            raw_manifest = tmp_path / "train_raw.jsonl"
            raw_manifest.write_text('{"audio":"a.wav","text":"hello","ref_audio":"a.wav"}\n', encoding="utf-8")
            failing_prepare = tmp_path / "failing_prepare.sh"
            failing_prepare.write_text("#!/usr/bin/env bash\nexit 7\n", encoding="utf-8")
            failing_prepare.chmod(0o755)
            args = self.module.create_parser().parse_args(
                [
                    "--voice_name",
                    "Baritone",
                    "--train_raw_jsonl",
                    str(raw_manifest),
                    "--output_root",
                    str(tmp_path / "out"),
                    "--run_name",
                    "failure",
                    "--max_epochs",
                    "1",
                    "--execution_mode",
                    "real",
                    "--prepare_command",
                    str(failing_prepare),
                ]
            )
            with self.assertRaises(self.module.OrchestrationError):
                self.module.orchestrate(args)
            paths = self.module.build_paths(tmp_path / "out", "Baritone", "failure")
            rows = self.module.read_metrics(paths.metrics_jsonl)
            prepare_end = [row for row in rows if row["event"] == "prepare_end"][0]
            self.assertEqual(prepare_end["status"], "failed")
            self.assertEqual(prepare_end["returncode"], 7)
            self.assertIn("started_at", prepare_end)
            self.assertIn("finished_at", prepare_end)
            self.assertEqual(rows[-1]["event"], "failure")
            self.assertFalse(any(row["event"] == "train_start" for row in rows))


if __name__ == "__main__":
    unittest.main()
