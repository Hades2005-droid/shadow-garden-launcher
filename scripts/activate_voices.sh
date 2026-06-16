#!/bin/zsh
# Shadow Garden voice activation — logs safe prompts; optional Grok synthesis.
set -euo pipefail
BASE_DIR="${SHADOW_GARDEN_DIR:-$HOME/ShadowGarden}"
LOG_DIR="$BASE_DIR/logs"
mkdir -p "$LOG_DIR" "$BASE_DIR/voices" "$BASE_DIR/data"

if [[ "${SG_SYNTHESIZE:-0}" == "1" ]]; then
  python3 "$BASE_DIR/bridge.py" --synthesize
else
  python3 "$BASE_DIR/bridge.py"
fi
