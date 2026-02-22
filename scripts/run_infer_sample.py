#!/usr/bin/env python3
"""Quick inference check for a fine-tuned Qwen3-TTS checkpoint."""

from __future__ import annotations

import argparse
from pathlib import Path

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True, help="Path to checkpoint directory")
    parser.add_argument("--speaker", required=True, help="Speaker name used in training")
    parser.add_argument("--text", default="She said she would be here by noon.", help="English test text")
    parser.add_argument("--output_wav", required=True, help="Output wav path")
    parser.add_argument("--device", default="cuda:0", help="Torch device")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = Path(args.output_wav)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tts = Qwen3TTSModel.from_pretrained(
        args.checkpoint,
        device_map=args.device,
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
    )

    wavs, sr = tts.generate_custom_voice(text=args.text, speaker=args.speaker)
    sf.write(str(output_path), wavs[0], sr)
    print(f"Wrote sample: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
