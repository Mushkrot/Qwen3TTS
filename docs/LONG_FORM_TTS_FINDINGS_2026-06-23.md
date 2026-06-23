# Long-Form TTS Findings (2026-06-23)

## Current conclusion

Qwen3TTS can learn a target voice timbre well enough for short phrases, words,
and short sentences. The current Baritone fine-tuned voice is not good enough
for long connected Russian audiobook narration, and it is only partially usable
for long English narration.

The main weakness is not only voice identity. It is long-form reading behavior:

- wrong Russian stress and `е`/`ё` interpretation;
- weak sentence-level context;
- weak question/exclamation/surprise intonation;
- too few natural pauses;
- rushed delivery unless text is segmented manually;
- timbre drift and clipped word endings when stitched segments are too short.

## Russian vs English

Russian long-form reading is not viable with the tested Qwen3TTS voice setup.
Short Russian phrases may still be usable, but connected chapter narration
sounds broken.

English is much better. Built-in native-English speakers read the same long
nonfiction paragraph with much stronger pronunciation, pacing, and continuity.
With careful segmentation, English may become acceptable for audiobook-style
work.

## Best tested generation style

The strongest tested style is the slow stitched / longer chunks approach:

- split text by semantic sentence groups rather than tiny fragments;
- use longer chunks to reduce timbre changes between generations;
- add explicit pauses after sentence groups;
- use gentle fades/crossfades;
- avoid aggressive trimming because it can clip word endings.

The best current listening candidates are the built-in Aiden/Ryan
`02_quality_longer_chunks` samples.

## Built-in voice result

The built-in Qwen3TTS CustomVoice speakers Aiden and Ryan read English better
than the trained Baritone voice because they are native model speakers. Their
speaker identities are already well aligned with the model's English phonetics,
prosody, and long-form rhythm.

The trained Baritone voice captured timbre, but it did not acquire the same
native-English reading behavior. The source voice and dataset were Russian, and
the fine-tune appears to associate that speaker with the Russian acoustic and
prosodic domain.

## Current local listening files

Useful generated listening files were moved out of the confusing experiment
tree and into the voice workspace:

```text
datasets/voices/Aiden/Ready/builtin_quality_2026-06-23/
datasets/voices/Ryan/Ready/builtin_quality_2026-06-23/
datasets/voices/Baritone/Ready/prosody_control_2026-06-23/
```

These directories are local ignored assets. They are not committed to Git.

## Cleanup decision

The old local `experiments/qwen3_ru_en_speaker_v1/` tree had grown into a
large, hard-to-navigate mix of checkpoints, logs, samples, and copied review
packs. On 2026-06-23, the ignored generated contents were removed after the
useful listening samples were copied to `datasets/voices/**/Ready/`.

The remaining `experiments/` tree is only a lightweight technical scaffold:

```text
experiments/qwen3_ru_en_speaker_v1/
  manifests/train_raw.template.jsonl
  notes/.gitkeep
  runs/.gitkeep
  samples/.gitkeep
```

Generated training checkpoints may still be written under `experiments/**/runs/`
by technical scripts, but they are disposable local artifacts unless explicitly
backed up outside Git.

## Next recommended experiment

The next Qwen3TTS experiment should use a new native-English speaker whose
timbre is already close to the desired voice. The source material should be
long-form or narration-like English, not only short phrases.

Suggested target-source requirements:

- native or near-native English;
- timbre close to the desired Baritone direction;
- stable microphone and room tone;
- minimal music/noise;
- enough connected speech to represent audiobook rhythm;
- source files placed under `datasets/voices/<NewVoice>/Input/`.

The success criterion is not only whether the new voice matches the desired
timbre. It must pass the same `02_quality_longer_chunks` English benchmark
without rushing, drift, or clipped endings.

## Alternative architecture

If a newly trained English voice still cannot combine good timbre with good
reading behavior, the most promising alternative is a two-stage pipeline:

1. generate natural long-form speech with a strong built-in/native reader;
2. convert the timbre toward the target speaker with a separate voice conversion
   model.

That route may preserve the stronger prosody of Aiden/Ryan while moving the
voice identity closer to the desired target.
