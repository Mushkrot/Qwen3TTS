# Voice Cloning / TTS Projects Audit (as of 2026-02-21)

## 0) Подробная постановка задачи (на русском)

### Что нужно сделать
Нужно вернуться к проекту клонирования голоса и сделать рабочую систему, которая обучается на **большом датасете русского оригинального голоса** и затем генерирует речь на **английском языке** с максимально похожим тембром и характером оригинального спикера.

Целевой сценарий: есть много русскоязычных видео-лекций, и нужно подготовить их англоязычный дубляж тем же голосом, чтобы итоговая дорожка звучала естественно и была пригодна для публикации.

### Ключевые нюансы задачи
1. **Источник голоса — русский, синтез — английский.**
   Ранее часть моделей плохо обрабатывала русский голос как reference/original speaker input. Сейчас важно выбрать и/или дообучить такой стек, который устойчиво работает именно с этим кросс-языковым сценарием.

2. **Главный приоритет — похожесть на оригинал и натуральность.**
   Требуется не просто generic voice clone по 3–10 секундному примеру, а максимально правдоподобная передача тембра и манеры исходного спикера при длинной работе на реальном контенте.

3. **Очень важен control над ритмом речи:**
   - **pace (темп),**
   - **pauses (паузы),**
   - **prosody (интонационно-ритмический рисунок).**

   Это критично, потому что английский язык компактнее русского: на длинных фрагментах англоязычная дорожка часто уходит слишком рано вперёд. Нужно уметь замедлять/структурировать речь без заметной потери натуральности.

4. **Требования к синхронизации — по блокам, не lip-sync.**
   На видео нет лица человека (научные схемы), поэтому покадровая синхронизация губ не нужна.
   Допустимы расхождения в несколько секунд, но на длинных сегментах недопустим системный увод тайминга из-за слишком быстрого чтения английского текста.

5. **Ограничения по ресурсам изменились.**
   Ранее часть перспективных моделей не помещалась в VRAM, сейчас доступна GPU 24GB, поэтому можно вернуться к более тяжёлым моделям и сравнить их с прежними решениями.

6. **Можно опираться на уже сделанное, но можно поискать совсем новые современные подходы.**
   В директории `/ai` есть несколько старых/параллельных попыток (XTTS, GPT-SoVITS, Tortoise, OpenVoice, Zonos, pipeline-проекты). Можно посмотреть одновления по текущим моделям или найти совсем новые и начать заново. Требуется найти оптималоьный подход под решение задачи.

### Что уже сделано в рамках текущего шага
В этом отчёте собран аудит имеющихся проектов и документации, чтобы зафиксировать отправную точку: какие репозитории релевантны, какие результаты уже существуют, и какие направления наиболее перспективны для возобновления работ.

### Приоритет следующего этапа обсуждения
1. Уточнить основной трек и резервный трек (например, XTTS как continuity + современная альтернатива для stronger control).
2. Зафиксировать практический подход к управлению pace/pauses/prosody при сохранении naturalness.
3. Определить, как встроить выбранную TTS-модель в pipeline дубляжа с синхронизацией по блокам.

## 1) Goal of this audit

This document summarizes the current state of all discovered projects in `/ai` related to:
- voice cloning,
- speaker adaptation / fine-tuning,
- cross-lingual synthesis,
- and dubbing pipeline support (timing/speed control).

Focus is on your target use case:
- source voice data in Russian,
- generated speech in English,
- high voice similarity,
- practical sync with lecture videos (without lip-sync constraints).

---

## 2) What was found in `/ai`

Primary relevant project groups:

1. `xtts-finetune-webui`
2. `vits` (Coqui + AllTalk + internal docs)
3. `vits (GPT-SoVITS) 1`
4. `vits (GPT-SoVITS) 2`
5. `tort (Tortoise TTS)`
6. `ov/OpenVoice`
7. `zonos/Zonos`
8. `whisperdub` (pipeline/docs with sync emphasis)

Non-core repositories were intentionally excluded from deep analysis.

---

## 3) Per-project status and findings

## 3.1 `xtts-finetune-webui`

### Evidence and current state
- Project exists and is installable with Linux scripts and headless mode (`README.md`).
- Key features include dataset append, VAD, language tracking, base-model selection, and optimized export.
- Local artifact presence confirms at least one completed fine-tuned export:
  - `finetune_models/ready/config.json`
  - `finetune_models/ready/speakers_xtts.pth`
  - `finetune_models/ready/vocab.json`
- `finetune_models/run/training` is currently empty.

### Important technical notes
- Config in `ready/config.json` indicates XTTS multilingual language list includes `ru` and `en`.
- Inference controls exist (temperature, top_k/top_p etc.) but direct hard timing alignment control is limited at model level.

### Practical assessment
- **Strong candidate** for your use case due to multilingual XTTS base + known workflow.
- Exported artifacts show this path already produced reusable model output.
- Better operational fit than raw/manual training stacks.

---

## 3.2 `vits` (Coqui + AllTalk + internal docs)

### Evidence and current state
- Contains Coqui TTS source (`src`) and AllTalk TTS integration (`alltalk_tts`).
- Internal roadmap explicitly states migration from VITS to XTTS v2 because of Russian model limitations.
- Historical XTTS fine-tune runs exist in:
  - `alltalk_tts/finetune/tmp-trn/training/...`
- Example run folders contain large model checkpoints (`best_model*.pth` around 5.59 GB).
- Logs confirm model training executed and loss decreased across epochs.

### Practical assessment
- This workspace is your **most informative historical baseline** (what worked / what failed).
- Confirms that fine-tuning pipeline ran end-to-end and produced checkpoints.
- AllTalk limitations (resume flexibility, dataset refresh ergonomics, hyperparameter constraints) are documented and align with your reported pain points.

---

## 3.3 `vits (GPT-SoVITS) 1`

### Evidence and current state
- Contains full GPT-SoVITS code + backups + local docs.
- Root-level model artifact found:
  - `GPT-SoVITS/SoVITS_weights/G_233333333333.pth`
- In many GPT/SoVITS v2/v3 subfolders, weight directories are empty.
- Internal roadmap/docs show partial pipeline progress and heavy manual setup.

### Practical assessment
- This repo appears to be an **older experimental track** with partial outcomes.
- There is at least one trained SoVITS checkpoint, but project state is fragmented.
- Good for retrospective lessons, but not the cleanest restart point without cleanup.

---

## 3.4 `vits (GPT-SoVITS) 2`

### Evidence and current state
- Contains GPT-SoVITS code and docs/changelog.
- Weight directories (`GPT_weights*`, `SoVITS_weights*`) are currently empty.
- Upstream changelog (through 2025) includes:
  - multilingual handling improvements,
  - speech-rate support,
  - lower VRAM paths (v3 + gradient checkpointing + LoRA notes).

### Practical assessment
- Promising from upstream capability evolution.
- Locally appears mostly as codebase setup without completed trained artifacts.
- Could become main candidate if you choose GPT-SoVITS v3/LoRA path on 24 GB GPU.

---

## 3.5 `tort (Tortoise TTS)`

### Evidence and current state
- Fine-tuning framework exists (`tune_tortoise_autoregressor`).
- Training history present under:
  - `fine_tuning/training/russian_voice`
  - many archived finetune snapshots.
- Current active finetune folder contains logs/config, but no `.pth` output found in scanned depth.
- Log shows very small dataset size (14 samples) and conservative training setup.

### Practical assessment
- You clearly invested effort here, but current observable outputs look incomplete for production.
- Historically known to be heavy/slow and difficult operationally.
- With 24 GB GPU it is more feasible, but still likely worse ROI than XTTS/GPT-SoVITS for your current objective.

---

## 3.6 `ov/OpenVoice`

### Evidence and current state
- OpenVoice V1/V2 repo present with docs.
- Claims: zero-shot cross-lingual cloning, style control, rhythm/pauses/intonation controls.
- Local checkpoints directories exist but appear empty of ready model files (`checkpoints`, `checkpoints_v2`).

### Practical assessment
- Conceptually attractive for your control/timing requirements.
- Locally not in trained/ready state.
- Worth re-evaluation as a **comparison baseline**, but not as immediate continuation from old experiments.

---

## 3.7 `zonos/Zonos`

### Evidence and current state
- Upstream-style repo present with modern feature set:
  - zero-shot cloning,
  - multilingual support,
  - explicit speaking-rate and emotion control.
- `whisperdub/docs/Zonos Parameters.md` contains practical parameter notes (including speaking_rate).

### Practical assessment
- Strong candidate for your specific pain point about pacing/sync control.
- Appears more inference/control-oriented than classic “train-on-large-private-dataset” workflow.
- Good for fast quality benchmark and sync behavior tests.

---

## 3.8 `whisperdub`

### Evidence and current state
- Contains project docs for automated video translation/dubbing pipeline.
- Technical specification includes explicit sync algorithm and optional dynamic speaking-rate control.
- This directly matches your end goal (lecture dubbing with acceptable seconds-level drift).

### Practical assessment
- This is not only a model repo; it is your likely orchestration/pipeline layer.
- Valuable as the integration target regardless of the chosen TTS model.

---

## 4) Mapping findings to your historical pain points

## Pain point A: Russian source voice -> English output
- XTTS v2 path explicitly supports multilingual including Russian + English.
- GPT-SoVITS upstream supports cross-lingual scenarios; newer versions improved multilingual segmentation.
- OpenVoice and Zonos both claim cross-lingual support, but local readiness differs.

## Pain point B: GPU memory limits (previously)
- Earlier constraints likely blocked heavier configs.
- With 24 GB VRAM now:
  - XTTS fine-tuning should be substantially easier.
  - GPT-SoVITS v3 with checkpointing/LoRA becomes realistic.
  - Tortoise remains possible but still expensive in time and maintenance.

## Pain point C: hard setup / poor results in some repos
- Confirmed by fragmented state in several old directories.
- Best preserved successful traces are in XTTS/AllTalk-related runs.

## Pain point D: no pacing/pauses control for video sync
- GPT-SoVITS changelog includes speech-rate support.
- Zonos explicitly exposes speaking_rate and rich generation controls.
- `whisperdub` architecture already anticipates timing correction and dynamic pacing.

---

## 5) Current readiness ranking (based on *local* state)

1. **XTTS path (`xtts-finetune-webui` + `vits/alltalk_tts`)**
   - Most concrete prior successful training evidence and reusable artifacts.
2. **GPT-SoVITS (especially v2/v3 direction)**
   - Strong upstream evolution; local artifacts mostly incomplete except one older SoVITS checkpoint.
3. **Zonos**
   - Potentially best control surface for pace/style; needs practical validation in your pipeline.
4. **OpenVoice**
   - Good theoretical fit; local environment/checkpoints not yet in ready state.
5. **Tortoise**
   - Historical effort evident, but low operational efficiency and weak current output signals.

---

## 6) Key risks before restarting full training

1. **Dataset quality and segmentation risk**
   - Long lecture recordings require strict segmentation and transcript quality control.
2. **Cross-lingual identity drift**
   - Voice similarity can degrade when training mostly on Russian and synthesizing long English passages.
3. **Tempo mismatch in dubbing**
   - Must evaluate not just MOS/similarity but “seconds drift per minute” and pause controllability.
4. **Experiment reproducibility**
   - Previous work spread across multiple repos and backups; easy to lose comparability without unified tracking.

---

## 7) Recommended immediate direction for discussion (not execution yet)

Given current evidence, the most rational baseline discussion path is:

1. **Primary track**: XTTS fine-tune (because you already have successful local artifacts and workflow familiarity).
2. **Parallel benchmark track**: Zonos and/or GPT-SoVITS v3 for pacing control and English output naturalness.
3. **Integration target**: your dubbing/sync pipeline (`whisperdub` logic) with objective timing metrics.

This keeps risk low while leveraging your past progress.

---

## 8) High-confidence facts (quick reference)

- XTTS fine-tune ready artifacts exist in `xtts-finetune-webui/finetune_models/ready`.
- Historical XTTS/AllTalk runs with large checkpoints and decreasing eval loss exist.
- GPT-SoVITS repos are present; many target weight folders are empty in current snapshots.
- Tortoise has extensive archived runs but no obvious final `.pth` in active run path scanned.
- OpenVoice and Zonos are present as modern alternatives; local readiness differs.
- WhisperDub docs already formalize sync strategy and optional speaking-rate correction.

---

## 9) Sources (key files reviewed)

- `/ai/xtts-finetune-webui/README.md`
- `/ai/xtts-finetune-webui/finetune_models/ready/config.json`
- `/ai/vits/docs/Roadmap_xtts-finetune-webui.md`
- `/ai/vits/alltalk_tts/README.md`
- `/ai/vits/alltalk_tts/finetune/tmp-trn/training/XTTS_FT-April-08-2025_10+40PM-958213d/trainer_0_log.txt`
- `/ai/vits (GPT-SoVITS) 2/GPT-SoVITS/README.md`
- `/ai/vits (GPT-SoVITS) 2/GPT-SoVITS/docs/en/Changelog_EN.md`
- `/ai/vits (GPT-SoVITS) 1/docs/Roadmap.md`
- `/ai/tort (Tortoise TTS)/tune_tortoise_autoregressor/README.md`
- `/ai/tort (Tortoise TTS)/tune_tortoise_autoregressor/fine_tuning/training/russian_voice/finetune/train_russian_voice_250322-231616.log`
- `/ai/ov/OpenVoice/README.md`
- `/ai/ov/OpenVoice/docs/USAGE.md`
- `/ai/zonos/Zonos/README.md`
- `/ai/whisperdub/docs/Zonos Parameters.md`
- `/ai/whisperdub/docs/Постановка задачи.md`

---

## 10) Conclusion

Your previous work was not wasted: there is clear evidence of meaningful progress, especially on the XTTS path. 

For your current objective (Russian source voice, English output, high similarity, practical sync for lectures), the strongest restart strategy is to treat XTTS as the continuity baseline and benchmark it against a modern controllable alternative (Zonos and/or GPT-SoVITS v3) inside the existing dubbing pipeline framework.

---

## 11) Local workspace addendum (what exists *here* vs what exists on the server)

This audit file describes projects found on the server under `/ai`. In the current local workspace (this repository/folder), there is additional useful context that helps an independent developer quickly understand what is already implemented as working code and what is still missing as an end-to-end dubbing system.

### 11.1 A partial but concrete pipeline implementation exists locally

Under `galperina/translation_project/Project/scripts` and `galperina/translation_project/Web interface/scripts` there is a working “front half” of a pipeline (up to text translation) that matches the architecture described in the Russian technical specification.

Key entry points:

- `galperina/translation_project/Project/scripts/00_main.py`
  - Runs a sequence of scripts with `subprocess`.
  - Current script list is focused on:
    - `01_audio_detach.py`
    - `02_transcribe.py`
    - `03_reblock.py`
    - `04_verbalize_stage1.py` (and other staged variants)
    - translation is present but commented out in this variant.

- `galperina/translation_project/Web interface/scripts/00_main.py`
  - Similar runner, but parameterized via `--input_dir` / `--output_dir`.
  - Script list includes:
    - `01_audio_detach.py`
    - `02_transcribe.py`
    - `03_reblock.py`
    - `04_verbalize.py`
    - `05_translate.py`

Scripts that appear production-useful:

- `01_audio_detach.py`
  - Uses `ffmpeg` to extract mono audio and resample to 24kHz.

- `02_transcribe.py`
  - Uses `faster_whisper` with `large-v3`, CUDA/FP16, VAD enabled, and `word_timestamps=True`.
  - Saves:
    - SRT (e.g. with a `_ru_vi` suffix),
    - raw TXT,
    - a JSON “checkpoint” containing segments, timecodes, and confidence-like signals.

- `03_reblock.py`
  - Implements “reblocking” to larger segments (e.g. ~21 seconds per block) by estimating words-per-second from the original subtitles.
  - This is relevant for dubbing because longer blocks often reduce prosody artifacts and reduce “choppiness”, but they also increase the risk of timing drift if TTS output duration is not controlled.

### 11.2 Verbalization stage is present, but one variant looks incomplete

The presence of multiple `04_verbalize_*` scripts suggests real iteration on the “math lecture” text normalization problem.

- `galperina/translation_project/Web interface/scripts/04_verbalize.py` includes a placeholder `messages = [...]` and therefore does not look runnable as-is.
- Other staged variants exist under `galperina/translation_project/Project/scripts/` and backups; those are better candidates for restoring a working verbalization module.

Practical implication: for a clean restart, treat verbalization as its own module with explicit unit tests on representative math fragments (numbers, variables, “икс/аш/С-один” style tokens, etc.).

### 11.3 Translation module: good batching, but portability risk

`galperina/translation_project/Project/scripts/05_translate.py` implements:

- batching (`blocks_per_request`),
- a separator contract to preserve block boundaries,
- careful terminology constraints for technical content.

However, it currently loads secrets from an absolute `.env` location. This is a portability risk (and should be replaced with environment-first configuration + an optional override, not a hardcoded path).

### 11.4 The “back half” (TTS + sync + assembly) is not present locally as runnable scripts

In this local workspace, the following modules described in the technical spec were not found as implemented scripts:

- `04_voice_synthes.py` (voice synthesis / voice cloning)
- `05_sync.py` (timing correction / drift control)
- `06_audio_join.py` (segment assembly into a full dub track)
- `07_video_mux.py` (final muxing of video + new audio + subtitles)

There is also a standalone alignment tool:

- `galperina/translation_project/Models/GigaAM/Обучение/aeneas_sync.py`
  - Uses `aeneas` forced alignment, but it is GUI-driven (Tkinter directory picker) and is not structured as part of a headless server pipeline.

Practical implication: the fastest path to an end-to-end system is to implement these 4 missing modules as a minimal “reference implementation” first (even with a placeholder TTS), and only then iterate on model choice.

---

## 12) A practical restart strategy (so work does not stall again)

This section is intentionally execution-oriented and focuses on avoiding previous failure modes.

### 12.1 Treat the dubbing pipeline as the product; treat TTS models as swappable engines

Given the historical pain points (naturalness, pace/pauses control, drift on long lectures), the project should be structured so that:

- TTS is an adapter with a stable interface (input text + target language + speaker reference/model → output wav + metadata).
- Sync is deterministic and measurable (segment durations, pauses, drift budget).

This reduces the risk of “endless model switching” without ever shipping a working pipeline.

### 12.2 Define objective metrics early (independent developer checklist)

For each 10–15 minute lecture sample, track:

- **Drift**: accumulated time difference (in seconds) between original segment boundaries and synthesized placement over time.
- **Slot fit ratio**: `tts_duration / original_slot_duration` per segment.
- **ASR self-check**: re-transcribe synthesized audio and compare to intended translated text (rough WER/Levenshtein threshold).
- **Listening MOS**: small blind set (10–20 segments) rated by naturalness and speaker similarity.

### 12.3 Two-track model evaluation that matches your priorities

- **Track A (continuity baseline)**: use the already-proven XTTS fine-tune path from the server as a baseline reference point (even if it is not the final choice). This anchors regression testing.

- **Track B (control/naturalness benchmark)**: benchmark at least one model whose main value is explicit controllability (e.g., speaking rate / style / emotion) and compare it inside the same pipeline with the same metrics.

The key rule: do not commit to full fine-tuning until the pipeline can measure and correct timing drift.
