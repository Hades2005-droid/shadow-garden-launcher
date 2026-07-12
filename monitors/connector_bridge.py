#!/usr/bin/env python3
"""Shadow Garden connector back-port bridge — LOCAL, credential-free.

Runs on the Mac (where 127.0.0.1:5619 / :5173 / :8188 actually listen) and
reconciles the connector status table into a normalized state.json that matches
the existing monitor schema (ok / degraded / cron_no_cli / error).

Design contract (mirrors q24 / TIMELINE_20 handoff):
  - No credentials are stored, read, or transmitted by this file.
  - No external writes. Only localhost TCP probes + a local JSON file write.
  - Cloud connectors (X / GitHub / Atlassian / Slack / HARPA / Qdrant) are
    reported from a DECLARED status you pass in, never from embedded secrets.
  - Local services (Fable5 / Vite / ComfyUI) are probed on loopback only.
  - Deterministic: same inputs -> same output (timestamps injected, not sampled).

Usage:
    python3 connector_bridge.py probe                 # probe local + declared
    python3 connector_bridge.py probe --now 2026-07-11T11:17:49+0000
    python3 connector_bridge.py self-test
"""

from __future__ import annotations

import argparse
import json
import socket
import sys
from dataclasses import dataclass, field
from typing import Any

# ---- symbolic-only controls, same shape as the engine's CONTROLS ------------
CONTROLS = {
    "external_fetch": False,
    "browser_automation": False,
    "agent_broadcast": False,
    "credentials_allowed": False,      # this bridge NEVER handles secrets
    "generated_code_execution": False,
    "shell_execution": False,
    "provider_calls": False,
    "safe_abort": True,
}

# Status vocabulary — identical to connector_monitor.py so cron can diff cleanly.
OK = "ok"
DEGRADED = "degraded"
CRON_NO_CLI = "cron_no_cli"   # expected when a sub-agent has no CLI creds
ERROR = "error"
ASSUMED_OK = "assumed_ok"


@dataclass(frozen=True)
class LocalService:
    """A service reachable on the Mac's loopback."""
    name: str
    port: int
    path: str = "local"


@dataclass(frozen=True)
class DeclaredConnector:
    """A cloud/off-box connector whose status you assert (no secrets here)."""
    name: str
    status: str
    note: str = ""


# Local services on the Mac's loopback (the ones a container can't see, but the
# Mac can). These are the only things this bridge actively probes.
LOCAL_SERVICES = (
    LocalService("fable5", 5619, "Launch Fable 5.command -> http://127.0.0.1:5619/"),
    LocalService("spell_sim", 5173, "Vite dev server"),
    LocalService("comfyui", 8188, "ComfyUI"),
    LocalService("comfyui_alt", 8000, "ComfyUI alt port"),
)


def probe_local(service: LocalService, timeout: float = 1.0) -> dict[str, Any]:
    """TCP-connect probe. OK if the port accepts a connection, else down."""
    try:
        with socket.create_connection(("127.0.0.1", service.port), timeout):
            status = OK
            reason = "listening"
    except (OSError, ConnectionError):
        status = DEGRADED
        reason = f"no listener on 127.0.0.1:{service.port}"
    return {
        "status": status,
        "path": service.path,
        "port": service.port,
        "reason": reason,
    }


def reconcile(
    declared: list[DeclaredConnector],
    now: str,
    probe: bool = True,
) -> dict[str, Any]:
    results: dict[str, dict[str, Any]] = {}

    for svc in LOCAL_SERVICES:
        results[svc.name] = (
            probe_local(svc) if probe
            else {"status": CRON_NO_CLI, "path": "none", "reason": "probe disabled"}
        )
        results[svc.name]["checked_at"] = now

    for dc in declared:
        results[dc.name] = {
            "status": dc.status,
            "path": "declared",
            "note": dc.note,
            "checked_at": now,
        }

    tally = {OK: 0, DEGRADED: 0, CRON_NO_CLI: 0, ERROR: 0, ASSUMED_OK: 0}
    for entry in results.values():
        tally[entry["status"]] = tally.get(entry["status"], 0) + 1

    # X waterfall priority, per the cron alert policy.
    x = results.get("x", {})
    x_priority = x.get("status") not in (OK, ASSUMED_OK, None)

    return {
        "schema": "shadow_garden.connector_bridge.v1",
        "run_at": now,
        "symbolic_only": True,
        "controls": dict(CONTROLS),
        "tally": tally,
        "alert": {
            # Alert ONLY on real errors — never on degraded / cron_no_cli.
            "should_alert": tally.get(ERROR, 0) > 0,
            "x_waterfall_priority": x_priority,
            "x_status": x.get("status"),
        },
        "results": results,
    }


def declared_from_table() -> list[DeclaredConnector]:
    """The connector table you pasted, as declared status (edit freely)."""
    return [
        DeclaredConnector("x", OK, "read: tweets/metrics/entities via xurl"),
        DeclaredConnector("github", OK, "5 repos under Hades2005-droid"),
        DeclaredConnector("atlassian", OK, "cloud frederickpr10 · Jira KAN + EPL · write Jira only"),
        DeclaredConnector("slack", OK, "#all-shadow-garden · #p-2d-shadow-garden"),
        DeclaredConnector("harpa", ERROR, "key invalid (403) — rekey in HARPA AUTOMATE tab"),
        DeclaredConnector("qdrant", ERROR, "transport fail — rebind cluster when ready"),
    ]


def run_self_test() -> dict[str, Any]:
    checks: list[str] = []
    fixed_now = "2026-07-11T00:00:00+0000"

    # Determinism: same inputs -> identical output (probe off for reproducibility).
    a = reconcile(declared_from_table(), fixed_now, probe=False)
    b = reconcile(declared_from_table(), fixed_now, probe=False)
    if json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
        raise RuntimeError("non-deterministic reconcile")
    checks.append("deterministic")

    # HARPA+Qdrant declared as error -> should_alert must be True.
    if not a["alert"]["should_alert"]:
        raise RuntimeError("error connectors did not raise alert")
    checks.append("alert_on_error")

    # No credentials ever allowed.
    if a["controls"]["credentials_allowed"] is not False:
        raise RuntimeError("credentials must never be allowed")
    checks.append("credential_free")

    # A clean table (no errors) must NOT alert, even with cron_no_cli present.
    clean = reconcile(
        [DeclaredConnector("x", CRON_NO_CLI, "xurl unauth")], fixed_now, probe=False
    )
    if clean["alert"]["should_alert"]:
        raise RuntimeError("cron_no_cli must not trigger an alert")
    if not clean["alert"]["x_waterfall_priority"]:
        raise RuntimeError("x not-ok should flag waterfall priority")
    checks.append("cron_no_cli_is_quiet")

    return {"ok": True, "tests": len(checks), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Shadow Garden connector bridge (local, credential-free)")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("probe")
    p.add_argument("--now", default="1970-01-01T00:00:00+0000",
                   help="ISO timestamp to stamp (inject from `date` on the Mac)")
    p.add_argument("--no-probe", action="store_true", help="skip localhost probes")
    p.add_argument("--out", default="", help="write state.json here (optional)")

    sub.add_parser("self-test")

    args = parser.parse_args()

    if args.command == "self-test":
        result = run_self_test()
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0 if result["ok"] else 1

    result = reconcile(declared_from_table(), args.now, probe=not args.no_probe)
    text = json.dumps(result, indent=2, ensure_ascii=False)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
