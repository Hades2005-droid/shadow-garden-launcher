#!/usr/bin/env python3
"""
NWW Asana Connector for Shadow Garden.

Additive reporting adapter that pushes Shadow Garden operational signals to
Asana. It does NOT replace the existing Jira-first behavior — Asana reporting
is opt-in and only activates when the required env vars are present.

Reportable signals:
  * Voice synthesis latency / quality metrics
  * Grok chat sync status
  * Message counts
  * Sanitized conversation summaries

Secrets are read from the environment only (never hard-coded):
  ASANA_ACCESS_TOKEN      Personal access token (required to enable)
  ASANA_WORKSPACE_ID      Workspace GID (optional; used on task create)
  ASANA_PROJECT_SHADOWGARDEN  Project GID tasks are added to (optional)
  ASANA_BASE_URL          Override API base (default https://app.asana.com/api/1.0)

Usage (library):
  from asana_connector import AsanaConfig, AsanaConnector
  cfg = AsanaConfig.from_env()
  if cfg.enabled:
      conn = AsanaConnector(cfg)
      conn.report_voice_synthesis("Angela", latency_ms=812.4, quality=0.93)

Usage (CLI):
  python3 asana_connector.py --check
  python3 asana_connector.py --voice Angela --latency-ms 812 --quality 0.93
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

DEFAULT_BASE_URL = "https://app.asana.com/api/1.0"

# Patterns for sanitizing potentially sensitive content out of summaries before
# they leave the machine and land in Asana.
_SECRET_PATTERNS = [
    re.compile(r"\b[A-Za-z0-9_-]*(?:api[_-]?key|token|secret|password|bearer)[A-Za-z0-9_-]*\s*[=:]\s*\S+", re.I),
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),  # OpenAI-style keys
    re.compile(r"\bxai-[A-Za-z0-9]{16,}\b"),  # xAI-style keys
    re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),  # emails
    re.compile(r"\b(?:\d[ -]?){13,16}\b"),  # long digit runs (card-like)
]

_MAX_SUMMARY_CHARS = 4000


class AsanaConfigError(RuntimeError):
    """Raised when Asana reporting is requested but not configured."""


@dataclass
class AsanaConfig:
    access_token: str = ""
    workspace_id: str = ""
    project_id: str = ""
    base_url: str = DEFAULT_BASE_URL

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "AsanaConfig":
        env = env if env is not None else os.environ
        return cls(
            access_token=env.get("ASANA_ACCESS_TOKEN", "").strip(),
            workspace_id=env.get("ASANA_WORKSPACE_ID", "").strip(),
            project_id=env.get("ASANA_PROJECT_SHADOWGARDEN", "").strip(),
            base_url=env.get("ASANA_BASE_URL", DEFAULT_BASE_URL).strip() or DEFAULT_BASE_URL,
        )

    @property
    def enabled(self) -> bool:
        """Asana reporting is only active when an access token is present."""
        return bool(self.access_token)

    def require_enabled(self) -> None:
        if not self.enabled:
            raise AsanaConfigError(
                "Asana reporting not configured: set ASANA_ACCESS_TOKEN "
                "(see .env.example). Shadow Garden Jira-first behavior is unaffected."
            )


def sanitize_text(text: str, max_chars: int = _MAX_SUMMARY_CHARS) -> str:
    """Strip likely secrets/PII and clamp length before sending to Asana."""
    if not text:
        return ""
    cleaned = text
    for pattern in _SECRET_PATTERNS:
        cleaned = pattern.sub("[REDACTED]", cleaned)
    cleaned = cleaned.strip()
    if len(cleaned) > max_chars:
        cleaned = cleaned[: max_chars - 1].rstrip() + "…"
    return cleaned


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


@dataclass
class AsanaConnector:
    config: AsanaConfig
    timeout: float = 15.0
    # Injectable opener for tests; defaults to urllib at call time.
    _opener: Any = field(default=None, repr=False)

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict:
        self.config.require_enabled()
        url = f"{self.config.base_url.rstrip('/')}/{path.lstrip('/')}"
        data = None
        if payload is not None:
            data = json.dumps({"data": payload}).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Authorization", f"Bearer {self.config.access_token}")
        req.add_header("Accept", "application/json")
        if data is not None:
            req.add_header("Content-Type", "application/json")

        opener = self._opener or urllib.request.urlopen
        try:
            with opener(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
        except urllib.error.HTTPError as exc:  # pragma: no cover - network path
            detail = exc.read().decode("utf-8", "replace") if hasattr(exc, "read") else str(exc)
            raise AsanaConfigError(f"Asana API error {exc.code}: {detail[:500]}") from exc
        return json.loads(body) if body else {}

    def create_task(self, name: str, notes: str = "") -> dict:
        """Create a task in the configured project/workspace."""
        payload: dict[str, Any] = {"name": sanitize_text(name, 512), "notes": sanitize_text(notes)}
        if self.config.project_id:
            payload["projects"] = [self.config.project_id]
        if self.config.workspace_id:
            payload["workspace"] = self.config.workspace_id
        return self._request("POST", "/tasks", payload)

    # --- High-level Shadow Garden reporters -------------------------------

    def report_voice_synthesis(
        self, voice: str, latency_ms: float, quality: float | None = None, extra: str = ""
    ) -> dict:
        quality_str = f"{quality:.3f}" if quality is not None else "n/a"
        name = f"[SG] Voice synthesis — {voice} ({latency_ms:.0f}ms)"
        notes = (
            f"Voice: {voice}\n"
            f"Latency: {latency_ms:.1f} ms\n"
            f"Quality: {quality_str}\n"
            f"Reported: {_utc_stamp()}\n"
        )
        if extra:
            notes += f"\n{sanitize_text(extra)}\n"
        return self.create_task(name, notes)

    def report_grok_sync(self, status: str, message_count: int, detail: str = "") -> dict:
        name = f"[SG] Grok chat sync — {status} ({message_count} msgs)"
        notes = (
            f"Sync status: {status}\n"
            f"Messages: {message_count}\n"
            f"Reported: {_utc_stamp()}\n"
        )
        if detail:
            notes += f"\n{sanitize_text(detail)}\n"
        return self.create_task(name, notes)

    def report_conversation_summary(self, title: str, summary: str, message_count: int | None = None) -> dict:
        name = f"[SG] Conversation summary — {sanitize_text(title, 200)}"
        header = f"Reported: {_utc_stamp()}\n"
        if message_count is not None:
            header += f"Messages: {message_count}\n"
        notes = f"{header}\n{sanitize_text(summary)}\n"
        return self.create_task(name, notes)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="NWW Asana Connector for Shadow Garden")
    p.add_argument("--check", action="store_true", help="Report whether Asana reporting is configured")
    p.add_argument("--voice", help="Voice name for a synthesis report")
    p.add_argument("--latency-ms", type=float, help="Synthesis latency in milliseconds")
    p.add_argument("--quality", type=float, help="Synthesis quality score (0-1)")
    p.add_argument("--sync-status", help="Grok chat sync status to report")
    p.add_argument("--messages", type=int, help="Message count for the sync report")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    cfg = AsanaConfig.from_env()

    if args.check or not (args.voice or args.sync_status):
        state = "enabled" if cfg.enabled else "disabled (set ASANA_ACCESS_TOKEN)"
        print(f"Asana reporting: {state}")
        print(f"  workspace: {cfg.workspace_id or '(unset)'}")
        print(f"  project:   {cfg.project_id or '(unset)'}")
        return 0

    if not cfg.enabled:
        print("Asana reporting disabled — set ASANA_ACCESS_TOKEN to enable.", file=sys.stderr)
        return 1

    conn = AsanaConnector(cfg)
    if args.voice:
        if args.latency_ms is None:
            print("--latency-ms is required with --voice", file=sys.stderr)
            return 2
        result = conn.report_voice_synthesis(args.voice, args.latency_ms, args.quality)
        print(f"Created task: {result.get('data', {}).get('gid', '(no gid)')}")
    if args.sync_status:
        result = conn.report_grok_sync(args.sync_status, args.messages or 0)
        print(f"Created task: {result.get('data', {}).get('gid', '(no gid)')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
