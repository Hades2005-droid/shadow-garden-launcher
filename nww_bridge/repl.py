#!/usr/bin/env python3
"""Interactive terminal REPL for the NWW Perplexity bridge.

  python3 repl.py                 # mock mode (no key)
  PERPLEXITY_API_KEY=... python3 repl.py --model sonar-pro

Type a question and press enter. Meta-commands start with ':':
  :model <name>   switch Sonar model (sonar | sonar-pro | sonar-reasoning)
  :trace          show the current trace_id (stable across the session)
  :new            start a fresh trace_id
  :log <path>     append results to a JSONL run log (mesh format)
  :mode           show mock/live status
  :help           this help
  :quit / :q      exit
"""
from __future__ import annotations

import argparse
import os
import sys
import textwrap

from perplexity_bridge import PerplexityBridge
from contract import AgentResult
from router import Router

BOLD, DIM, GREEN, RED, YELLOW, RESET = (
    "\033[1m", "\033[2m", "\033[32m", "\033[31m", "\033[33m", "\033[0m")


def _c(code: str, text: str) -> str:
    return text if not sys.stdout.isatty() else f"{code}{text}{RESET}"


def render(result: AgentResult) -> str:
    r = result.to_dict()
    lines = []
    if r["status"] == "success":
        head = _c(GREEN, f"● {r['agent']} · success · {r['output'].get('mode','?')}")
        lines.append(head)
        answer = r["output"].get("answer", "")
        lines.append(textwrap.fill(answer, width=88))
        cites = r["output"].get("citations") or []
        if cites:
            lines.append(_c(DIM, "citations:"))
            for i, c in enumerate(cites, 1):
                lines.append(_c(DIM, f"  [{i}] {c}"))
    else:
        lines.append(_c(RED, f"● {r['agent']} · {r['status']} · "
                            f"{r.get('error',{}).get('class','?')}"))
        lines.append(_c(DIM, r.get("error", {}).get("detail", "")))
    lines.append(_c(DIM, f"trace={r['trace_id'][:8]} run={r['run_id'][:8]}"))
    return "\n".join(lines)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="NWW Perplexity terminal REPL")
    p.add_argument("--model", default="sonar")
    p.add_argument("--log", default=None, help="JSONL run log path")
    args = p.parse_args(argv)

    bridge = PerplexityBridge(model=args.model)
    router = Router(log_path=args.log)
    router.register("web_research",
                    lambda q, tid: bridge.research(q, trace_id=tid))
    trace_id = AgentResult.new_trace_id()

    mode = "mock" if bridge.mock_mode else _c(GREEN, "LIVE")
    print(_c(BOLD, "NWW Perplexity bridge") + f" — {mode} — model={bridge.model}")
    if bridge.mock_mode:
        print(_c(YELLOW, "  (mock mode — set PERPLEXITY_API_KEY for live research)"))
    print(_c(DIM, "  :help for commands, :quit to exit"))

    while True:
        try:
            line = input(_c(BOLD, "\nnww› ")).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue

        if line.startswith(":"):
            cmd, _, arg = line[1:].partition(" ")
            cmd, arg = cmd.strip(), arg.strip()
            if cmd in ("quit", "q"):
                break
            elif cmd == "help":
                print(textwrap.dedent(__doc__))
            elif cmd == "model" and arg:
                bridge.model = arg
                print(_c(DIM, f"model → {arg}"))
            elif cmd == "trace":
                print(_c(DIM, f"trace_id = {trace_id}"))
            elif cmd == "new":
                trace_id = AgentResult.new_trace_id()
                print(_c(DIM, f"new trace_id = {trace_id[:8]}…"))
            elif cmd == "log" and arg:
                router.log_path = arg
                print(_c(DIM, f"logging to {arg}"))
            elif cmd == "mode":
                print(_c(DIM, "mock" if bridge.mock_mode else "live"))
            else:
                print(_c(RED, f"unknown command :{cmd} (try :help)"))
            continue

        chain = router.run("web_research", line, trace_id=trace_id)
        # reconstruct AgentResult-ish for rendering from the logged dict
        for rec in chain:
            fake = AgentResult(agent=rec["agent"], status=rec["status"],
                               summary=rec["summary"], trace_id=rec["trace_id"],
                               run_id=rec["run_id"],
                               output=rec.get("output", {}),
                               error=rec.get("error"))
            print(render(fake))

    print(_c(DIM, "bye."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
