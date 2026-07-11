#!/bin/sh
# Local playable launcher for shadowgarden_unified_game (offline, stdlib-only).
# Runs the default catalyst arc. No network, no credentials, no code exec from data.
set -eu
HERE="$(cd "$(dirname "$0")" && pwd)"
exec python3 "${HERE}/../south_star/shadowgarden_unified_game.py" \
  --seed 42 --mastery 10 \
  --actions launch emperor fable harmony chariot land
