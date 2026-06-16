#!/bin/zsh
# Runs the existing local transcription pipeline, then translates latest transcript.
set -euo pipefail
BASE_DIR="${SHADOW_GARDEN_DIR:-$HOME/ShadowGarden}"
TARGET="${1:-${TARGET_LANG:-ja}}"
TRANSCRIPT="${2:-$HOME/Documents/Transcripts/latest.txt}"
if [[ ! -s "$TRANSCRIPT" && -x /tmp/toolkit/transcribe.sh ]]; then
  /tmp/toolkit/transcribe.sh
fi
if [[ ! -s "$TRANSCRIPT" ]]; then
  echo "Transcript not found or empty: $TRANSCRIPT" >&2
  exit 66
fi
"$BASE_DIR/scripts/translation_router.sh" "$TARGET" "$(cat "$TRANSCRIPT")"
