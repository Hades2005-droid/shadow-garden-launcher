#!/bin/zsh
# Shadow Garden connector bridge hook — NON-BLOCKING.
# Drop this call into any terminal point (.command, .sh, launch agent):
#     "$BASE_DIR/scripts/connector_bridge_hook.sh" || true
#
# Reconciles the connector table to monitors/state.json and prints an alert
# ONLY on a real 'error' status. Never handles credentials. Every step is
# guarded with `|| true` and the script always ends `exit 0`, so it can never
# break the launch it is attached to. Works under zsh (Mac) and bash.

# Resolve repo dir whether launched from anywhere. ${0:A:h} is zsh; the
# ${BASH_SOURCE} fallback covers bash.
if [ -n "${ZSH_VERSION:-}" ]; then
  HOOK_DIR="${0:A:h}"
else
  HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
fi
REPO_DIR="${SHADOW_GARDEN_DIR:-$(dirname "$HOOK_DIR")}"
BRIDGE="$REPO_DIR/monitors/connector_bridge.py"
STATE="$REPO_DIR/monitors/state.json"

if [ -f "$BRIDGE" ]; then
  NOW="$(date -u +%Y-%m-%dT%H:%M:%S%z 2>/dev/null || echo unknown)"
  if python3 "$BRIDGE" probe --now "$NOW" --out "$STATE" >/dev/null 2>&1; then
    python3 - "$STATE" <<'PY' 2>/dev/null || true
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
a = d.get("alert", {})
if a.get("should_alert"):
    errs = [k for k, v in d.get("results", {}).items() if v.get("status") == "error"]
    print(f"warning: connector alert - error on {', '.join(errs)}")
    if a.get("x_waterfall_priority"):
        print(f"   X waterfall: x_status={a.get('x_status')}")
else:
    print("ok: connectors nominal (bridge)")
PY
  else
    echo "info: connector bridge skipped (probe failed, non-fatal)" || true
  fi
else
  echo "info: connector bridge not found at $BRIDGE (skipped)" || true
fi

# Always succeed — this hook must never fail a launch.
exit 0
