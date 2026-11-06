---
name: yt-dlp
description: Download reference videos, audio, thumbnails, subtitles and metadata from YouTube, TikTok, Instagram, Vimeo, X and 1,000+ other sites with yt-dlp, for use as editing references, b-roll sources, or transcript input. Use whenever a video URL needs to become a local file.
---

# yt-dlp: download references

yt-dlp fetches a URL into a local media file. It feeds the rest of the pipeline: `/ffmpeg` cuts and converts it, `/whisper` transcribes it, `/remotion-*` and `/hyperframes` embed it.

## Availability

```bash
yt-dlp --version
```

Install or update (pick one):

```bash
pip3 install -U yt-dlp            # Python (works anywhere pip works)
brew install yt-dlp               # macOS
sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && sudo chmod a+rx /usr/local/bin/yt-dlp
```

Site extractors break often. If a download fails with an extractor error, the first fix is `pip3 install -U yt-dlp` (or `yt-dlp -U` for the binary) and retry.

FFmpeg must be installed for merging video and audio streams and for `--extract-audio`.

## Rules

1. **Only download what the person has the right to use.** References for study and analysis are fine. Say so plainly if a request looks like redistributing someone else's content.
2. **Download into a dedicated directory** (e.g. `refs/`) and name files predictably with `-o`. Never download into the project root.
3. **Default to MP4 (H.264 + AAC)** so every downstream tool can read it without re-encoding.
4. **Keep the metadata.** Save the JSON sidecar when the title, author, upload date or URL will matter later.
5. **Inspect before bulk.** For a playlist or channel, list first with `--flat-playlist`, then download a bounded subset.
6. **Do not loop retries or hammer a site.** One update-and-retry is enough; then report the error.

## Everyday commands

```bash
# Best quality MP4 up to 1080p, merged, predictable filename
yt-dlp -f 'bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b' \
  --merge-output-format mp4 -o 'refs/%(title).80s [%(id)s].%(ext)s' URL

# Audio only (for /whisper or music reference)
yt-dlp -x --audio-format mp3 --audio-quality 0 -o 'refs/%(title).80s [%(id)s].%(ext)s' URL
yt-dlp -x --audio-format wav --postprocessor-args 'ffmpeg:-ar 16000 -ac 1' -o 'refs/%(id)s.%(ext)s' URL   # 16 kHz mono, whisper-ready

# Thumbnail and metadata alongside the video
yt-dlp --write-thumbnail --convert-thumbnails jpg --write-info-json -o 'refs/%(id)s.%(ext)s' URL

# Only the metadata (no media)
yt-dlp --skip-download --write-info-json -o 'refs/%(id)s' URL
yt-dlp --dump-json URL | jq '{title, uploader, duration, view_count, upload_date, webpage_url}'

# Subtitles / auto-captions as SRT (no media)
yt-dlp --skip-download --write-subs --write-auto-subs --sub-langs 'en.*' --convert-subs srt -o 'refs/%(id)s' URL

# Just a section of a long video (needs ffmpeg; re-encodes the cut)
yt-dlp --download-sections '*00:01:30-00:02:15' --force-keyframes-at-cuts -f 'bv*[ext=mp4]+ba[ext=m4a]' -o 'refs/%(id)s_clip.%(ext)s' URL

# See available formats before choosing
yt-dlp -F URL
```

## Playlists and channels

```bash
# List entries without downloading
yt-dlp --flat-playlist --print '%(playlist_index)s  %(id)s  %(title)s' PLAYLIST_URL

# Download the first 5 as MP4
yt-dlp --playlist-items 1-5 -f 'bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b' \
  -o 'refs/%(playlist_index)03d - %(title).60s [%(id)s].%(ext)s' PLAYLIST_URL

# Everything a channel posted in the last 30 days
yt-dlp --dateafter now-30days --break-on-reject -o 'refs/%(upload_date)s %(title).60s [%(id)s].%(ext)s' CHANNEL_URL
```

## Site notes

- **TikTok / Instagram / X**: public posts usually work with no flags. Private or age-gated content needs `--cookies-from-browser chrome` (or `firefox`, `safari`) run on the person's own machine; never ask them to paste cookies into chat.
- **YouTube "Sign in to confirm you're not a bot"**: update yt-dlp first; then `--cookies-from-browser` on the person's machine. Cloud/CI IPs are often blocked and there is no reliable workaround from a server.
- **Shorts / Reels** are vertical already. Check with `ffprobe` before assuming a 16:9 reframe is needed.
- **Live streams**: `--live-from-start` records from the beginning when the site supports it.

## Useful flags

| Flag | Effect |
|---|---|
| `-o TEMPLATE` | Output filename template (`%(title)s`, `%(id)s`, `%(ext)s`, `%(upload_date)s`, `%(uploader)s`) |
| `-f FORMAT` | Format selector; `-F` lists them |
| `--merge-output-format mp4` | Container after merging separate video and audio |
| `-x --audio-format mp3\|wav\|m4a` | Extract audio |
| `--download-sections '*START-END'` | Partial download |
| `--write-info-json` / `--write-thumbnail` / `--write-subs` | Sidecars |
| `--no-playlist` | A video URL that is also in a playlist: only that video |
| `--restrict-filenames` | ASCII-only, no spaces (safe for scripts) |
| `--limit-rate 5M` | Be polite on shared connections |
| `--cookies-from-browser BROWSER` | Logged-in access, on the person's machine only |
| `-q --progress` | Quiet except the progress bar (good in agent logs) |

## After downloading

Verify and hand off:

```bash
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height -of compact refs/FILE.mp4
```

Then continue with `/ffmpeg` (cuts, reframe), `/whisper` (transcript, subtitles) or the composition skills.

## Troubleshooting

- `ERROR: Unable to extract ...` / `HTTP Error 403`: update yt-dlp, retry once.
- `Requested format is not available`: run `-F` and pick a listed format, or drop to `-f b`.
- `ffmpeg not found`: install ffmpeg (see `/ffmpeg`); without it only single-file formats work.
- Slow or stalled download: add `--concurrent-fragments 4` for HLS/DASH sources.
- Filename too long: cap the title with `%(title).80s` as in the examples.
