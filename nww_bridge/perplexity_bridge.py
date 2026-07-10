"""Local Perplexity bridge — a mesh agent that runs research via the Sonar API.

Design rules (consistent with the NWW hardening spec):
  * Secret ONLY from env (PERPLEXITY_API_KEY). Never hardcoded, never logged,
    never serialized into an AgentResult.
  * Mock-by-default: with no key present the bridge returns a deterministic
    mock AgentResult and makes ZERO network calls. Safe for CI.
  * Live mode engages only when a key is present AND allow_live is not disabled.
  * Transport is injectable so tests never touch the network.
  * Every call returns a contract v1.0 AgentResult; failures map to the frozen
    error.class enum with status "blocked".
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Callable, Optional

from contract import AgentResult, now_rfc3339, INTENTS

SONAR_URL = "https://api.perplexity.ai/chat/completions"
DEFAULT_MODEL = "sonar"

# transport(url, headers, body_bytes, timeout) -> (status_code, response_dict)
Transport = Callable[[str, dict[str, str], bytes, float], "tuple[int, dict[str, Any]]"]


def _urllib_transport(url: str, headers: dict[str, str], body: bytes,
                      timeout: float) -> "tuple[int, dict[str, Any]]":
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_txt = e.read().decode("utf-8", "replace")
        try:
            payload = json.loads(body_txt)
        except ValueError:
            payload = {"raw": body_txt}
        return e.code, payload


class PerplexityBridge:
    AGENT = "perplexity"

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL,
                 transport: Optional[Transport] = None, timeout: float = 30.0,
                 allow_live: bool = True):
        self._api_key = api_key if api_key is not None else os.environ.get("PERPLEXITY_API_KEY")
        self.model = model
        self.timeout = timeout
        self._transport = transport or _urllib_transport
        # Mock unless we have a key and live is allowed.
        self.mock_mode = not (self._api_key and allow_live)

    # -- public API --------------------------------------------------------

    def research(self, question: str, trace_id: Optional[str] = None,
                 intent: str = "web_research",
                 handoff_to: Optional[str] = None,
                 handoff_intent: Optional[str] = None) -> AgentResult:
        trace_id = trace_id or AgentResult.new_trace_id()
        ts_start = now_rfc3339()

        if not question or not question.strip():
            return self._blocked(trace_id, ts_start,
                                 "invalid_input", "empty research question")

        if self.mock_mode:
            return self._mock_result(question, trace_id, ts_start,
                                     handoff_to, handoff_intent)

        return self._live_research(question, trace_id, ts_start, intent,
                                   handoff_to, handoff_intent)

    # -- internals ---------------------------------------------------------

    def _mock_result(self, question: str, trace_id: str, ts_start: str,
                     handoff_to, handoff_intent) -> AgentResult:
        return AgentResult(
            agent=self.AGENT,
            status="success",
            summary=f"[mock] research on: {question[:80]}",
            trace_id=trace_id,
            ts_start=ts_start,
            ts_end=now_rfc3339(),
            output={
                "mode": "mock",
                "model": self.model,
                "answer": f"MOCK ANSWER for {question!r} — no live Perplexity call made.",
                "citations": [],
            },
            handoff=self._make_handoff(handoff_to, handoff_intent),
        )

    def _live_research(self, question, trace_id, ts_start, intent,
                       handoff_to, handoff_intent) -> AgentResult:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": question}],
        }).encode("utf-8")

        try:
            code, payload = self._transport(SONAR_URL, headers, body, self.timeout)
        except (TimeoutError,) as e:
            return self._blocked(trace_id, ts_start, "timeout", str(e))
        except (urllib.error.URLError, OSError) as e:
            return self._blocked(trace_id, ts_start, "network_error", str(e))
        except Exception as e:  # noqa: BLE001 — last-resort classification
            return self._blocked(trace_id, ts_start, "internal_error", repr(e))

        if code == 401 or code == 403:
            return self._blocked(trace_id, ts_start, "auth_error", f"HTTP {code}")
        if code == 429:
            return self._blocked(trace_id, ts_start, "rate_limited", "HTTP 429")
        if code >= 500:
            return self._blocked(trace_id, ts_start, "upstream_error", f"HTTP {code}")
        if code >= 400:
            return self._blocked(trace_id, ts_start, "invalid_input", f"HTTP {code}")

        try:
            answer = payload["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError):
            return self._blocked(trace_id, ts_start, "contract_mismatch",
                                 "unexpected Sonar response shape")

        citations = payload.get("citations") or payload.get("search_results") or []
        return AgentResult(
            agent=self.AGENT,
            status="success",
            summary=f"research on: {question[:80]}",
            trace_id=trace_id,
            ts_start=ts_start,
            ts_end=now_rfc3339(),
            output={
                "mode": "live",
                "model": self.model,
                "answer": answer,
                "citations": citations,
            },
            handoff=self._make_handoff(handoff_to, handoff_intent),
        )

    def _blocked(self, trace_id, ts_start, error_class, detail) -> AgentResult:
        return AgentResult(
            agent=self.AGENT,
            status="blocked",
            summary=f"perplexity research blocked ({error_class})",
            trace_id=trace_id,
            ts_start=ts_start,
            ts_end=now_rfc3339(),
            output={},
            error={"class": error_class, "detail": self._redact(detail)},
        )

    def _make_handoff(self, to, intent) -> Optional[dict[str, Any]]:
        if not to:
            return None
        if intent not in INTENTS:
            intent = "plan_fallback"
        return {"to": to, "intent": intent, "payload": {}}

    def _redact(self, text: str) -> str:
        """Never let the key leak into a serialized error detail."""
        if self._api_key:
            return str(text).replace(self._api_key, "***REDACTED***")
        return str(text)
