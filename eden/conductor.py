#!/usr/bin/env python3
"""Eden conductor — Perplexity-led Fable 5 + Devin integration.

One goal, one seamless pipeline:

    Perplexity (LEAD)  ->  research the goal + split it into tasks
        |
        +--> Claude Fable 5   : reason, write specs, design, review
        +--> Devin            : long-horizon code execution (returns a session URL)
        |
    Perplexity (LEAD)  ->  synthesize the results into a final briefing

Run it:

    python eden/conductor.py "<your goal>"
    python eden/conductor.py --wait "<goal>"     # block until Devin sessions finish

Providers are wired by environment variable and every one is optional:

    PERPLEXITY_API_KEY  -> Perplexity leads (else Fable 5 leads, else a static plan)
    ANTHROPIC_API_KEY   -> Claude Fable 5 reasoning/review
    DEVIN_API_KEY       -> Devin execution (else specs are emitted as handoff packets)

With no keys at all this still runs end-to-end as a dry run: it prints the plan
and a handoff packet for every task, so you always get a usable output.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))  # so sibling eden modules import as scripts


def log(icon: str, msg: str) -> None:
    # Progress goes to stderr so `--json` keeps stdout machine-clean.
    print(f"  {icon} {msg}", file=sys.stderr)


def _say(msg: str = "") -> None:
    print(msg, file=sys.stderr)


# --------------------------------------------------------------------------- #
# Stage 1 — LEAD: build the plan (Perplexity, else Fable 5, else static)
# --------------------------------------------------------------------------- #
def build_plan(goal: str) -> Dict[str, Any]:
    try:
        import perplexity

        if perplexity.has_credentials():
            log("LEAD", "Perplexity is leading — researching the goal...")
            plan = perplexity.Perplexity().plan(goal)
            log("OK", f"Plan: {plan.get('summary', '')[:120]}")
            return plan
        log("..", "No PERPLEXITY_API_KEY — Perplexity cannot lead this run")
    except Exception as exc:  # import or API failure
        log("XX", f"Perplexity lead unavailable ({exc})")

    # Fallback lead: Claude Fable 5 plans, if it is available.
    try:
        import fable5

        if fable5.has_credentials():
            log("LEAD", "Fable 5 is standing in as lead — drafting the plan...")
            raw = fable5.Fable5().ask(
                "Split this goal into concrete tasks. Assign 'fable5' to reasoning/"
                "spec-writing/design/review and 'devin' to code execution. Return ONLY "
                'JSON: {"summary": str, "tasks": [{"id": str, "assignee": '
                f'"fable5"|"devin", "title": str, "spec": str}}]}}.\n\nGoal: {goal}',
                system="You are the lead orchestrator of the Eden stack. JSON only.",
                max_tokens=2000,
            )
            return _loads(raw)
        log("..", "No ANTHROPIC_API_KEY — Fable 5 cannot lead either")
    except Exception as exc:
        log("XX", f"Fable 5 lead unavailable ({exc})")

    # Last resort: a static two-step plan so the pipeline always has shape.
    log("..", "Dry run — using a static plan (no lead provider reachable)")
    return {
        "summary": f"Static plan for: {goal}",
        "tasks": [
            {"id": "T1", "assignee": "fable5", "title": "Write the spec",
             "spec": f"Turn this goal into a precise, buildable spec: {goal}"},
            {"id": "T2", "assignee": "devin", "title": "Execute the spec",
             "spec": f"Implement the spec produced for: {goal}"},
        ],
    }


# --------------------------------------------------------------------------- #
# Stage 2 — EXECUTE each task on its assignee
# --------------------------------------------------------------------------- #
def run_task(task: Dict[str, Any], *, wait: bool) -> Dict[str, Any]:
    assignee = task.get("assignee", "fable5")
    spec = task.get("spec", "")
    title = task.get("title", task.get("id", "task"))
    result: Dict[str, Any] = {"id": task.get("id"), "assignee": assignee, "title": title}

    if assignee == "devin":
        try:
            import devin

            if devin.has_credentials():
                log("DEVIN", f"Executing: {title}")
                session = devin.Devin().run(spec, title=f"[Eden] {title}", wait=wait)
                result["devin_session"] = session
                result["output"] = session.get("url") or session
                log("OK", f"Devin session: {session.get('url', session)}")
                return result
            log("..", f"No DEVIN_API_KEY — handoff packet for: {title}")
        except Exception as exc:
            log("XX", f"Devin unavailable ({exc}) — handoff packet for: {title}")
        # Degrade: emit a handoff packet the user can paste into Devin later.
        result["handoff"] = {"target": "devin", "prompt": spec}
        result["output"] = f"[handoff->devin] {spec}"
        return result

    # assignee == "fable5"
    try:
        import fable5

        if fable5.has_credentials():
            log("FABLE5", f"Reasoning: {title}")
            out = fable5.Fable5().ask(
                spec, system="You are Claude Fable 5 in the Eden stack. Be precise.",
                max_tokens=4000,
            )
            result["output"] = out
            log("OK", f"Fable 5 produced {len(out)} chars for: {title}")
            return result
        log("..", f"No ANTHROPIC_API_KEY — handoff packet for: {title}")
    except Exception as exc:
        log("XX", f"Fable 5 unavailable ({exc}) — handoff packet for: {title}")
    result["handoff"] = {"target": "fable5", "prompt": spec}
    result["output"] = f"[handoff->fable5] {spec}"
    return result


# --------------------------------------------------------------------------- #
# Stage 3 — SYNTHESIZE (Perplexity leads the wrap-up, else Fable 5, else raw)
# --------------------------------------------------------------------------- #
def synthesize(goal: str, results: List[Dict[str, Any]]) -> str:
    digest = "\n".join(
        f"- [{r['assignee']}] {r['title']}: {str(r.get('output', ''))[:200]}"
        for r in results
    )
    prompt = (
        f"Goal: {goal}\n\nWhat each agent produced:\n{digest}\n\n"
        "Give a 4-line briefing: what is done, what Devin is executing, and the next step."
    )
    try:
        import perplexity

        if perplexity.has_credentials():
            return perplexity.Perplexity().chat(
                [{"role": "user", "content": prompt}], search_recency=None, max_tokens=800
            )
    except Exception as exc:
        log("XX", f"Perplexity synthesis unavailable ({exc})")
    try:
        import fable5

        if fable5.has_credentials():
            return fable5.Fable5().ask(prompt, max_tokens=800)
    except Exception as exc:
        log("XX", f"Fable 5 synthesis unavailable ({exc})")
    return digest  # raw fallback


# --------------------------------------------------------------------------- #
def conduct(goal: str, *, wait: bool = False) -> Dict[str, Any]:
    _say(f"\n[EDEN CONDUCTOR] goal: {goal!r}\n")
    plan = build_plan(goal)
    tasks = plan.get("tasks", [])
    log("PLAN", f"{len(tasks)} task(s): " + ", ".join(
        f"{t.get('id')}->{t.get('assignee')}" for t in tasks))

    results = [run_task(t, wait=wait) for t in tasks]

    _say()
    briefing = synthesize(goal, results)
    log("SYNTH", "Final briefing:")
    for line in str(briefing).strip().splitlines():
        _say(f"        {line}")
    _say("\n  Eden conductor complete.\n")
    return {"goal": goal, "plan": plan, "results": results, "briefing": briefing}


def _loads(text: str) -> Dict[str, Any]:
    import re
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            return json.loads(m.group(0))
        raise


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Perplexity-led Fable 5 + Devin conductor for the Shadow Garden."
    )
    parser.add_argument("--wait", action="store_true", help="Block until Devin sessions finish.")
    parser.add_argument("--json", action="store_true", help="Print the full result as JSON.")
    parser.add_argument("goal", nargs="*", help="Your one goal.")
    args = parser.parse_args(argv)
    goal = " ".join(args.goal).strip() or "bootstrap the Shadow Garden"

    out = conduct(goal, wait=args.wait)
    if args.json:
        print(json.dumps(out, indent=2, default=str))


if __name__ == "__main__":
    main()
