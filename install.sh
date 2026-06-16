#!/usr/bin/env bash
# Shadow Garden Launcher — curl | bash entry (v4.3)
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/Hades2005-droid/shadow-garden-launcher/main/install.sh | bash
#   curl -fsSL ... | bash -s -- --perplexity
set -euo pipefail

SHADOW_GARDEN_DIR="${SHADOW_GARDEN_DIR:-$HOME/ShadowGarden}"
REPO_OWNER="${SHADOW_GARDEN_REPO_OWNER:-Hades2005-droid}"
REPO_NAME="${SHADOW_GARDEN_REPO_NAME:-shadow-garden-launcher}"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
BRANCH="${SHADOW_GARDEN_BRANCH:-main}"

if ! command -v git >/dev/null 2>&1; then
  echo "[launcher] git is required. Run: xcode-select --install" >&2
  exit 1
fi

mkdir -p "$(dirname "$SHADOW_GARDEN_DIR")"

if [[ -d "$SHADOW_GARDEN_DIR/.git" ]]; then
  echo "[launcher] Updating $SHADOW_GARDEN_DIR"
  git -C "$SHADOW_GARDEN_DIR" fetch origin "$BRANCH" --depth 1 2>/dev/null || git -C "$SHADOW_GARDEN_DIR" fetch origin "$BRANCH"
  git -C "$SHADOW_GARDEN_DIR" checkout "$BRANCH" 2>/dev/null || true
  git -C "$SHADOW_GARDEN_DIR" pull --ff-only origin "$BRANCH" 2>/dev/null || true
else
  echo "[launcher] Cloning $REPO_URL → $SHADOW_GARDEN_DIR"
  git clone --branch "$BRANCH" --depth 1 "$REPO_URL" "$SHADOW_GARDEN_DIR"
fi

exec bash "$SHADOW_GARDEN_DIR/install-local.sh" "$@"