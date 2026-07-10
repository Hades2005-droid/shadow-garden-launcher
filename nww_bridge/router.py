"""Minimal mesh router — the planning layer.

Routes an intent to a registered agent, validates the returned AgentResult
against contract v1.0, appends it to a JSONL run log, and follows any handoff
to the next agent. trace_id stays stable across the whole chain; each hop gets
its own run_id.
"""
from __future__ import annotations

import json
from typing import Any, Callable, Optional

from contract import validate, AgentResult

# handler(question, trace_id) -> AgentResult
Handler = Callable[[str, str], AgentResult]


class Router:
    def __init__(self, log_path: Optional[str] = None, max_hops: int = 5):
        self._handlers: dict[str, Handler] = {}
        self.log_path = log_path
        self.max_hops = max_hops

    def register(self, intent: str, handler: Handler) -> None:
        self._handlers[intent] = handler

    def run(self, intent: str, question: str,
            trace_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Execute an intent and follow handoffs. Returns the chain of results."""
        trace_id = trace_id or AgentResult.new_trace_id()
        chain: list[dict[str, Any]] = []
        hops = 0

        while intent and hops < self.max_hops:
            handler = self._handlers.get(intent)
            if handler is None:
                chain.append(self._unroutable(intent, trace_id))
                break

            result = handler(question, trace_id)
            record = result.to_dict()
            ok, errors = validate(record)
            record["_valid"] = ok
            if not ok:
                record["_validation_errors"] = errors
            self._log(record)
            chain.append(record)

            handoff = record.get("handoff")
            if not handoff or record.get("status") != "success":
                break
            intent = handoff.get("intent")
            hops += 1

        return chain

    def _unroutable(self, intent: str, trace_id: str) -> dict[str, Any]:
        rec = AgentResult(
            agent="router", status="blocked",
            summary=f"no handler for intent {intent!r}", trace_id=trace_id,
            error={"class": "not_implemented", "detail": f"intent={intent}"},
        ).to_dict()
        self._log(rec)
        return rec

    def _log(self, record: dict[str, Any]) -> None:
        if not self.log_path:
            return
        with open(self.log_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
