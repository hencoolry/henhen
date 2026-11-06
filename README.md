# henhen

Claude Code skills for an AI video-editing workflow. Open this repo in Claude Code and the skills under `.claude/skills/` load automatically.

| Tool | Role | Skills |
|---|---|---|
| Remotion | video compositions in React | `/remotion-best-practices`, `/remotion-create`, `/remotion-markup`, `/remotion-render`, `/remotion-studio`, `/remotion-captions`, `/remotion-multimedia`, `/remotion-interactivity`, `/remotion-maps`, `/remotion-saas`, `/remotion-docs`, `/remotion-upgrade`, `/remotion-license` |
| HyperFrames | graphics: HTML rendered to video | `/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry`, `/media-use` |
| FFmpeg | cuts & exports | `/ffmpeg` |
| Whisper | subtitles | `/whisper` |
| yt-dlp | downloads references | `/yt-dlp` |

## Setup

```bash
./scripts/setup-tools.sh
```

Installs ffmpeg, yt-dlp and faster-whisper if missing. Remotion and HyperFrames install themselves per project through `npx` when their skills run.

## Keeping the vendored skills current

The Remotion and HyperFrames skills are copied from their official repositories and pinned in `skills-lock.json`.

```bash
npx skills update            # refresh remotion-dev/skills and heygen-com/hyperframes
npx skills add heygen-com/hyperframes --skill slideshow   # add an optional HyperFrames skill
```

The `ffmpeg`, `whisper` and `yt-dlp` skills are maintained in this repo: neither project publishes an official agent skill, and the community ones are OpenClaw-specific wrappers. The Whisper skill ships a runnable transcriber at `.claude/skills/whisper/scripts/transcribe.py`.

## Typical flow

1. `/yt-dlp` pulls a reference clip into `refs/`.
2. `/whisper` transcribes it to SRT and word-level JSON.
3. `/remotion-create` or `/hyperframes` builds the composition, with captions from step 2.
4. `/ffmpeg` cuts, reframes to 9:16 and exports the deliverable.
