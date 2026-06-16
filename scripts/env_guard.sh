#!/bin/zsh
# Loads local env without printing secrets. Never put API keys directly in scripts.
set -euo pipefail
ENV_CANDIDATES=(
  "$HOME/Movies/Grok-Videos/.env"
  "$HOME/shadow_garden_may30_monitoring/live/.xai.env"
  "$HOME/ShadowGarden/.env"
)
for env_file in "${ENV_CANDIDATES[@]}"; do
  if [[ -f "$env_file" ]]; then
    set -a
    source "$env_file"
    set +a
    export ACTIVE_SHADOW_GARDEN_ENV="$env_file"
    break
  fi
done
if [[ -z "${XAI_API_KEY:-}" ]]; then
  echo "Missing XAI_API_KEY. Add it to ~/ShadowGarden/.env or an existing local .env file." >&2
  exit 64
fi
