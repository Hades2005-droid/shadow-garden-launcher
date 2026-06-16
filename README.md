# Shadow Garden Launcher v4.3

One-line install for the Shadow Garden Grok sync + voice bridge on macOS.

## Quick install

```bash
curl -fsSL https://raw.githubusercontent.com/Hades2005-droid/shadow-garden-launcher/main/install.sh | bash
```

With Perplexity Sonar research pass (requires `PERPLEXITY_API_KEY` in env or `~/ShadowGarden/.env`):

```bash
curl -fsSL https://raw.githubusercontent.com/Hades2005-droid/shadow-garden-launcher/main/install.sh | bash -s -- --perplexity
```

Then:

```bash
source ~/.zshrc
sg
```

## Fork / custom owner

If you publish under a different GitHub user (e.g. `fredwashere`):

```bash
SHADOW_GARDEN_REPO_OWNER=fredwashere \
  curl -fsSL https://raw.githubusercontent.com/fredwashere/shadow-garden-launcher/main/install.sh | bash
```

## Commands

| Command | Description |
|---------|-------------|
| `sg` | Save clipboard Grok chat + log safe voice prompts |
| `sg-bridge` | Voice prompt log only |
| `sg-voice` | Save + Grok Voice Agent WAV synthesis |

## Secrets (never committed)

Scripts load keys from, in order:

1. `~/Movies/Grok-Videos/.env`
2. `~/shadow_garden_may30_monitoring/live/.xai.env`
3. `~/ShadowGarden/.env`

Copy `.env.example` → `.env` and fill locally.

## Perplexity

```bash
python3 ~/ShadowGarden/scripts/perplexity_research.py "your topic"
```

Saves structured markdown to `~/ShadowGarden/research/`.

## Layout

```
~/ShadowGarden/
  install.sh          # curl entry (clone + install-local)
  install-local.sh    # dirs, aliases, optional Perplexity
  bridge.py           # safe voice bridge v4.3
  master_sync.sh      # sg entry
  scripts/
  research/
  templates/
```

## Related

- Grok Voice Agent: `~/Movies/Grok-Videos/grok-voice-agent`
- 4.2 Sovereign lattice: `sovereign-lattice-42.mjs` in voice agent dir