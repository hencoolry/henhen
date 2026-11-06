---
name: whisper
description: Transcribe speech to text and generate subtitles (SRT, VTT, word-level JSON) from any audio or video file with OpenAI Whisper, locally and offline. Use for captions, transcripts for editing (find the cut points), translation to English, or feeding a script to Remotion/HyperFrames caption components. Covers faster-whisper (recommended), openai-whisper, and whisper.cpp.
---

# Whisper: subtitles and transcripts

Whisper turns speech into timed text. In the editing pipeline it produces the subtitle file that `/ffmpeg` burns in or that the `/remotion-captions` and `/hyperframes` caption references consume, and a transcript you read to decide where to cut.

## Pick an implementation

| Implementation | When | Install |
|---|---|---|
| **faster-whisper** (default) | CPU or NVIDIA GPU, Python available. 4x faster than the reference, same accuracy, word timestamps built in. | `pip3 install -U faster-whisper` |
| openai-whisper | The reference. Simplest CLI. Pulls PyTorch (~2 GB). | `pip3 install -U openai-whisper` |
| whisper.cpp | No Python, Apple Silicon, embedded, or a Remotion project (`@remotion/install-whisper-cpp`). | `brew install whisper-cpp` or build from source |
| `@remotion/whisper-webgpu` | Already inside a Remotion project and a GPU is present. See `/remotion-captions`. | `npx remotion add @remotion/whisper-webgpu` |

If unsure, use faster-whisper. If the project is a Remotion project, read `/remotion-captions` first and use its route.

Models (all implementations): `tiny`, `base`, `small`, `medium`, `large-v3`, `large-v3-turbo`. Accuracy and cost both rise down the list. Defaults that work: `small` for a quick pass on CPU, `large-v3-turbo` for final captions (near large-v3 accuracy, much faster), `medium` when the turbo model is unavailable. Add `.en` (e.g. `small.en`) for English-only audio on the small models. Models download on first use to `~/.cache` (hundreds of MB to ~3 GB), so the machine needs network access to Hugging Face for faster-whisper or to openaipublic.azureedge.net for openai-whisper.

## Rules

1. **Give Whisper clean audio.** Extract 16 kHz mono WAV with ffmpeg first. It is faster and avoids container quirks.
2. **Always set `--language` when you know it.** Auto-detect costs time and mis-fires on short clips or music intros.
3. **Use word timestamps** when the subtitles will be styled per word (TikTok-style highlight captions) or when you need exact cut points.
4. **Proofread names and jargon.** Whisper guesses proper nouns. Pass `--initial_prompt "Remotion, HyperFrames, yt-dlp, FFmpeg"` with the terms expected in the audio so it spells them right.
5. **Keep caption lines short** for vertical video: 1 to 2 lines, up to ~32 characters per line, 1 to 3 seconds each. Resegment if the raw output is long sentences.
6. **Never report a transcript as verified without reading it.** Sample the start, middle and end against the audio timing.

## Step 1: prepare the audio

```bash
ffmpeg -y -i input.mp4 -vn -ar 16000 -ac 1 -c:a pcm_s16le audio.wav
```

For a URL, `/yt-dlp` can produce this directly.

## Step 2a: faster-whisper (recommended)

Save as `transcribe.py` and run with `python3 transcribe.py audio.wav --model large-v3-turbo --language en`.

```python
#!/usr/bin/env python3
"""Transcribe audio with faster-whisper; write .srt, .vtt, .txt and word-level .json next to the input."""
import argparse, json, sys
from pathlib import Path
from faster_whisper import WhisperModel

def ts(sec: float, sep: str = ",") -> str:
    ms = int(round(sec * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02}{sep}{ms:03}"

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--language", default=None, help="e.g. en; omit to auto-detect")
    ap.add_argument("--device", default="auto", help="auto|cpu|cuda")
    ap.add_argument("--compute-type", default="default", help="int8 for CPU, float16 for GPU")
    ap.add_argument("--initial-prompt", default=None, help="names/jargon to bias spelling")
    ap.add_argument("--translate", action="store_true", help="translate to English")
    args = ap.parse_args()

    model = WhisperModel(args.model, device=args.device, compute_type=args.compute_type)
    segments, info = model.transcribe(
        args.audio,
        language=args.language,
        task="translate" if args.translate else "transcribe",
        word_timestamps=True,
        vad_filter=True,
        initial_prompt=args.initial_prompt,
    )
    print(f"language={info.language} p={info.language_probability:.2f} duration={info.duration:.1f}s", file=sys.stderr)

    out = Path(args.audio).with_suffix("")
    srt, vtt, txt, words = [], ["WEBVTT", ""], [], []
    for i, seg in enumerate(segments, 1):
        text = seg.text.strip()
        srt += [str(i), f"{ts(seg.start)} --> {ts(seg.end)}", text, ""]
        vtt += [f"{ts(seg.start, '.')} --> {ts(seg.end, '.')}", text, ""]
        txt.append(text)
        for w in seg.words or []:
            words.append({"start": round(w.start, 3), "end": round(w.end, 3), "word": w.word.strip(), "probability": round(w.probability, 3)})
        print(f"[{ts(seg.start)} -> {ts(seg.end)}] {text}", file=sys.stderr)

    out.with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")
    out.with_suffix(".vtt").write_text("\n".join(vtt), encoding="utf-8")
    out.with_suffix(".txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    out.with_suffix(".words.json").write_text(json.dumps(words, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {out}.srt .vtt .txt .words.json", file=sys.stderr)

if __name__ == "__main__":
    main()
```

CPU tip: `--compute-type int8` roughly halves memory and time with negligible accuracy loss. GPU: `--device cuda --compute-type float16`.

## Step 2b: openai-whisper CLI

```bash
pip3 install -U openai-whisper
whisper audio.wav --model turbo --language en --output_format all --word_timestamps True --output_dir captions/
# Translate any language to English subtitles
whisper audio.wav --model turbo --task translate --output_format srt --output_dir captions/
```

Outputs `audio.srt`, `audio.vtt`, `audio.txt`, `audio.tsv`, `audio.json` (segments with words when `--word_timestamps True`). Add `--initial_prompt "..."` for jargon and `--fp16 False` on CPU to silence the warning.

## Step 2c: whisper.cpp

```bash
# macOS
brew install whisper-cpp
whisper-cli -m ~/.cache/whisper/ggml-large-v3-turbo.bin -l en -osrt -ovtt -of captions/audio audio.wav
# Models: https://huggingface.co/ggerganov/whisper.cpp/tree/main (download the ggml-*.bin you need)
```

Inside a Remotion project prefer `@remotion/install-whisper-cpp` which downloads the binary and model for you and returns captions typed for `@remotion/captions`.

## Step 3: shape the captions

Word-level JSON lets you build TikTok-style captions (a few words per cue, the active word highlighted). The `/remotion-captions` skill (`createTikTokStyleCaptions`) and the HyperFrames caption references consume exactly this shape: `{start, end, word}` in seconds or milliseconds. Convert ms if the consumer expects it (`startMs = round(start*1000)`).

Resegment an SRT into short cues (max 2 lines x 32 chars) from the word JSON when the raw segments are too long. A simple approach: walk the words, start a new cue whenever adding the next word would exceed 32 chars on the current line, or the gap to the next word is > 0.6 s, or the cue is > 3 s long.

## Step 4: use the result

```bash
# Burn in with ffmpeg (see /ffmpeg for styling)
ffmpeg -i input.mp4 -vf "subtitles=audio.srt:force_style='FontSize=28,Outline=2,MarginV=80'" -c:a copy captioned.mp4
```

Or load the SRT/JSON into the composition (`/remotion-captions`, `/hyperframes`).

For edit planning, read `audio.txt` with timestamps from stderr (or the SRT) and mark the lines to keep; convert their timestamps into `/ffmpeg` cut commands or `trimBefore`/`durationInFrames` props.

## Troubleshooting

- Hallucinated text during silence or music: keep `vad_filter=True` (faster-whisper) or trim the silence first with ffmpeg `silenceremove`.
- Repeated phrases looping: use a bigger model, set `condition_on_previous_text=False` (faster-whisper) / `--condition_on_previous_text False` (openai-whisper).
- Wrong language detected: pass `--language`.
- `CUDA out of memory`: smaller model, `int8_float16` compute type, or `--device cpu`.
- Model download blocked (no network to Hugging Face): download the model elsewhere and pass its local directory as `--model /path/to/model`.
- Timestamps drift on long files: split the audio into ~10 minute chunks with ffmpeg `-f segment -segment_time 600`, transcribe each, offset the times.
