"""NWW mesh contract v1.0 — the shared AgentResult envelope.

Frozen for v1.0. Breaking changes go to v2.0, never mutate these enums in place.
Every agent in the mesh (perplexity, claude, cursor, router, ...) returns an
AgentResult so a step can be handed off deterministically to the next agent.
"""
from __future__ import annotations

import calendar
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional
import uuid

CONTRACT_VERSION = "1.0"

# --- Frozen enums (v1.0) --------------------------------------------------

# A run ends in exactly one of these three states.
STATUS = frozenset({"success", "blocked", "needs_input"})

# error.class — the 9 frozen failure categories. `error` is present ONLY when
# status != "success".
ERROR_CLASSES = frozenset({
    "auth_error",        # bad/missing credentials
    "rate_limited",      # 429 / quota
    "network_error",     # connection reset, DNS, TLS
    "timeout",           # deadline exceeded
    "invalid_input",     # caller sent something malformed
    "contract_mismatch", # payload violated this contract
    "upstream_error",    # backend 5xx / provider fault
    "not_implemented",   # seam not wired yet
    "internal_error",    # anything else, unclassified
})

# Intent vocabulary — union across the mesh (bridge:* + media + user agents).
INTENTS = frozenset({
    "web_research",
    "fact_check",
    "code_review",
    "architecture_review",
    "implement_fix",
    "plan_fallback",
    "needs_input",
    "bridge:perplexity",
    "elevenlabs",
    "grok-imagine",
})


def now_rfc3339() -> str:
    """UTC RFC3339 timestamp with trailing Z (never local time)."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_rfc3339(ts: str) -> float:
    """Parse an RFC3339 'Z' timestamp to epoch seconds, UTC-safe.

    Uses calendar.timegm (treats the struct as UTC) rather than time.mktime
    (which assumes local time and causes heartbeat-stale false positives).
    """
    struct = time.strptime(ts.replace("Z", "GMT"), "%Y-%m-%dT%H:%M:%S%Z")
    return calendar.timegm(struct)


@dataclass
class AgentResult:
    agent: str
    status: str
    summary: str
    trace_id: str
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    contract_version: str = CONTRACT_VERSION
    ts_start: str = field(default_factory=now_rfc3339)
    ts_end: str = field(default_factory=now_rfc3339)
    output: dict[str, Any] = field(default_factory=dict)
    error: Optional[dict[str, Any]] = None
    handoff: Optional[dict[str, Any]] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # Conditional field: drop error entirely on success.
        if self.status == "success":
            d.pop("error", None)
        if self.handoff is None:
            d.pop("handoff", None)
        return d

    @classmethod
    def new_trace_id(cls) -> str:
        return uuid.uuid4().hex


def validate(result: dict[str, Any]) -> tuple[bool, list[str]]:
    """Validate a result dict against contract v1.0. Returns (ok, errors)."""
    errors: list[str] = []
    required = ("contract_version", "agent", "run_id", "trace_id",
                "status", "summary", "ts_start", "ts_end")
    for key in required:
        if not result.get(key):
            errors.append(f"missing required field: {key}")

    if result.get("contract_version") not in (None, CONTRACT_VERSION):
        errors.append(f"unsupported contract_version: {result.get('contract_version')}")

    status = result.get("status")
    if status is not None and status not in STATUS:
        errors.append(f"bad status enum: {status!r}")

    # Conditional error logic.
    err = result.get("error")
    if status == "success" and err:
        errors.append("error must be absent when status == success")
    if status in ("blocked", "needs_input") and not err:
        errors.append(f"error required when status == {status}")
    if err is not None:
        cls = err.get("class")
        if cls not in ERROR_CLASSES:
            errors.append(f"bad error.class enum: {cls!r}")

    handoff = result.get("handoff")
    if handoff is not None:
        intent = handoff.get("intent")
        if intent not in INTENTS:
            errors.append(f"bad handoff.intent: {intent!r}")

    return (len(errors) == 0, errors)


def classify_health(last_ts: Optional[str], now: Optional[str] = None,
                    stale_after_s: int = 120) -> str:
    """Health from heartbeat freshness: 'up' | 'degraded' | 'down'."""
    if not last_ts:
        return "down"
    now_s = parse_rfc3339(now) if now else parse_rfc3339(now_rfc3339())
    try:
        age = now_s - parse_rfc3339(last_ts)
    except (ValueError, KeyError):
        return "down"
    if age < 0:
        return "up"
    if age <= stale_after_s:
        return "up"
    if age <= stale_after_s * 3:
        return "degraded"
    return "down"
