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

## NWW Asana Connector (optional)

Additive reporting adapter that pushes Shadow Garden operational signals to
Asana: voice synthesis latency/quality, Grok chat sync status, message counts,
and sanitized conversation summaries. Shadow Garden stays **Jira-first** — Asana
reporting is disabled unless `ASANA_ACCESS_TOKEN` is set, and nothing else in the
existing flow changes.

### Setup

Add to `~/ShadowGarden/.env` (see `.env.example`):

```bash
ASANA_ACCESS_TOKEN=your_personal_access_token
ASANA_WORKSPACE_ID=1200000000000000        # optional
ASANA_PROJECT_SHADOWGARDEN=1200000000000000 # optional
```

Tokens are read from the environment only — never commit them.

### Usage

```bash
python3 asana_connector.py --check                          # show config state
python3 asana_connector.py --voice Angela --latency-ms 812 --quality 0.93
python3 asana_connector.py --sync-status ok --messages 42
```

Library:

```python
from asana_connector import AsanaConfig, AsanaConnector
cfg = AsanaConfig.from_env()
if cfg.enabled:
    AsanaConnector(cfg).report_grok_sync("ok", message_count=42)
```

### Safe operation

- Summaries pass through `sanitize_text()`, which redacts API-key/token/password
  assignments, `sk-`/`xai-` keys, emails, and long digit runs, then clamps length.
- No secrets are logged or committed; only `.env.example` placeholders are tracked.

### Tests

```bash
python3 -m unittest tests.test_asana_connector -v
```

All Asana HTTP calls are mocked by default. Live calls run **only** when you opt
in explicitly:

```bash
RUN_LIVE_ASANA_TESTS=1 ASANA_ACCESS_TOKEN=... python3 -m unittest tests.test_asana_connector
```

## Related

- Grok Voice Agent: `~/Movies/Grok-Videos/grok-voice-agent`
- 4.2 Sovereign lattice: `sovereign-lattice-42.mjs` in voice agent dir