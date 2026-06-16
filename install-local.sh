#!/usr/bin/env bash
# Shadow Garden local install (run after clone or from repo checkout)
set -euo pipefail

BASE_DIR="${SHADOW_GARDEN_DIR:-$HOME/ShadowGarden}"
RUN_PERPLEXITY=0

for arg in "$@"; do
  case "$arg" in
    --perplexity) RUN_PERPLEXITY=1 ;;
  esac
done

echo "[Shadow Garden] Installing to $BASE_DIR"
mkdir -p \
  "$BASE_DIR/chats" \
  "$BASE_DIR/data" \
  "$BASE_DIR/logs" \
  "$BASE_DIR/voices" \
  "$BASE_DIR/scripts" \
  "$BASE_DIR/templates" \
  "$BASE_DIR/research"

chmod +x "$BASE_DIR/master_sync.sh" 2>/dev/null || true
chmod +x "$BASE_DIR/install-local.sh" 2>/dev/null || true
chmod +x "$BASE_DIR/scripts/"*.sh 2>/dev/null || true
chmod +x "$BASE_DIR/bridge.py" 2>/dev/null || true
chmod +x "$BASE_DIR/scripts/perplexity_research.py" 2>/dev/null || true

if [[ -x "$BASE_DIR/scripts/install_alias.sh" ]]; then
  zsh "$BASE_DIR/scripts/install_alias.sh"
fi

if [[ ! -f "$BASE_DIR/.env" && -f "$BASE_DIR/.env.example" ]]; then
  cp "$BASE_DIR/.env.example" "$BASE_DIR/.env"
  echo "[Shadow Garden] Created $BASE_DIR/.env — add keys locally."
fi

if [[ "$RUN_PERPLEXITY" == "1" ]]; then
  python3 "$BASE_DIR/scripts/perplexity_research.py" \
    "Shadow Garden launcher v4.3 post-install checklist: macOS zsh aliases, xAI Grok voice agent env, safe curl installer idempotency, Perplexity research hook."
fi

echo "[Shadow Garden] Install complete."
echo "  sg          — save clipboard + log voice prompts"
echo "  sg-bridge   — prompt log only"
echo "  sg-voice    — save + Grok voice synthesis"
echo "  Run: source ~/.zshrc"