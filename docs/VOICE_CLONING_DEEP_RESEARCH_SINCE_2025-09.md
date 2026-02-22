# Deep Research: Voice Cloning / TTS (Sep 2025 → Feb 2026)

## 0) Scope

This document focuses only on **Sub-task #1**:
- Train/adapt a model to a **single target speaker** (Russian original voice dataset)
- Generate **English** speech with **maximum speaker similarity** (priority ~60%)
- English pronunciation quality is secondary (~40%)

Out of scope:
- video/audio synchronization
- pipeline orchestration

Constraints:
- must be **free to use** locally (open-source or free non-commercial/self-hosted license)
- compute: **single local NVIDIA GPU with 24GB VRAM**
- time horizon: **projects released or significantly updated since Sep 2025**

---

## 1) Evaluation lens (what matters for this use case)

### 1.1 Speaker similarity / cloning fidelity
- Whether the model can *actually lock onto* a single speaker identity.
- Whether it stays stable on **long-form** and across different text domains.

### 1.2 Cross-lingual constraints (RU voice → EN text)
You need at least one of the following to be true:
- the model natively supports **Russian language tokens/normalization** for training on RU transcripts, OR
- it can be fine-tuned with RU audio **without** requiring RU transcript modeling quality (rare), OR
- you can train in a way that avoids RU transcripts entirely (rare; typically degrades similarity).

### 1.3 Fine-tuning support (preferred)
Because you historically observed that pure zero-shot/few-shot voice cloning is not sufficient, priority is given to:
- full fine-tuning (SFT)
- LoRA / parameter-efficient fine-tuning

---

## 2) Candidate landscape (Sep 2025 → Feb 2026)

### 2.1 Qwen3-TTS (Jan 2026)
- **Repo**: https://github.com/QwenLM/Qwen3-TTS
- **License**: Apache-2.0
- **Languages**: explicitly includes Russian among 10 major languages.
- **What’s new**: instruction-driven control (incl. speaking rate / prosody) + explicit fine-tuning docs.
- **Fine-tuning**: supported; currently **single-speaker fine-tuning**.
  - Data format: JSONL with `audio`, `text`, `ref_audio`.
  - Requires extracting `audio_codes` with the Qwen tokenizer.
  - Finetune script: `sft_12hz.py` (SFT).
- **Fit for your use case**:
  - Strong match: modern, multilingual incl. RU, explicit single-speaker fine-tuning.
  - Potential risk: fine-tuning workflow is non-trivial (tokenization step), but still explicit.

### 2.2 Fish Speech / FishAudio-S1 (active 2025–2026)
- **Repo**: https://github.com/fishaudio/fish-speech
- **License**: Apache-2.0
- **Voice cloning**: supports rapid voice cloning from 10–30s reference.
- **Fine-tuning**: LoRA fine-tune exists in official docs.
- **Important nuance** (per docs): by default, fine-tuning mainly learns **speech patterns**, not timbre; timbre stability still relies on prompts unless you increase steps (risk of overfit).
- **Fit for your use case**:
  - Good for quality + expressiveness; RU is listed among languages supporting emotion markers.
  - May not be the easiest path to “speaker identity lock” via fine-tuning alone (needs careful prompt protocol).

### 2.3 CosyVoice 3.0 / 2.0 (late 2025)
- **Repo**: https://github.com/FunAudioLLM/CosyVoice
- **License**: Apache-2.0
- **Languages**: includes Russian and English.
- **Claimed strengths**: speaker similarity + prosody naturalness + instruct support (speed/emotion etc.).
- **Fine-tuning**: repository positions itself as full-stack (inference/training/deployment); multiple released model variants exist.
- **Fit for your use case**:
  - Likely strong candidate for speaker similarity + controllability.
  - Practical risk: training stack may be heavier than minimal fine-tune workflows; needs hands-on validation.

### 2.4 Higgs Audio v2.5 (Jan 2026 update)
- **Repo**: https://github.com/boson-ai/higgs-audio
- **License**: Apache-2.0
- **What’s new**: v2.5 reportedly condenses to 1B while improving stability and cloning + style control.
- **Voice cloning**: supports zero-shot voice cloning; provides example scripts.
- **Fine-tuning**: not clearly presented as “bring your own dataset and fine-tune to a single speaker” (in the chunks reviewed); this may be more of a foundation model with prompting.
- **Fit for your use case**:
  - Strong as a *benchmark* for modern zero-shot voice cloning.
  - Unclear if it solves your preference for fine-tuning-to-identity; likely needs validation.

### 2.5 VoxCPM 1.5 (Dec 2025)
- **Repo**: https://github.com/OpenBMB/VoxCPM
- **License**: Apache-2.0
- **Fine-tuning**: supports full SFT and LoRA.
- **Data requirement**: transcripts required; specific sample rate requirement for v1.5.
- **Critical language issue**:
  - The README explicitly states it is trained primarily on **Chinese and English** and performance on other languages is not guaranteed.
  - For your case (RU training transcripts), this is a major risk.
- **Fit for your use case**:
  - Great fine-tuning ergonomics (LoRA FAQ mentions convergence from 5–10 minutes).
  - However, likely a weak fit because your training data and ref transcripts are Russian.

### 2.6 Chatterbox (Resemble AI) (2025–2026)
- **Repo**: https://github.com/resemble-ai/chatterbox
- **License**: MIT
- **Multilingual**: 23 languages including Russian.
- **Voice cloning**: reference-audio conditioning.
- **Fine-tuning**: not highlighted in reviewed chunks; appears primarily as strong inference + cloning.
- **Fit for your use case**:
  - Very strong baseline for “modern zero-shot cloning quality”.
  - If no real fine-tuning path exists, it may not match your preference—but it can still be an important comparator.

### 2.7 KaniTTS-2 (Feb 2026)
- **Repo**: https://github.com/nineninesix-ai/kani-tts-2
- **License**: declared as Apache-2.0 in `pyproject.toml` (note: classifiers list includes MIT, which is inconsistent; treat as “needs manual confirmation” until a dedicated license file exists).
- **Core idea**: speaker embeddings ("no fine-tuning for each speaker"; clone from reference audio).
- **Fine-tuning**: not presented as a stable “single-speaker LoRA/SFT recipe” in the repo chunks reviewed; pretraining framework exists but is described as under active development.
- **Fit for your use case**:
  - Useful as a modern comparator for “speaker-embedding-based cloning”.
  - However, it does not clearly match your stated preference for robust fine-tuning-to-identity on your own dataset.

### 2.8 IndexTTS2 (released Sep 2025)
- **Repo**: https://github.com/index-tts/index-tts
- **License**: **Bilibili Model Use License Agreement** (custom, not OSI standard).
  - It explicitly defines derivative works and usage.
  - It appears free/royalty-free for typical individual/small usage, but is not a “standard open-source” license.
- **Notable capability**: duration control is a core claim (but “not enabled in this release”).
- **Fit for your use case**:
  - Potentially relevant due to controllability claims.
  - But licensing + “duration control not enabled yet” makes it a less predictable path.

### 2.9 OuteTTS (2025)
- **Repo**: https://github.com/edwko/OuteTTS
- **License**: Apache-2.0
- **Interface project**: provides a framework for speaker profiles and generation; relies on specific models/backends.
- **Fit for your use case**:
  - Worth noting as tooling; unclear if it is the best route for high-fidelity single-speaker fine-tune.

### 2.10 Step-Audio2 (reference: 2025–2026; open models)
- **Repo**: https://github.com/stepfun-ai/Step-Audio2
- **License**: Apache-2.0 (code).
- **Nature**: end-to-end multimodal speech conversation model (ASR/audio understanding + speech conversation). It is not primarily positioned as a “voice cloning fine-tune your speaker” TTS product.
- **Fit for your use case**:
  - Interesting, but likely off-focus for “single-speaker voice identity fine-tune for EN reading”.

### 2.11 VibeVoice (status note; 2025–2026)
- **Repo**: https://github.com/microsoft/VibeVoice
- **License**: MIT (repo).
- **Important status**: official repo notes that **VibeVoice-TTS code was removed** (2025-09-05 note). What remains strongly available is ASR and realtime components.
- **Fit for your use case**:
  - Not a primary candidate for Sub-task #1 in its current official state.

---

## 3) Shortlist (5–8) for your exact goal

### Tier-1 (most aligned with “fine-tune to a single RU speaker, then read EN text”)
1. **Qwen3-TTS (CustomVoice fine-tuning)**
   - Best alignment: multilingual incl. RU + explicit single-speaker fine-tuning workflow.
2. **CosyVoice 3.0 / 2.0**
   - Likely strong at speaker similarity + prosody; multilingual incl. RU; needs validation of the fine-tune workflow for a single speaker.
3. **FishAudio-S1 (LoRA fine-tuning)**
   - Strong quality and ecosystem; but you must confirm whether LoRA training can truly lock timbre, not just patterns.

### Tier-2 (important comparators / possibly sufficient with modern zero-shot)
4. **Chatterbox-Multilingual**
   - Very strong comparator for current-gen cloning quality (fast to test).
5. **Higgs Audio v2.5**
   - Benchmark for SOTA foundation-model voice cloning; unclear fine-tuning story.

### Tier-2.5 (comparator; promising, but fine-tune story unclear)
6. **KaniTTS-2**
   - Modern speaker-embedding cloning approach; but not clearly a “fine-tune to a single speaker” solution.

### Tier-3 (situational)
7. **IndexTTS2**
   - Potential controllability, but licensing and “not enabled yet” claims reduce predictability.
8. **VoxCPM 1.5**
   - Only if you confirm you can fine-tune without RU transcript issues (otherwise high risk).
9. **OuteTTS**
   - More of an interface/tooling option than a core “best model” choice.

---

## 4) Recommended 2–3 candidates for the first bake-off (and why)

If the goal is to pick 1 main direction quickly, I would start with:

1. **Qwen3-TTS (fine-tune)**
   - Because it is the most explicit “single-speaker fine-tuning” path among the new releases and includes RU.

2. **CosyVoice 3.0 / 2.0 (voice cloning / adaptation)**
   - Because it is explicitly multilingual incl. RU and emphasizes speaker similarity + prosody.

3. **Chatterbox-Multilingual (zero-shot baseline)**
   - Not because you expect zero-shot to win, but because it is a fast, modern baseline.
   - If it is already close in similarity, it saves you weeks of fine-tuning.

Alternative #3 (if you want a “new wave” comparator instead of Chatterbox):
- **Higgs Audio v2.5** or **KaniTTS-2** as the modern foundation-model/speaker-embedding baseline.

---

## 5) What I still need to confirm (quick items)

To finalize a very confident recommendation, I would next confirm:
- whether CosyVoice offers a clean “single-speaker adaptation” recipe comparable to Qwen’s CustomVoice,
- the practical RU→EN behavior on FishAudio-S1 LoRA (does it lock timbre),
- KaniTTS-2 license status (repo declares Apache-2.0, but classifiers mention MIT; confirm via an explicit license file or upstream statement),
- the real practicality of IndexTTS2 for your case given its custom license.
