#!/bin/zsh
set -euo pipefail
touch "$HOME/.zshrc"
for LINE in \
  'alias sg="$HOME/ShadowGarden/master_sync.sh"' \
  'alias sg-bridge="python3 $HOME/ShadowGarden/bridge.py"' \
  'alias sg-voice="SG_SYNTHESIZE=1 $HOME/ShadowGarden/master_sync.sh"'
do
  if ! grep -Fq "$LINE" "$HOME/.zshrc"; then
    echo "$LINE" >> "$HOME/.zshrc"
  fi
done
echo "Aliases installed: sg, sg-bridge, sg-voice"
echo "Open a new terminal or run: source ~/.zshrc"
