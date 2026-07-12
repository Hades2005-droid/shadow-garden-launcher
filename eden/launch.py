#!/usr/bin/env python3
"""Eden launcher — one input, launches everywhere into the Shadow Garden.

    python eden/launch.py "<your one command>"

One input does three things:

  1. Opens the EDEN burst-alpha physics artifact (``eden/index.html``) in a
     browser. This is the catalyst — a self-contained, data-everywhere physics
     field with an auto-recursive burst loop.

  2. Dispatches the same input to sibling Eden repos, if they are cloned next to
     this one:
        ../wha-spell-simulator  ->  node   eden/eden_spell.mjs "<input>"
        ../gitmynotes           ->  python eden/eden_notes.py  "<input>"

  3. Asks Claude Fable 5 for a short launch briefing (if an API key is set).

Everything degrades gracefully. A missing sibling repo, a missing Node runtime,
or an unset API key is reported and skipped — the launch still fires.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent          # .../shadow-garden-launcher/eden
REPO_ROOT = HERE.parent                          # .../shadow-garden-launcher
CONSTELLATION = REPO_ROOT.parent                 # dir holding the sibling repos
ARTIFACT = HERE / "index.html"

sys.path.insert(0, str(HERE))  # so `import fable5` works when run as a script

# name -> command run inside that sibling repo (the one input is appended)
SIBLINGS = [
    ("wha-spell-simulator", ["node", "eden/eden_spell.mjs"]),
    ("gitmynotes", [sys.executable, "eden/eden_notes.py"]),
]


def log(icon: str, msg: str) -> None:
    print(f"  {icon} {msg}")


def open_artifact() -> None:
    if ARTIFACT.exists():
        webbrowser.open(ARTIFACT.as_uri())
        log("✔", f"Opened the Eden physics field  →  {ARTIFACT}")
    else:
        log("✖", f"Artifact not found at {ARTIFACT}")


def dispatch_siblings(one_input: str) -> None:
    for name, cmd in SIBLINGS:
        repo = CONSTELLATION / name
        if not repo.exists():
            log("·", f"{name} not cloned next door — skipping")
            continue
        try:
            subprocess.Popen(cmd + [one_input], cwd=repo)
            log("✔", f'Ignited {name}:  {" ".join(cmd)} "{one_input}"')
        except FileNotFoundError:
            log("✖", f"{name}: runtime '{cmd[0]}' not found — skipping")
        except Exception as exc:  # pragma: no cover - defensive
            log("✖", f"{name}: {exc}")


def brief_with_fable(one_input: str) -> None:
    try:
        from fable5 import Fable5, Fable5Refused, has_credentials
    except Exception as exc:  # pragma: no cover - optional dependency
        log("·", f"Fable 5 client unavailable ({exc}) — skipping briefing")
        return
    if not has_credentials():
        log("·", "No ANTHROPIC_API_KEY set — skipping Fable 5 briefing")
        return
    try:
        briefing = Fable5().ask(
            "You are the operations mind of Shadow Garden in Eden. Turn this single "
            f"launch command into a 4-line briefing: {one_input!r}",
            system="Be terse, vivid, and practical. No preamble, no numbering.",
            max_tokens=400,
        )
        log("✔", "Fable 5 launch briefing:")
        for line in briefing.strip().splitlines():
            print(f"        {line}")
    except Fable5Refused as exc:
        log("·", str(exc))
    except Exception as exc:  # pragma: no cover - network/runtime
        log("✖", f"Fable 5 briefing failed: {exc}")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="One input, launches everywhere into the Shadow Garden."
    )
    parser.add_argument(
        "input", nargs="*", help="Your single launch command / intent."
    )
    args = parser.parse_args(argv)
    one_input = " ".join(args.input).strip() or "ignite"

    print(f"\n🌑⚡  EDEN LAUNCH — one input: {one_input!r}\n")
    open_artifact()
    dispatch_siblings(one_input)
    brief_with_fable(one_input)
    print("\n  Shadow Garden is live.\n")


if __name__ == "__main__":
    main()
