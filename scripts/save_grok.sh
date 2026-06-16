#!/bin/zsh
# Shadow Garden Universal Grok Chat Saver — hardened, no secrets.
set -euo pipefail
umask 077

BASE_DIR="${SHADOW_GARDEN_DIR:-$HOME/ShadowGarden}"
CHAT_DIR="$BASE_DIR/chats"
LOG_DIR="$BASE_DIR/logs"
ICLOUD_DIR="$HOME/Library/Mobile Documents/com~apple~CloudDocs/ShadowGarden"
TIMESTAMP=$(date "+%Y-%m-%d_%H-%M-%S")
FILE="$CHAT_DIR/grok_chat_$TIMESTAMP.md"

mkdir -p "$CHAT_DIR" "$LOG_DIR" "$ICLOUD_DIR"
CLIPBOARD_TEXT=$(pbpaste || true)
if [[ -z "${CLIPBOARD_TEXT//[[:space:]]/}" ]]; then
  echo "[save_grok] Clipboard is empty; nothing saved." | tee -a "$LOG_DIR/save_grok.log"
  exit 2
fi

{
  echo "# Grok Chat — $TIMESTAMP"
  echo
  echo "Captured from macOS clipboard."
  echo
  echo "---"
  echo
  printf "%s\n" "$CLIPBOARD_TEXT"
  echo
  echo "---"
  echo "End of chat."
} > "$FILE"

cp "$FILE" "$ICLOUD_DIR/" 2>/dev/null || echo "[save_grok] iCloud copy skipped or failed." >> "$LOG_DIR/save_grok.log"

if command -v git >/dev/null 2>&1 && [[ -d "$BASE_DIR/.git" ]]; then
  (cd "$BASE_DIR" && git add chats/ && git commit -m "Grok chat $TIMESTAMP" && git push) >> "$LOG_DIR/git_sync.log" 2>&1 || true
fi

echo "Saved to: $FILE"
