---
name: ffmpeg
description: Cut, trim, concatenate, resize, crop, re-encode, extract audio, burn subtitles, make vertical/square versions, and export final deliverables with FFmpeg and ffprobe. Use for any command-line video or audio processing step that is not rendering a Remotion or HyperFrames composition (those have their own render skills). Also use to inspect a media file (duration, fps, resolution, codecs) before editing it.
---

# FFmpeg: cuts & exports

FFmpeg is the command-line tool for every mechanical edit on a finished media file. Compose with the other skills: `/yt-dlp` downloads references, `/whisper` makes subtitles, `/remotion-*` and `/hyperframes` render compositions, and FFmpeg does the cuts, conversions and final exports around them.

## Availability

```bash
ffmpeg -version | head -1 && ffprobe -version | head -1
```

If missing: `sudo apt-get install -y ffmpeg` (Debian/Ubuntu), `brew install ffmpeg` (macOS), or inside a Remotion project `npx remotion ffmpeg ...` and `npx remotion ffprobe ...` work without a system install.

## Rules

1. **Inspect first.** Run ffprobe before editing so you know the real fps, resolution, rotation and audio layout. Never guess.
2. **Never overwrite the source.** Write to a new file. Pass `-y` only when you intend to overwrite the output.
3. **Stream copy (`-c copy`) only cuts on keyframes.** For frame-accurate trims re-encode with `-c:v libx264 -c:a aac`. Put `-ss` *before* `-i` for fast seeking; with re-encoding the result is still exact.
4. **Deliverables are H.264 + AAC in MP4 with `-pix_fmt yuv420p` and `-movflags +faststart`.** That plays everywhere (TikTok, Reels, Shorts, YouTube, browsers).
5. **Even dimensions.** H.264 needs width and height divisible by 2: use `scale=-2:1080` not `-1:1080`.
6. **Quote filter graphs** in single quotes so the shell does not eat `,` `;` `:`.
7. **Keep it short and reversible**: one operation per command when debugging, chain filters only once each step works.

## Inspect

```bash
# Human summary
ffprobe -hide_banner input.mp4

# Machine-readable: duration (s), fps, width, height, codecs
ffprobe -v error -show_entries format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,sample_rate,channels \
  -of json input.mp4

# Just the duration in seconds
ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 input.mp4
```

## Trim / cut

```bash
# Frame-accurate cut from 00:05 to 00:12 (re-encodes)
ffmpeg -ss 00:00:05 -to 00:00:12 -i input.mp4 -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -movflags +faststart out.mp4

# Fast lossless cut (keyframe-aligned, may start up to a GOP early)
ffmpeg -ss 00:00:05 -to 00:00:12 -i input.mp4 -c copy out.mp4

# Keep only the first 30 seconds
ffmpeg -i input.mp4 -t 30 -c:v libx264 -crf 18 -c:a aac out.mp4
```

## Concatenate clips

Same codec/resolution/fps: write a list file and use the concat demuxer.

```bash
printf "file '%s'\n" clip1.mp4 clip2.mp4 clip3.mp4 > list.txt
ffmpeg -f concat -safe 0 -i list.txt -c copy joined.mp4
```

Different sources: normalise through the concat filter (re-encodes).

```bash
ffmpeg -i a.mp4 -i b.mp4 -filter_complex \
 '[0:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v0];
  [1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=30[v1];
  [v0][0:a][v1][1:a]concat=n=2:v=1:a=1[v][a]' \
 -map '[v]' -map '[a]' -c:v libx264 -crf 18 -c:a aac joined.mp4
```

## Resize, crop, reframe

```bash
# 1080p, keep aspect
ffmpeg -i in.mp4 -vf 'scale=-2:1080' -c:v libx264 -crf 18 -c:a copy out.mp4

# Vertical 9:16 (1080x1920): centre-crop
ffmpeg -i in.mp4 -vf 'scale=-2:1920,crop=1080:1920' -c:v libx264 -crf 18 -c:a copy vertical.mp4

# Vertical 9:16 with blurred background instead of cropping
ffmpeg -i in.mp4 -filter_complex \
 '[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=20[bg];
  [0:v]scale=1080:-2[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2' \
 -c:v libx264 -crf 18 -c:a copy vertical_blur.mp4

# Square 1:1
ffmpeg -i in.mp4 -vf 'scale=1080:1080:force_original_aspect_ratio=increase,crop=1080:1080' -c:v libx264 -crf 18 -c:a copy square.mp4

# Fix phone videos whose rotation metadata confuses tools
ffmpeg -i in.mp4 -vf 'transpose=1' -c:v libx264 -crf 18 -c:a copy rotated.mp4   # 1=90° CW, 2=90° CCW
```

## Speed, fps, still frames, GIF

```bash
# 2x speed (video + audio)
ffmpeg -i in.mp4 -filter_complex '[0:v]setpts=0.5*PTS[v];[0:a]atempo=2.0[a]' -map '[v]' -map '[a]' fast.mp4

# Convert to 30 fps
ffmpeg -i in.mp4 -vf 'fps=30' -c:v libx264 -crf 18 -c:a copy out30.mp4

# Thumbnail at 3 s
ffmpeg -ss 3 -i in.mp4 -frames:v 1 -q:v 2 thumb.jpg

# Image sequence -> video (e.g. frames rendered elsewhere)
ffmpeg -framerate 30 -i frames/frame_%04d.png -c:v libx264 -pix_fmt yuv420p -crf 18 out.mp4

# High-quality GIF
ffmpeg -i in.mp4 -vf 'fps=15,scale=640:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse' out.gif
```

## Audio

```bash
# Extract audio
ffmpeg -i in.mp4 -vn -c:a aac -b:a 192k audio.m4a
ffmpeg -i in.mp4 -vn -ar 16000 -ac 1 audio.wav      # 16 kHz mono: what /whisper wants

# Replace the audio track
ffmpeg -i video.mp4 -i voiceover.wav -map 0:v -map 1:a -c:v copy -c:a aac -shortest out.mp4

# Mix music under the original audio (music at 20%)
ffmpeg -i video.mp4 -i music.mp3 -filter_complex '[1:a]volume=0.2[m];[0:a][m]amix=inputs=2:duration=first' -c:v copy -c:a aac out.mp4

# Normalise loudness for social (EBU R128, -14 LUFS)
ffmpeg -i in.mp4 -af 'loudnorm=I=-14:TP=-1.5:LRA=11' -c:v copy -c:a aac out.mp4

# Fade in/out (first 1 s, last 1 s of a 20 s clip)
ffmpeg -i in.mp4 -vf 'fade=t=in:st=0:d=1,fade=t=out:st=19:d=1' -af 'afade=t=in:st=0:d=1,afade=t=out:st=19:d=1' out.mp4

# Mute
ffmpeg -i in.mp4 -an -c:v copy silent.mp4
```

## Subtitles and overlays

```bash
# Burn in an SRT (hard subs)
ffmpeg -i in.mp4 -vf "subtitles=captions.srt:force_style='FontName=Inter,FontSize=28,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,Outline=2,Alignment=2,MarginV=80'" -c:v libx264 -crf 18 -c:a copy subbed.mp4

# Burn in ASS (styled, karaoke/word-highlight)
ffmpeg -i in.mp4 -vf 'ass=captions.ass' -c:v libx264 -crf 18 -c:a copy subbed.mp4

# Soft subs (toggleable track, MP4)
ffmpeg -i in.mp4 -i captions.srt -c copy -c:s mov_text -metadata:s:s:0 language=eng out.mp4

# Watermark / logo bottom-right
ffmpeg -i in.mp4 -i logo.png -filter_complex 'overlay=W-w-40:H-h-40' -c:v libx264 -crf 18 -c:a copy out.mp4

# Text overlay
ffmpeg -i in.mp4 -vf "drawtext=text='Hello':fontsize=64:fontcolor=white:x=(w-text_w)/2:y=h-200:box=1:boxcolor=black@0.5:boxborderw=20" -c:a copy out.mp4
```

## Export presets

```bash
# Universal social / web deliverable
ffmpeg -i in.mp4 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -c:a aac -b:a 192k -movflags +faststart final.mp4

# Small file (email/Slack), ~2 Mbps target
ffmpeg -i in.mp4 -c:v libx264 -preset slow -b:v 2M -maxrate 2.5M -bufsize 5M -c:a aac -b:a 128k -movflags +faststart small.mp4

# Hardware-agnostic high quality archive
ffmpeg -i in.mp4 -c:v libx264 -preset slow -crf 14 -c:a aac -b:a 320k archive.mp4

# WebM (VP9 + Opus) for web embeds
ffmpeg -i in.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus out.webm

# Transparent video (from a Remotion/HyperFrames alpha render) -> ProRes 4444 or VP9 with alpha
ffmpeg -i in.mov -c:v prores_ks -profile:v 4444 -pix_fmt yuva444p10le out.mov
ffmpeg -i in.mov -c:v libvpx-vp9 -pix_fmt yuva420p out.webm
```

CRF guide for libx264: 14 near-lossless, 18 visually lossless, 23 default, 28 small. Presets trade speed for size: `ultrafast` for previews, `slow` for finals.

## Verify the result

Always check the output before reporting done:

```bash
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height,r_frame_rate -of compact out.mp4
```

Expect the duration you asked for, `h264`/`aac`, even dimensions, and the intended fps. If the user will watch it, also pull one still from the middle with `-ss <mid> -frames:v 1` and look at it.

## Troubleshooting

- `height not divisible by 2`: use `scale=-2:H` or add `pad=ceil(iw/2)*2:ceil(ih/2)*2`.
- Frozen or black first frames after a `-c copy` cut: re-encode (rule 3).
- Audio drifts after concat: give every input the same sample rate (`-ar 48000`) and use the concat filter, not the demuxer.
- `Unknown encoder 'libx264'`: the build lacks x264; install a full build (`apt-get install ffmpeg` from Ubuntu is fine) or use `-c:v mpeg4` as a last resort.
- Rotation looks wrong: phones store rotation in metadata; `-noautorotate` disables auto-rotation, or bake it in with `transpose`.
- Subtitles filter cannot find fonts: install fonts (`fonts-inter`, `fonts-noto`) or pass `:fontsdir=./fonts`.
