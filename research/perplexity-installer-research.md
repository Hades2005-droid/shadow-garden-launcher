# Perplexity Research (bundled)

**Topic:** Safe curl-to-bash installer for Shadow Garden Launcher v4.3  
**Source:** Perplexity-style synthesis (web-grounded, pre-install bundle)  
**For:** 4.2 Sovereign / Shadow Garden

---

## Installer best practices

1. **Idempotency** — Re-running install must be safe. Use `git pull --ff-only` for updates, `mkdir -p` for dirs, and grep-before-append for shell aliases.
2. **No secrets in repo** — Never embed API keys in `install.sh`. Load from `~/ShadowGarden/.env`, `~/Movies/Grok-Videos/.env`, or macOS Keychain.
3. **Explicit target dir** — Default `~/ShadowGarden`, overridable via `SHADOW_GARDEN_DIR`.
4. **Fail fast** — `set -euo pipefail`; require `git` with a clear Xcode CLT message.
5. **curl | bash hygiene** — Pin to a known GitHub owner/repo; allow override via `SHADOW_GARDEN_REPO_OWNER` for forks (e.g. `fredwashere`).

## Post-install checklist

- [ ] `source ~/.zshrc` — load `sg`, `sg-bridge`, `sg-voice`
- [ ] Add `XAI_API_KEY` to env (rotate if ever pasted in chat)
- [ ] Optional: `PERPLEXITY_API_KEY` for live Sonar research hook
- [ ] Run `sg` after copying a Grok chat to clipboard
- [ ] Run `sg-voice` for Grok WAV synthesis (requires `grok-voice-agent`)

## Perplexity integration

- Set `PERPLEXITY_API_KEY` from [console.perplexity.ai](https://console.perplexity.ai)
- Install with research pass: `curl -fsSL .../install.sh | bash -s -- --perplexity`
- Or anytime: `python3 ~/ShadowGarden/scripts/perplexity_research.py "topic"`

## Recommended aliases

| Alias | Action |
|-------|--------|
| `sg` | Clipboard save + voice prompt log |
| `sg-bridge` | Prompt log only |
| `sg-voice` | Save + Grok synthesis |

---

*Live Sonar queries overwrite/append new dated files in `~/ShadowGarden/research/` when `PERPLEXITY_API_KEY` is set.*