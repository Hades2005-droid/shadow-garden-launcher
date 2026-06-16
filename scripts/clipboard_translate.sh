#!/bin/zsh
# Polls clipboard and logs translations. Start manually or via LaunchAgent.
set -euo pipefail
BASE_DIR="${SHADOW_GARDEN_DIR:-$HOME/ShadowGarden}"
TARGET="${TARGET_LANG:-es}"
LOG_DIR="$BASE_DIR/logs"
OUT_DIR="$HOME/Documents/Translations"
mkdir -p "$LOG_DIR" "$OUT_DIR"
PREV=""
echo "[$(date)] Clipboard translator started for target=$TARGET" >> "$LOG_DIR/clipboard_translate.log"
while true; do
  CURRENT=$(pbpaste || true)
  if [[ "$CURRENT" != "$PREV" && -n "${CURRENT//[[:space:]]/}" ]]; then
    PREV="$CURRENT"
    if RESULT=$("$BASE_DIR/scripts/translation_router.sh" "$TARGET" "$CURRENT" 2>>"$LOG_DIR/clipboard_translate.err"); then
      TRANSLATED=$(echo "$RESULT" | jq -r '.translated // .best_search_phrase // .literal_translation // empty' 2>/dev/null || true)
      NOTES=$(echo "$RESULT" | jq -r '.nuance_notes // empty' 2>/dev/null || true)
      printf '[%s] [%s] %s | NUANCE: %s\n' "$(date)" "$TARGET" "$TRANSLATED" "$NOTES" >> "$OUT_DIR/clipboard_log.txt"
      osascript -e "display notification \"${TRANSLATED:0:180}\" with title \"Translation → $TARGET\" subtitle \"${NOTES:0:80}\"" 2>/dev/null || true
    fi
  fi
  sleep "${CLIPBOARD_TRANSLATE_INTERVAL:-1}"
done
