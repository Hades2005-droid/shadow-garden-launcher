#!/usr/bin/env python3
"""
Shadow Garden — Unified Alpha Timeline Game (deterministic, offline, stdlib-only)

Design language note: "alpha timeline," "reverse polarity," "Swiss Bridge," and
similar terms are fictional flavor text for a local state-machine game, not
factual claims about real models, providers, or events. "Swiss Bridge" and the
launch/hold/correct/land action names are abstract gameplay states — this module
provides no real-world navigation or flight instruction of any kind.

Guarantees:
  - No network access, no subprocess, no filesystem writes outside what the
    caller explicitly requests.
  - Fully deterministic: same seed + mastery_input + action sequence always
    produces byte-identical JSON (after key-sorted serialization).
  - Every run terminates in exactly one of two terminal states: "complete" or
    "aborted" (explicit abort, illegal transition, or turn-limit exhaustion).
  - Full event history is inspectable via report()["events"].
  - Generated/returned JSON is data only — this module never executes code
    that arrives at runtime.

CLI:
    python3 shadowgarden_unified_game.py
    python3 shadowgarden_unified_game.py --seed 7 --mastery 6 --actions launch hold land
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from typing import Any

MAX_TURNS = 24

# state -> {action: next_state}. Any action not listed for the current state,
# or the literal action "abort", forces a transition to "aborted".
#
# Final catalyst arc (fictional, symbolic gameplay only):
#   launch -> emperor_4 -> fable_5 -> harmony_6 -> chariot_7 -> complete
# These names are game-design metadata for a local state machine — they are
# NOT references to real model providers, real people, or real navigation.
TRANSITION_TABLE: dict[str, dict[str, str]] = {
    "launch":    {"launch": "hold", "hold": "hold", "correct": "correct",
                  "emperor": "emperor_4"},
    "hold":      {"hold": "hold", "correct": "correct", "land": "complete",
                  "emperor": "emperor_4"},
    "correct":   {"hold": "hold", "correct": "correct", "land": "complete",
                  "emperor": "emperor_4"},
    "emperor_4": {"fable": "fable_5", "hold": "emperor_4", "land": "complete"},
    "fable_5":   {"harmony": "harmony_6", "hold": "fable_5", "land": "complete"},
    "harmony_6": {"chariot": "chariot_7", "hold": "harmony_6", "land": "complete"},
    "chariot_7": {"land": "complete", "hold": "chariot_7"},
}
TERMINAL_STATES = frozenset({"complete", "aborted"})
DEFAULT_ACTIONS = ["launch", "hold", "correct", "hold", "land"]
CATALYST_ARC = ["launch", "emperor", "fable", "harmony", "chariot", "land"]


@dataclass
class Event:
    turn: int
    action: str
    from_state: str
    to_state: str
    resonance: float
    note: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn": self.turn,
            "action": self.action,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "resonance": round(self.resonance, 4),
            "note": self.note,
        }


@dataclass
class GameConfig:
    seed: int = 42
    mastery_input: int = 10  # capped 0..10 symbolic gameplay value

    def __post_init__(self) -> None:
        self.mastery_input = max(0, min(10, self.mastery_input))


class ShadowGardenUnifiedGame:
    """Deterministic local state machine: launch -> hold/correct (any order,
    any count) -> land -> complete. 'abort' or an illegal action at any point
    -> aborted. Exhausting MAX_TURNS without reaching a terminal state also
    aborts (safe-abort by construction; no infinite games)."""

    def __init__(self, config: GameConfig | None = None):
        self.config = config or GameConfig()
        self.state = "launch"
        self.turn = 0
        self.resonance = float(self.config.mastery_input)
        self.events: list[Event] = []
        self.terminal = False

    def _deterministic_noise(self, action: str) -> float:
        """Pure function of (seed, turn, action) — no randomness module, no
        wall-clock, no external entropy. Same inputs -> same output, always."""
        h = 0
        for ch in f"{self.config.seed}:{self.turn}:{action}":
            h = (h * 131 + ord(ch)) & 0xFFFFFFFF
        return (h % 1000) / 1000.0

    def step(self, action: str) -> Event:
        if self.terminal:
            raise RuntimeError(f"game already terminal at state={self.state!r}")
        if self.turn >= MAX_TURNS:
            return self._abort("turn limit reached")

        self.turn += 1
        from_state = self.state

        if action == "abort":
            return self._abort("manual abort")

        to_state = TRANSITION_TABLE.get(from_state, {}).get(action, "aborted")

        noise = self._deterministic_noise(action)
        delta = (noise - 0.5) * 2.0 + (0.5 if to_state == "correct" else 0.0)
        self.resonance = max(0.0, min(42.0, self.resonance + delta))
        self.state = to_state

        note = ("illegal transition" if to_state == "aborted" and action not in ("abort",)
                else f"{from_state} -> {to_state} via '{action}'")
        event = Event(self.turn, action, from_state, to_state, self.resonance, note)
        self.events.append(event)

        if to_state in TERMINAL_STATES:
            self.terminal = True
        return event

    def _abort(self, reason: str) -> Event:
        from_state = self.state
        event = Event(self.turn, "abort", from_state, "aborted", self.resonance, reason)
        self.events.append(event)
        self.state = "aborted"
        self.terminal = True
        return event

    def run(self, actions: list[str]) -> dict[str, Any]:
        for action in actions:
            if self.terminal:
                break
            self.step(action)
        if not self.terminal:
            self._abort("action sequence exhausted without reaching a terminal state")
        return self.report()

    def report(self) -> dict[str, Any]:
        return {
            "schema": "shadow_garden.unified_game_report.v1",
            "seed": self.config.seed,
            "mastery_input": self.config.mastery_input,
            "final_state": self.state,
            "turns_used": self.turn,
            "final_resonance": round(self.resonance, 4),
            "status": "complete" if self.state == "complete" else "aborted",
            "events": [e.to_dict() for e in self.events],
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Shadow Garden unified alpha-timeline game (deterministic, offline, stdlib-only)")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mastery", type=int, default=10)
    parser.add_argument("--actions", nargs="*", default=DEFAULT_ACTIONS)
    args = parser.parse_args(argv)

    game = ShadowGardenUnifiedGame(GameConfig(seed=args.seed, mastery_input=args.mastery))
    report = game.run(list(args.actions))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
