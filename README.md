# henhen

Claude Code skills for AI video editing and frontend design. Open this repo in Claude Code and the skills under `.claude/skills/` load automatically.

| Tool | Role | Skills |
|---|---|---|
| Remotion | video compositions in React | `/remotion-best-practices`, `/remotion-create`, `/remotion-markup`, `/remotion-render`, `/remotion-studio`, `/remotion-captions`, `/remotion-multimedia`, `/remotion-interactivity`, `/remotion-maps`, `/remotion-saas`, `/remotion-docs`, `/remotion-upgrade`, `/remotion-license` |
| HyperFrames | graphics: HTML rendered to video | `/hyperframes`, `/hyperframes-cli`, `/hyperframes-registry`, `/media-use` |
| FFmpeg | cuts & exports | `/ffmpeg` |
| Whisper | subtitles | `/whisper` |
| yt-dlp | downloads references | `/yt-dlp` |

## Design skills

| Tool | Role | Skills |
|---|---|---|
| Stageshow (`benjitaylor/skills`) | UI animations and bento demos | `/stageshow` |
| Dimensional Drawing (`enesozturk/dimensional-drawing`) | spec sheets of your components | `/dimensional-drawing`, `/dimensional-drawing-motion` |
| Oil UI (`oil-oil/oil-ui`) | explore design directions | `/oil-ui` |
| Emil Kowalski (`emilkowalski/skills`) | motion and UI details | `/animate`, `/choreograph`, `/gestures`, `/emil-design-eng`, `/review-animations`, `/improve-animations`, `/apple-design`, `/break-ui` and 11 more |
| Taste Skill (`Leonxlnx/taste-skill`) | art direction and real-browser checks | `/design-taste-frontend` |
| Impeccable (`pbakaus/impeccable`) | polish, kills AI slop | `/impeccable` |
| Design.how (`arla6ka/design.how`) | design systems for agents | `/design-system-boss`, `/build-design-system`, `/migrate-design-system`, `/token-mapping`, `/component-docs`, `/ui-review` |

Notes:

- `oil-ui` checks ui.oiloil.org for updates when it loads. Set `OIL_NO_UPDATE_CHECK=1` to turn that off.
- Design.how also offers visual effects and ready-made design systems that install one at a time, for example `npx skills add https://design.how/vault/warp-type`.

### Awwwards MCP

References from award-winning sites come from an MCP server, not a skill. It is already registered in `.mcp.json`, so it travels with the repo. Claude Code asks you to approve it the first time you open the project.

It offers site search, design briefs, live-site capture, motion and scroll analysis, design-token export and more. To re-add it by hand:

```bash
claude mcp add --scope project awwwards -- npx -y awwwards-mcp
```

## Setup

```bash
./scripts/setup-tools.sh
```

Installs ffmpeg, yt-dlp and faster-whisper if missing. Remotion and HyperFrames install themselves per project through `npx` when their skills run.

## Keeping the vendored skills current

Skills from other repositories are copied in and pinned in `skills-lock.json`.

```bash
npx skills update            # refresh every vendored skill package
npx skills add heygen-com/hyperframes --skill slideshow   # add an optional HyperFrames skill
```

The `ffmpeg`, `whisper` and `yt-dlp` skills are maintained in this repo: neither project publishes an official agent skill, and the community ones are OpenClaw-specific wrappers. The Whisper skill ships a runnable transcriber at `.claude/skills/whisper/scripts/transcribe.py`.

## Typical flow

1. `/yt-dlp` pulls a reference clip into `refs/`.
2. `/whisper` transcribes it to SRT and word-level JSON.
3. `/remotion-create` or `/hyperframes` builds the composition, with captions from step 2.
4. `/ffmpeg` cuts, reframes to 9:16 and exports the deliverable.
