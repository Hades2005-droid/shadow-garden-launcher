"""Perplexity Sonar client — the LEAD / orchestrator brain of the Eden conductor.

Perplexity runs the show: given a goal it researches the web and returns a
structured plan that splits the work between Claude Fable 5 (reasoning, authoring,
review) and Devin (long-horizon code execution).

Zero extra dependencies — uses the stdlib so it runs on a fresh machine.
Auth: set ``PERPLEXITY_API_KEY``.  Endpoint per docs.perplexity.ai (July 2026):
``POST https://api.perplexity.ai/v1/sonar``.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

PERPLEXITY_BASE = os.getenv("PERPLEXITY_BASE_URL", "https://api.perplexity.ai")
PERPLEXITY_ENDPOINT = os.getenv("PERPLEXITY_ENDPOINT", "/v1/sonar")
LEAD_MODEL = os.getenv("PERPLEXITY_MODEL", "sonar-reasoning-pro")


class PerplexityError(RuntimeError):
    """Raised when the Perplexity API call fails."""


def has_credentials() -> bool:
    return bool(os.getenv("PERPLEXITY_API_KEY"))


# The plan Perplexity hands back to the conductor.
_PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "tasks"],
    "properties": {
        "summary": {"type": "string"},
        "research": {"type": "array", "items": {"type": "string"}},
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["id", "assignee", "title", "spec"],
                "properties": {
                    "id": {"type": "string"},
                    "assignee": {"type": "string", "enum": ["fable5", "devin"]},
                    "title": {"type": "string"},
                    "spec": {"type": "string"},
                },
            },
        },
    },
}


class Perplexity:
    """Thin stdlib client for the Perplexity Sonar API."""

    def __init__(self, api_key: Optional[str] = None, model: str = LEAD_MODEL) -> None:
        self.api_key = api_key or os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key:
            raise PerplexityError("PERPLEXITY_API_KEY is not set.")
        self.model = model

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        response_format: Optional[Dict[str, Any]] = None,
        search_recency: Optional[str] = "month",
        max_tokens: int = 4000,
        timeout: int = 120,
    ) -> str:
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
        }
        if search_recency:
            body["search_recency_filter"] = search_recency
        if response_format:
            body["response_format"] = response_format

        req = urllib.request.Request(
            PERPLEXITY_BASE + PERPLEXITY_ENDPOINT,
            data=json.dumps(body).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise PerplexityError(f"Perplexity HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise PerplexityError(f"Perplexity connection error: {exc.reason}") from exc

        return payload["choices"][0]["message"]["content"]

    def plan(self, goal: str) -> Dict[str, Any]:
        """Lead the run: research ``goal`` and return a structured plan dict."""
        system = (
            "You are the LEAD orchestrator of the Shadow Garden / Eden agent stack. "
            "Research the goal on the web, then split the work into concrete tasks. "
            "Assign 'fable5' (Claude Fable 5) to reasoning, spec-writing, design, and "
            "review; assign 'devin' to long-horizon code execution. Keep specs precise "
            "and self-contained. Return ONLY JSON matching the schema."
        )
        raw = self.chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": f"Goal: {goal}"},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {"schema": _PLAN_SCHEMA},
            },
        )
        return _extract_json(raw)


def _extract_json(text: str) -> Dict[str, Any]:
    """Parse a JSON object out of a model reply (reasoning models may prepend text)."""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise PerplexityError(f"Could not parse plan JSON: {exc}") from exc
    raise PerplexityError("Perplexity returned no JSON plan.")
