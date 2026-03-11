#!/usr/bin/env bash
set -euo pipefail

INBOX_DIR="$HOME/.openclaw/skills/video-pipeline/scripts/user_clips/inbox"
mkdir -p "$INBOX_DIR"

if [ "$#" -lt 1 ]; then
  echo "Usage: add_user_clip.sh /path/to/clip.mp4 [more clips...]" >&2
  exit 1
fi

for source in "$@"; do
  if [ ! -f "$source" ]; then
    echo "Skipping missing file: $source" >&2
    continue
  fi

  ext="${source##*.}"
  ext="${ext,,}"
  case "$ext" in
    mp4|mov|m4v|webm) ;;
    *)
      echo "Skipping unsupported format: $source" >&2
      continue
      ;;
  esac

  base="$(basename "$source")"
  stem="${base%.*}"
  safe_stem="$(printf "%s" "$stem" | tr -cs 'A-Za-z0-9._-' '_')"
  target="$INBOX_DIR/$(date +%Y%m%d-%H%M%S)_${safe_stem}.${ext}"
  cp -f "$source" "$target"
  echo "Queued clip: $target"
done