#!/bin/zsh
set -euo pipefail
BASE_DIR="${SHADOW_GARDEN_DIR:-$HOME/ShadowGarden}"
echo "Starting Shadow Garden sync..."
"$BASE_DIR/scripts/save_grok.sh"
"$BASE_DIR/scripts/activate_voices.sh"
echo "Shadow Garden sync complete."
