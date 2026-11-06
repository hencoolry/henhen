#!/usr/bin/env bash
# Installs the command-line tools the skills in .claude/skills depend on.
# Safe to re-run. Remotion and HyperFrames are installed per project via npx when a skill runs.
set -euo pipefail

have() { command -v "$1" >/dev/null 2>&1; }

echo "== ffmpeg"
if have ffmpeg; then ffmpeg -version | head -1
elif have apt-get; then sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg
elif have brew; then brew install ffmpeg
else echo "install ffmpeg manually: https://ffmpeg.org/download.html"; fi

echo "== yt-dlp"
python3 -m pip install -q -U yt-dlp
yt-dlp --version

echo "== whisper (faster-whisper)"
python3 -m pip install -q -U faster-whisper
python3 -c 'import faster_whisper; print("faster-whisper", faster_whisper.__version__)'

echo "== node"
if have node; then node --version; else echo "install Node 20+ for Remotion and HyperFrames: https://nodejs.org"; fi

echo "== skills"
ls -1 .claude/skills
echo "done. Refresh the vendored skills later with: npx skills update"
