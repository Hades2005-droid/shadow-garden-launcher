#!/bin/zsh
set -euo pipefail
BASE_DIR="${SHADOW_GARDEN_DIR:-$HOME/ShadowGarden}"
echo "Starting Shadow Garden sync..."
# Connector bridge health check — non-blocking, credential-free (never fails the launch).
"$BASE_DIR/scripts/connector_bridge_hook.sh" || true
"$BASE_DIR/scripts/save_grok.sh"
"$BASE_DIR/scripts/activate_voices.sh"
echo "Shadow Garden sync complete."
