# Architecture

## Scope

This repository is a Qwen3-TTS workspace for Sub-task #1:

- adapt one target speaker from Russian source recordings;
- generate English speech with stable speaker identity and natural delivery;
- validate pace, pauses, prosody, and pronunciation using a fixed phrase set.

Synchronization, video alignment, muxing, and full dubbing orchestration are out of scope here.

## Main surfaces

```text
docs/                         Canonical project guidance
scripts/                      Local helper CLIs and shell wrappers
datasets/voices/<Voice>/      Human voice workspace
  Input/                      Raw source recordings for that voice
  Ready/                      Prepared data and generated listening samples
experiments/qwen3_ru_en_speaker_v1/
  manifests/                  Manifest templates and generated JSONL files
  runs/                       Technical scratch for generated training runs/checkpoints
  samples/                    Technical scratch for generated evaluation samples
  notes/                      Small run notes
external/Qwen3-TTS/           Ignored upstream clone
patches/                      Tracked local patches for ignored upstream code
```

## Data flow

1. Put raw source recordings in `datasets/voices/<Voice>/Input/`.
2. Run `scripts/build_dataset_from_audio.py`.
3. The builder converts audio, detects voice regions, removes music/noise/non-speech spans, runs ASR, and writes accepted chunks plus reports under `Ready/<run_name>/`.
4. Validate `train_raw.jsonl` with `scripts/validate_manifest.py`.
5. Run upstream `prepare_data.py` through `scripts/run_prepare_data.sh` to create `train_with_codes.jsonl`.
6. Run SFT through `scripts/run_sft_0_6b.sh` or an equivalent 1.7B command.
7. Generate samples with `scripts/run_infer_sample.py`.
8. Evaluate with `docs/EVAL_PHRASE_SET.md`.

For owner-facing listening files, prefer
`datasets/voices/<Voice>/Ready/<purpose>/<language>/`. Treat `experiments/` as
rebuildable local scratch, not as the place to browse final audio.

## Voice filtering

Voice filtering is part of dataset construction, before ASR:

- default mode is `--voice_filter_mode silero`;
- current implementation uses local Silero VAD first, WebRTC-VAD when installed, and a conservative ffmpeg
  silencedetect fallback only when the model-based VAD path is unavailable;
- strict mode requires full speech coverage unless overridden;
- rejected spans are written to quarantine outputs when enabled.

The manifest schema does not change. Filtering changes which chunks are allowed into the manifest.

## Upstream patching

`external/Qwen3-TTS/` is ignored and may contain local runtime edits.
Tracked patch files in `patches/` are the reproducible record of those edits.

Current patch:

```text
patches/qwen3-tts-sft-runtime-local-model.patch
```

It records the local SFT change that downloads/copies model snapshots correctly and uses `QWEN3_TTS_ATTN_IMPL` with `sdpa` default instead of requiring `flash_attention_2`.

Apply it with:

```bash
git -C external/Qwen3-TTS apply --unidiff-zero ../../patches/qwen3-tts-sft-runtime-local-model.patch
```
