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
