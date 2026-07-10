#!/usr/bin/env python3
"""CLI for the Perplexity bridge.

  python cli.py "What changed in the Asana API in 2025?"
  python cli.py --model sonar-pro "..."      # pick a Sonar model
  PERPLEXITY_API_KEY=... python cli.py "..."  # live mode

With no key set it runs in mock mode and makes no network call.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from perplexity_bridge import PerplexityBridge


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="NWW Perplexity bridge")
    p.add_argument("question", help="research question")
    p.add_argument("--model", default="sonar", help="Sonar model (default: sonar)")
    p.add_argument("--trace-id", default=None, help="reuse a trace_id across a chain")
    p.add_argument("--handoff-to", default=None, help="next agent to hand off to")
    p.add_argument("--handoff-intent", default="code_review", help="handoff intent")
    args = p.parse_args(argv)

    bridge = PerplexityBridge(model=args.model)
    result = bridge.research(
        args.question, trace_id=args.trace_id,
        handoff_to=args.handoff_to, handoff_intent=args.handoff_intent,
    )
    print(json.dumps(result.to_dict(), indent=2))

    if bridge.mock_mode:
        print("\n[mock mode — set PERPLEXITY_API_KEY for live research]",
              file=sys.stderr)
    return 0 if result.status == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
