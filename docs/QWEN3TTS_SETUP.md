# Qwen3TTS Setup Guide (Environment + Dependencies + Baseline Model)

## Purpose

This guide defines a reproducible setup path for Sub-task #1:
- train/adapt a single-speaker model from RU voice data,
- generate EN speech with high speaker similarity and naturalness,
- evaluate controllability (pace/pauses/prosody).

Out of scope: synchronization and dubbing pipeline.

---

## 1) Preconditions

- Linux host with NVIDIA GPU (24GB VRAM expected).
- Python 3.12 available.
- `ffmpeg` installed.
- `sox` binary installed on the host (`sox --version`).
- Network access to PyPI and Hugging Face.

---

## 2) Repository root

All commands are expected to run from:

```bash
/ai/Qwen3TTS
```

---

## 3) Python environment

Create or recreate a clean virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

---

## 4) Install dependencies

Project dependencies are defined in `requirements.txt`:

```txt
qwen-tts
soundfile
```

Pinned installation snapshot (generated after install):

```text
requirements.lock.txt
```

Install:

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

Optional (recommended when supported):

```bash
source .venv/bin/activate
pip install -U flash-attn --no-build-isolation
```

If host RAM is limited:

```bash
source .venv/bin/activate
MAX_JOBS=4 pip install -U flash-attn --no-build-isolation
```

Important:
- FlashAttention is optional for correctness, but useful for speed/VRAM.
- In the current host state, `flash-attn` installation failed due CUDA toolchain mismatch (`CUDA 13.0` detected vs `torch` built with `CUDA 12.8`).

---

## 5) Verify runtime

```bash
source .venv/bin/activate
python -c "import torch; print(torch.__version__)"
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'no cuda')"
python -c "from qwen_tts import Qwen3TTSModel; print('qwen_tts_ok')"
```

---

## 6) Baseline model and tokenizer

Baseline model for first run:
- `Qwen/Qwen3-TTS-12Hz-0.6B-Base`

Current working smoke-train track:
- `Qwen/Qwen3-TTS-12Hz-1.7B-Base` (0.6B path currently has shape mismatch in upstream script)

Tokenizer for preprocessing:
- `Qwen/Qwen3-TTS-Tokenizer-12Hz`

Optional pre-download (to avoid lazy-download delays later):

```bash
source .venv/bin/activate
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-TTS-12Hz-0.6B-Base')"
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-TTS-Tokenizer-12Hz')"
```

---

## 7) Fine-tuning scripts source

Qwen fine-tuning scripts (`prepare_data.py`, `sft_12hz.py`) are provided by upstream repository.

Recommended local placement:

```text
/ai/Qwen3TTS/external/Qwen3-TTS/finetuning
```

Clone command:

```bash
git clone https://github.com/QwenLM/Qwen3-TTS.git external/Qwen3-TTS
```

---

## 8) First-run scope (after dataset handoff)

Once dataset is ready, workflow will be:
1. Build `train_raw.jsonl`.
2. Run `prepare_data.py` -> `train_with_codes.jsonl`.
3. Run `sft_12hz.py` with 0.6B init model.
4. Run fixed prompt inference pack for quality/control checks.

See implementation plan:
- `docs/QWEN3TTS_IMPLEMENTATION_PLAN.md`

See dataset requirements:
- `docs/DATASET_CONTRACT.md`

Use script wrappers:
- `scripts/README.md`

---

## 9) Notes for independent developers

- Do not commit dataset or secrets.
- Keep all run outputs under `experiments/`.
- Update `docs/PROJECT_STATUS.md` after every meaningful change.
- If setup deviates from this guide, document exact delta and reason.

---

## 10) Current server execution status (latest run)

Completed on `/ai/Qwen3TTS`:
- `.venv` created and pip tooling upgraded.
- `requirements.txt` installed successfully.
- `external/Qwen3-TTS` cloned successfully.
- Runtime import checks passed (`qwen_tts_ok`, CUDA visible).
- `sox` installed and verified (`sox --version`).
- Baseline model and tokenizer downloaded from Hugging Face:
  - `Qwen/Qwen3-TTS-12Hz-0.6B-Base`
  - `Qwen/Qwen3-TTS-Tokenizer-12Hz`

Open blockers:
1. `flash-attn` build failed due CUDA mismatch (`13.0` vs `12.8`).
2. `0.6B` fine-tune path currently fails with embedding shape mismatch in upstream script.
