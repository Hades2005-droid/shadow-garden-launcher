#!/usr/bin/env python3
"""
Devin Gift Taker — bridge readiness observer + gift acceptance contract.

Watches the primordial_bridge module for readiness, then accepts the gift
package and returns a normalized acceptance record.

Controls (all false — inert observer, no side-effects):
  external_fetch:           false
  generated_code_execution: false
  credentials_allowed:      false
"""
from __future__ import annotations

import sys
import os
from typing import Any

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from primordial_bridge import SIGNATURE, bridge, verify_signature


GIFT_CONTRACT_VERSION = "v1.0"

READY_STATES = frozenset({"bridge_ready", "gift_accepted", "gift_returned"})


class BridgeReadinessObserver:
    """Lightweight observer: checks bridge signature and readiness once."""

    def __init__(self) -> None:
        self.state: str = "uninspected"
        self.last_signature: str | None = None

    def inspect(self) -> bool:
        """Return True if bridge is ready (signature valid). Updates state."""
        ready = verify_signature()
        self.last_signature = SIGNATURE if ready else None
        self.state = "bridge_ready" if ready else "bridge_fault"
        return ready


class GiftTaker:
    """Accept a Morse gift, pass through bridge, return normalized acceptance."""

    def __init__(self) -> None:
        self.observer = BridgeReadinessObserver()
        self.state: str = "idle"

    def take(self, morse_gift: str) -> dict[str, Any]:
        """
        Accept a Morse gift string and return a normalized acceptance record.

        Args:
            morse_gift: ITU Morse string, max 4096 chars.

        Returns dict with: contract_version, bridge_signature, accepted,
                           gift_report (full bridge output).

        Raises RuntimeError if bridge is not ready.
        Raises ValueError if bridge rejects the input.
        """
        if not self.observer.inspect():
            raise RuntimeError(f"bridge not ready: state={self.observer.state!r}")

        self.state = "accepting"
        gift_report = bridge(morse_gift)
        self.state = "gift_accepted"

        return {
            "contract_version": GIFT_CONTRACT_VERSION,
            "bridge_signature": gift_report["signature"],
            "accepted": True,
            "state": self.state,
            "gift_report": gift_report,
        }
