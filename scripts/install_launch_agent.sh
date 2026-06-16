#!/bin/zsh
set -euo pipefail
LABEL="com.shadowgarden.clipboardtranslate"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PLIST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>$HOME/ShadowGarden/scripts/clipboard_translate.sh</string>
  </array>
  <key>RunAtLoad</key><false/>
  <key>KeepAlive</key><false/>
  <key>StandardOutPath</key><string>$HOME/ShadowGarden/logs/clipboard_launch.out</string>
  <key>StandardErrorPath</key><string>$HOME/ShadowGarden/logs/clipboard_launch.err</string>
</dict>
</plist>
PLIST
launchctl unload "$PLIST" >/dev/null 2>&1 || true
launchctl load "$PLIST"
echo "LaunchAgent installed but not auto-started. Start it with: launchctl start $LABEL"
