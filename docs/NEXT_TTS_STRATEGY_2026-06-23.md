# Next TTS Strategy After Qwen3TTS Tests (2026-06-23)

## Current conclusion

Qwen3TTS is currently the best local result for speaker cloning in this project, especially after the Baritone fine-tune runs. The weak point is long-form speech generation: connected book-style reading still sounds too unstable and monotonous for audiobooks or long dubbing.

Update after the 2026-06-23 built-in voice test: Qwen3TTS built-in native-English
speakers Aiden and Ryan read English long-form text much better than the
Russian-trained Baritone voice. The best current Qwen3TTS result is the
`02_quality_longer_chunks` generation style with Aiden/Ryan. The next Qwen3TTS
experiment should therefore use a native-English target speaker with a desired
timbre, not another blind run on the Russian Baritone source.

The next stage should not be another blind Qwen3TTS run. It should be a controlled bake-off focused on:

- long-form reading stability;
- voice similarity;
- pause and pace control;
- emotion and breath/control tags;
- hallucinations, repetitions, and off-prompt speech;
- drift per minute for dubbing;
- Russian and English behavior separately.

## Local project audit

Relevant local projects found under `/ai`:

| Local path | Local state | Upstream freshness | Current assessment |
| --- | --- | --- | --- |
| `/ai/Qwen3TTS` | Active local project; Baritone input and multiple recent run metrics/samples exist. | Local fork active in June 2026. | Best voice-clone result so far, but long-form generation is the pain point. Keep as baseline and possible voice-identity source. |
| `/ai/vits (GPT-SoVITS) 1/GPT-SoVITS` | Has trained/preprocessed local artifacts from 2025-03-24, including SoVITS weights. | Local checkout is March 2025-era. | Old local experiment has useful artifacts, but not the clean restart target. |
| `/ai/vits (GPT-SoVITS) 2/GPT-SoVITS` | Mostly pretrained model setup; fewer local trained artifacts. | Upstream now has newer tags including `20250422v4` and `20250606v2pro`; local checkout is older. | Strongest "old project to revisit"; update or clone fresh before testing. |
| `/ai/vits/alltalk_tts` | Has XTTS trained model artifacts around 2025-04-09. | XTTS/AllTalk track is older. | Useful historical baseline, but likely not the new primary path. |
| `/ai/xtts-finetune-webui` | Has ready XTTS artifacts and dataset wavs from April 2025. | Local fork has later remote changes, but XTTS itself is old compared with 2026 models. | Keep as baseline, not first choice for new R&D. |
| `/ai/ov/OpenVoice` | Has v1/v2 checkpoints locally. | Upstream main is newer than local. | Good control concept, but model generation quality likely behind newer 2026 systems. Consider as voice-conversion/control baseline. |
| `/ai/zonos/Zonos` | Local checkout matches upstream main from March 2025. | No meaningful upstream movement detected by remote HEAD. | Useful for speaking-rate/emotion control experiments, but not an obvious long-form winner now. |
| `/ai/tort (Tortoise TTS)` | Base models and tuning repos exist. | Upstream exists but old. | Low ROI for current goal: slow, heavy, less likely to beat modern models. |
| `/ai/whisperdub` | Pipeline scripts/docs exist, including timing/sync and Zonos params. | Local pipeline layer, not a model. | Likely integration layer for final dubbing/book pipeline, regardless of TTS choice. |

## Fresh external candidates

### MisoTTS

MisoTTS is worth testing for English expressiveness, but it is not a direct replacement for Qwen3TTS voice fine-tuning.

Observed from upstream docs:

- model is `Miso TTS 8B`;
- English only;
- high-VRAM local inference, roughly 24 GB recommended for bf16/fp16;
- can condition on prior prompt audio for voice cloning;
- no clear "train on my large speaker dataset" recipe in the public repo.

Verdict: test as an English emotional/conversational baseline, not as the main trained-voice-clone path.

### GPT-SoVITS current upstream

This is the most obvious already-tested project to revisit. Upstream moved beyond the local March 2025 checkout and now exposes newer release tags, including v4/v2pro-era work. It explicitly targets few-shot TTS and claims fine-tuning from about one minute of data, with cross-lingual support.

Verdict: clone/update cleanly and run a fresh GPT-SoVITS v4/v2pro bake-off.

### CosyVoice 3.0

Very high-priority candidate. It supports Russian and English, cross-lingual zero-shot voice cloning, instructions for language/emotion/speed/volume, and claims stronger content consistency, speaker similarity, and prosody naturalness than CosyVoice2.

Verdict: top-tier test for both Russian and English.

### Fish Audio S2 Pro

Very high-priority for controllability. It supports 80+ languages, includes Russian, supports short-reference voice cloning, and exposes very rich inline tags for pauses, emotion, breath, whisper, emphasis, etc.

Risk: license is research-focused, and the model is large. It may be better as an evaluation target than a production default until licensing is checked.

Verdict: top-tier expressive/control benchmark.

### Chatterbox Multilingual V3

Strong fast comparator. It supports 23+ languages including Russian, is relatively small, and explicitly targets improved speaker similarity, fewer hallucinations, and more natural multilingual speech. It is prompt-reference cloning, not large-dataset speaker training.

Verdict: fast zero-shot baseline; run early because setup cost should be low.

### Higgs Audio v3

Strong modern candidate for conversational TTS, 100+ languages, zero-shot voice cloning, and inline emotion/style/prosody control. The open weights are under a non-commercial research license.

Verdict: good benchmark if license/use case is acceptable.

### IndexTTS2

Very relevant conceptually because it targets emotion and duration control, which matter for dubbing and audiobooks. Licensing and multilingual/Russian fit need careful verification before treating it as a production candidate.

Verdict: high-interest control benchmark, but not first unless licensing and language fit look clean.

### PFluxTTS / X-Voice

Both are especially relevant research signals:

- PFluxTTS targets robust cross-lingual cloning and claims strong results against F5-TTS, FishSpeech, SparkTTS, Chatterbox, and ElevenLabs.
- X-Voice targets 30-language zero-shot cross-lingual cloning and is built from F5-TTS ideas with IPA language representation.

Verdict: watch and test if runnable code/weights are available. These may become better fits than Qwen-style fine-tuning if short-reference cloning has improved enough.

## Recommended bake-off order

1. **Chatterbox Multilingual V3**
   - Fastest modern zero-shot sanity check.
   - Tests whether 2026 short-reference cloning is now good enough.

2. **CosyVoice 3.0**
   - Best balance of RU/EN support, voice cloning, prosody naturalness, and instruction control.

3. **Fish Audio S2 Pro**
   - Best candidate for inline expressive control: pauses, breaths, emotions, emphasis.

4. **GPT-SoVITS fresh v4/v2pro**
   - Best continuation of an old local project with newer upstream progress.
   - Worth testing because it supports few-shot/fine-tune style workflows.

5. **MisoTTS**
   - English-only expressive/conversational benchmark.
   - Useful for English secretary/dialogue style, less useful for Russian or dataset-trained cloning.

6. **Higgs Audio v3 / IndexTTS2**
   - Run if the first four do not satisfy long-form quality/control.

## Test protocol

Each model should produce the same fixed sample set:

1. English audiobook paragraph, 90-150 seconds target.
2. English dialogue/secretary sample with interruptions, short pauses, breath/emotion tags.
3. Russian audiobook paragraph, 90-150 seconds target.
4. Russian lecture/dubbing block with target duration.
5. Cross-lingual test: Russian source voice reference -> English text.

For every output, capture:

- model and commit/tag;
- reference audio used;
- text and control tags;
- generation parameters;
- raw output duration;
- ASR text match / WER;
- speaker similarity score if available;
- subjective notes: naturalness, reading continuity, emotion, pauses, fatigue;
- drift against target duration.

## Can Qwen3TTS cloned voices be transferred?

Direct transfer is almost certainly not possible. The "voice" learned by Qwen3TTS is not a portable universal speaker file; it is encoded inside Qwen3TTS-specific weights, tokenizer/audio-code space, and conditioning format. GPT-SoVITS, XTTS, CosyVoice, Fish, Miso, and Chatterbox all represent speaker identity differently.

What can be reused:

- the original clean dataset;
- the same reference clips;
- Qwen3TTS-generated best samples as additional prompt/reference audio for zero-shot models;
- Qwen3TTS-generated samples as synthetic training material, but only carefully, because artifacts can contaminate the new model;
- a separate voice-conversion route: generate natural speech with another model, then convert timbre with RVC/OpenVoice/So-VITS-style conversion trained on the original voice.

Most promising hybrid strategy:

1. Use the best long-form reader for text/prosody.
2. Preserve target identity with either strong reference cloning or a voice-conversion layer.
3. Use Qwen3TTS as a benchmark and maybe as a source of very clean voice prompts, not as a transferable voice model.

## Working recommendation

Do not abandon Qwen3TTS yet, but stop treating it as the only candidate. Keep it as the speaker-identity baseline and start a structured bake-off:

1. Chatterbox Multilingual V3;
2. CosyVoice 3.0;
3. Fish Audio S2 Pro;
4. fresh GPT-SoVITS v4/v2pro;
5. MisoTTS for English-only expressiveness.

If none of those can preserve the Qwen-level cloned identity while reading naturally, the next serious architecture should be a two-stage pipeline: high-quality expressive TTS first, then voice conversion into the target speaker.

## Additional Candidates Checked After Initial Report

### Audiblez / Kokoro-82M

Audiblez is not a voice-cloning model. It is an audiobook production wrapper: EPUB in, chapter WAV files and final `.m4b` out. It uses Kokoro-82M as the TTS backend.

Strengths:

- very practical audiobook tooling;
- MIT wrapper around Kokoro-based audiobook generation;
- fast and lightweight compared with large TTS models;
- supports speed control and CUDA mode;
- good candidate for testing book-production ergonomics.

Weaknesses for this project:

- no target-speaker training path;
- no Qwen-level voice cloning;
- no Russian voice listed in the current Audiblez README voice table;
- limited expressive/control surface compared with Fish/VoxCPM/CosyVoice.

Verdict: test only as an audiobook pipeline and Kokoro quality baseline. It is unlikely to solve the custom voice-cloning problem.

### MisoTTS

MisoTTS remains interesting for English expressive/conversational speech, but its current public repo is narrow for our needs.

Strengths:

- 8B expressive model;
- local inference is documented;
- audio-context conditioning can be used for prompted voice cloning;
- likely worth testing on English dialogue/secretary style.

Weaknesses:

- English only;
- no public large-dataset speaker fine-tuning recipe found;
- roughly 30-40 GB first-run download and 24 GB GPU class recommended;
- max sequence length and example generation style suggest it should be tested on short/medium chunks first, not full audiobook chapters.

Verdict: English-only benchmark, not primary RU/EN audiobook or dubbing engine.

### Violin

Violin is not a local open-source TTS model. It is an open-source video translation/dubbing pipeline.

Strengths:

- practical pipeline: ffmpeg audio extraction, Whisper Large v3 word timestamps, LLM translation, TTS, speed-aligned remux, SRT;
- CLI, FastAPI app, and Claude Code skill;
- style profiles and pluggable providers;
- useful reference for the orchestration layer of a dubbing system.

Weaknesses:

- default stack depends on hosted providers: Together, Cartesia Sonic 3, ElevenLabs/OpenAI options;
- voice cloning and lip sync are still listed as todo items;
- not self-hosted by default;
- does not solve custom voice identity by itself.

Verdict: study or borrow as a dubbing pipeline pattern. For this project it would need a local TTS backend adapter, for example Qwen3TTS, VoxCPM2, Fish, CosyVoice, GPT-SoVITS, or a TTS-plus-voice-conversion chain.

### VoxCPM2

Very strong new China-origin candidate not yet tested locally.

Strengths:

- 2B model, 30 languages including Russian and English;
- Apache-2.0 and claims commercial-ready weights/code;
- voice design from text description;
- controllable voice cloning from short reference audio;
- "ultimate cloning" path with prompt audio plus transcript;
- 48kHz output;
- context-aware prosody and streaming;
- LoRA/SFT existed in VoxCPM1.5 track, and VoxCPM2 is the current recommended release.

Risks:

- needs real testing for Russian audiobook reading and RU->EN cross-lingual identity;
- short-reference cloning may still fall short of our Qwen3TTS trained clone;
- setup/performance needs verification on the actual server GPU.

Verdict: promote into the first bake-off tier. Suggested order is now Chatterbox V3, VoxCPM2, CosyVoice3, Fish S2 Pro, GPT-SoVITS v4/v2pro.

### Spark-TTS

China-origin 0.5B model with zero-shot voice cloning and controllable gender/pitch/speaking-rate generation.

Strengths:

- Apache-2.0;
- relatively small;
- supports Chinese and English;
- zero-shot voice cloning and voice creation;
- efficient runtime and Triton/TensorRT-LLM serving notes.

Weaknesses:

- no Russian support in the README features checked;
- training code/dataset were still listed as todo;
- likely less relevant than VoxCPM2/CosyVoice/Fish for Russian and cross-lingual audiobook work.

Verdict: test later for English/Chinese only, or if we need a small efficient baseline.

### FireRedTTS-2

China-origin long-form streaming TTS for multi-speaker dialogue generation.

Strengths:

- Apache-2.0;
- explicitly targets long conversational speech;
- claims 3-minute dialogues with 4 speakers;
- supports Russian, English, Chinese, Japanese, Korean, French, German;
- supports zero-shot voice cloning for cross-lingual/code-switching.

Weaknesses:

- first public release looks smaller/younger than VoxCPM2/Fish/CosyVoice ecosystems;
- needs hands-on test to see whether "dialogue long-form" translates into audiobook narration quality.

Verdict: high-interest candidate for dialogue/podcast/dubbing, especially because long-form stability is our pain point.

### VibeVoice

Microsoft open-source long-form voice model family.

Strengths:

- specifically targets long-form multi-speaker TTS;
- claims up to 90 minutes in one pass with up to 4 speakers;
- promising for podcast/dialogue continuity and speaker consistency;
- also has ASR work that may be useful for long video handling.

Weaknesses:

- language fit for Russian is unclear from the repo overview;
- not primarily framed as "clone my trained speaker from a large dataset";
- may be better for podcast/dialogue generation than single-speaker custom audiobook voice.

Verdict: important long-form benchmark, especially for English/Mandarin dialogue, but not first for Russian custom voice.

### GLM-4-Voice

China-origin end-to-end speech dialogue model.

Strengths:

- understands and generates Chinese/English speech;
- supports following instructions for emotion, intonation, speed, dialect and other speech attributes;
- useful as a speech-agent/conversation research direction.

Weaknesses:

- not a primary TTS audiobook engine;
- no clear custom voice-cloning/fine-tuning path found in the checked README section;
- no Russian fit.

Verdict: not priority for this project unless we later build real-time speech agents.

### PFluxTTS

High-interest Russia-linked research signal.

Strengths:

- explicitly targets robust cross-lingual voice cloning;
- claims strong performance against F5-TTS, FishSpeech, SparkTTS, Chatterbox and ElevenLabs;
- claims it needs only short reference audio and no extra training;
- particularly relevant because the authors appear to be Russian/Eastern European and the problem framing matches our RU/EN cross-lingual use case.

Weaknesses:

- from the sources checked, it is not yet confirmed as a readily runnable GitHub/Hugging Face package;
- should be watched and tested immediately if code/weights are available.

Verdict: watchlist with high upside. If runnable artifacts exist, it jumps into tier 1.

### VoiceSculptor

New instruction-controlled voice design and cloning system.

Strengths:

- targets fine-grained control over pitch, speaking rate, age, emotion, and style;
- combines natural-language voice design with cloning;
- claims open-source code and pretrained models.

Weaknesses:

- Chinese/control research focus may not map directly to RU/EN audiobook needs;
- needs repo/weights verification and a real sample test.

Verdict: good control research candidate, not first production candidate.

## Revised Shortlist

Tier 1 for immediate tests:

1. Chatterbox Multilingual V3: fastest sanity check for modern short-reference cloning.
2. VoxCPM2: strongest new all-around open candidate for Russian, English, voice design, controllable cloning.
3. CosyVoice 3.0: strong multilingual prosody and instruction support.
4. Fish Audio S2 Pro: strongest inline control tags and expressive speech.
5. FireRedTTS-2: long-form dialogue/podcast stability and Russian support.
6. GPT-SoVITS fresh v4/v2pro: best continuation of old local work.

Tier 2:

- MisoTTS: English-only expressive benchmark.
- VibeVoice: long-form English/Chinese dialogue benchmark.
- Audiblez/Kokoro: audiobook tooling and lightweight fixed-voice baseline.
- IndexTTS2 and Higgs Audio v3: strong but license/fit needs careful review.

Watchlist:

- PFluxTTS if code/weights become runnable.
- VoiceSculptor for voice design/control experiments.
