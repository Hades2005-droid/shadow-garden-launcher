#!/usr/bin/env python3
"""
Perplexity Sonar hook for Shadow Garden Launcher.

Requires PERPLEXITY_API_KEY in env or ~/ShadowGarden/.env

Usage:
  python3 scripts/perplexity_research.py "your research topic"
  python3 scripts/perplexity_research.py   # default installer checklist topic
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(os.environ.get("SHADOW_GARDEN_DIR", Path.home() / "ShadowGarden"))
RESEARCH_DIR = BASE_DIR / "research"
ENV_FILE = BASE_DIR / ".env"

DEFAULT_TOPIC = (
    "Shadow Garden launcher v4.3 post-install checklist for macOS: "
    "safe curl-to-bash installer idempotency, zsh alias patterns, "
    "xAI Grok voice agent env loading, and Perplexity research integration. "
    "Practical steps only, under 600 words."
)


def load_dotenv() -> None:
    if not ENV_FILE.is_file():
        return
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text).strip("_").lower()
    return cleaned[:80] or "research"


def query_sonar(topic: str, api_key: str) -> str:
    payload = json.dumps(
        {
            "model": "sonar-pro",
            "messages": [{"role": "user", "content": topic}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://api.perplexity.ai/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def save_research(topic: str, content: str, source: str) -> Path:
    RESEARCH_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    path = RESEARCH_DIR / f"perplexity_{slugify(topic)}_{stamp}.md"
    path.write_text(
        f"# Perplexity Research\n\n"
        f"**Topic:** {topic}\n"
        f"**Source:** {source}\n"
        f"**Captured:** {datetime.now(timezone.utc).isoformat()}\n\n"
        f"---\n\n{content}\n",
        encoding="utf-8",
    )
    return path


def main() -> int:
    load_dotenv()
    topic = " ".join(sys.argv[1:]).strip() or DEFAULT_TOPIC
    api_key = os.environ.get("PERPLEXITY_API_KEY", "").strip()

    if not api_key:
        fallback = BASE_DIR / "research" / "perplexity-installer-research.md"
        print("No PERPLEXITY_API_KEY — skipping live Sonar query.")
        if fallback.is_file():
            print(f"Using bundled research: {fallback}")
        else:
            print("Add PERPLEXITY_API_KEY to ~/ShadowGarden/.env and re-run with --perplexity")
        return 0

    try:
        content = query_sonar(topic, api_key)
    except urllib.error.HTTPError as exc:
        print(f"Perplexity API error: {exc.code} {exc.reason}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Perplexity network error: {exc.reason}", file=sys.stderr)
        return 1

    path = save_research(topic, content, source="perplexity_sonar_pro")
    print(f"✓ Perplexity research saved: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())