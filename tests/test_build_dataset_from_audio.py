from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path


def load_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "build_dataset_from_audio.py"
    scripts_dir = str(path.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("build_dataset_from_audio_for_test", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load module from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BuildDatasetFromAudioTextHygieneTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()

    def quality_args(self) -> types.SimpleNamespace:
        return types.SimpleNamespace(
            low_confidence_threshold=0.5,
            max_low_conf_ratio=0.35,
            min_avg_confidence=0.45,
            min_chars=8,
            min_words=3,
            min_duration=2.0,
            max_duration=14.0,
            voice_filter_mode="silero",
            voice_filter_min_coverage=0.75,
            voice_filter_min_speech_ms=300,
            voice_filter_reject_initial_seconds=0.0,
        )

    def test_subtitle_credit_text_is_detected_as_boilerplate(self) -> None:
        self.assertTrue(self.module.contains_transcript_boilerplate("Субтитры сделал DimaTorzok"))
        self.assertTrue(self.module.contains_transcript_boilerplate("Subtitles by Example Studio"))
        self.assertFalse(self.module.contains_transcript_boilerplate("Сегодня хороший день для ясной речи."))

    def test_segments_with_subtitle_credit_are_rejected(self) -> None:
        words = [
            self.module.WordItem("Сегодня", 0.0, 0.4, 0.95),
            self.module.WordItem("хороший", 0.5, 0.9, 0.95),
            self.module.WordItem("день.", 1.0, 1.4, 0.95),
            self.module.WordItem("Субтитры", 1.5, 2.0, 0.95),
            self.module.WordItem("сделал", 2.1, 2.5, 0.95),
            self.module.WordItem("DimaTorzok", 2.6, 3.0, 0.95),
        ]
        quality = self.module.evaluate_segment_quality(
            words,
            "Сегодня хороший день. Субтитры сделал DimaTorzok",
            source_duration=3.0,
            speech_ratio=1.0,
            args=self.quality_args(),
            start_sec=10.0,
        )
        self.assertIn("transcript_boilerplate", quality.reasons)


if __name__ == "__main__":
    unittest.main()
