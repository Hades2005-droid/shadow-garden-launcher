"""Devin API client — the EXECUTION arm of the Eden conductor.

Devin runs long-horizon coding tasks the lead (Perplexity) hands off. This is a
zero-dependency stdlib client for Devin's v1 session API.

Auth: set ``DEVIN_API_KEY`` (a ``apk_...`` key).  Endpoints (docs.devin.ai):
  * POST /v1/sessions              -> create a session   {prompt} -> {session_id, url}
  * GET  /v1/session/{id}          -> session status + structured_output
  * POST /v1/session/{id}/message  -> send a follow-up   {message}
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

DEVIN_BASE = os.getenv("DEVIN_BASE_URL", "https://api.devin.ai/v1")

# Session statuses Devin reports as finished (no more work will happen).
_TERMINAL = {"blocked", "stopped", "finished", "expired", "completed"}


class DevinError(RuntimeError):
    """Raised when the Devin API call fails."""


def has_credentials() -> bool:
    return bool(os.getenv("DEVIN_API_KEY"))


class Devin:
    """Thin stdlib client for Devin's v1 session API."""

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.getenv("DEVIN_API_KEY")
        if not self.api_key:
            raise DevinError("DEVIN_API_KEY is not set.")

    def _request(self, method: str, path: str, body: Optional[dict] = None, timeout: int = 60) -> dict:
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(
            DEVIN_BASE + path,
            data=data,
            method=method,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8")
                return json.loads(text) if text else {}
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:300]
            raise DevinError(f"Devin HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise DevinError(f"Devin connection error: {exc.reason}") from exc

    def create_session(self, prompt: str, *, title: Optional[str] = None,
                        idempotent: bool = True) -> Dict[str, Any]:
        body: Dict[str, Any] = {"prompt": prompt, "idempotent": idempotent}
        if title:
            body["title"] = title
        return self._request("POST", "/sessions", body)

    def get_session(self, session_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/session/{session_id}")

    def send_message(self, session_id: str, message: str) -> Dict[str, Any]:
        return self._request("POST", f"/session/{session_id}/message", {"message": message})

    def run(self, prompt: str, *, title: Optional[str] = None,
            wait: bool = False, poll_seconds: int = 20, timeout_seconds: int = 1800) -> Dict[str, Any]:
        """Create a session and optionally poll until it reaches a terminal state.

        With ``wait=False`` (default) this returns immediately with the session
        URL so the conductor stays responsive — Devin keeps working in the
        background and you follow it at that URL.
        """
        session = self.create_session(prompt, title=title)
        session_id = session.get("session_id")
        if not wait or not session_id:
            return session

        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            detail = self.get_session(session_id)
            status = (detail.get("status_enum") or detail.get("status") or "").lower()
            if status in _TERMINAL:
                return {**session, **detail}
            time.sleep(poll_seconds)
        return {**session, "status": "timeout"}
