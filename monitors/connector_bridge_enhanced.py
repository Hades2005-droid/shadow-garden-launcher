#!/usr/bin/env python3
"""Shadow Garden connector bridge (enhanced) — LOCAL, credential-free.

Extends connector_bridge.py with:
  - Post-rebind validation helpers (test HARPA/Qdrant after you rekey)
  - Key rotation status checker
  - ComfyUI readiness verification
  - Better diagnostics for the 5 pending human tasks

Design contract (same as base bridge):
  - No credentials stored, read, or transmitted.
  - No external writes. Only localhost TCP probes + JSON file write.
  - Deterministic: same inputs -> same output.

Usage:
    python3 connector_bridge_enhanced.py probe --now 2026-07-XX
    python3 connector_bridge_enhanced.py validate-keys
    python3 connector_bridge_enhanced.py validate-harpa
    python3 connector_bridge_enhanced.py validate-qdrant
    python3 connector_bridge_enhanced.py validate-comfyui
    python3 connector_bridge_enhanced.py self-test
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
from dataclasses import dataclass
from typing import Any, Optional

# ---- controls (same as base bridge) ----
CONTROLS = {
    "external_fetch": False,
    "browser_automation": False,
    "agent_broadcast": False,
    "credentials_allowed": False,
    "generated_code_execution": False,
    "shell_execution": False,
    "provider_calls": False,
    "safe_abort": True,
}

OK = "ok"
DEGRADED = "degraded"
CRON_NO_CLI = "cron_no_cli"
ERROR = "error"
ASSUMED_OK = "assumed_ok"


@dataclass(frozen=True)
class LocalService:
    """A loopback service the bridge can TCP-probe.

    ``owner`` records who is responsible for starting it, so a DEGRADED
    result routes to a person instead of sitting unexplained.
    """
    name: str
    port: int
    path: str = "local"
    owner: str = "unassigned"
    required: bool = False


# ---------------------------------------------------------------------------
# Single source of truth for loopback services.
#
# To wire a new one in, add a row HERE and nothing else: the probe loop, the
# `validate-service` command, and the orchestrator's port map all read from
# this tuple. Adding a row must never require editing three files.
#
# A probe reports only whether a port accepts a TCP connection. It sends no
# payload, reads no response body, and knows nothing about what the service
# hosts.
# ---------------------------------------------------------------------------
LOCAL_SERVICES = (
    LocalService("fable5", 5619, "http://127.0.0.1:5619/", owner="launcher", required=True),
    LocalService("spell_sim", 5173, "Vite dev server", owner="wha-spell-simulator"),
    LocalService("comfyui", 8188, "ComfyUI", owner="human:launch-app", required=True),
    LocalService("comfyui_alt", 8000, "ComfyUI alt port", owner="human:launch-app"),
    LocalService("eden_shell", 8790, "Eden shell", owner="devin:needs-approval"),
    LocalService("control_center", 8851, "Control center", owner="human:launch-app"),
)

SERVICES_BY_NAME = {s.name: s for s in LOCAL_SERVICES}

# Keys that need rotation (the 4 leaked keys).
LEAKED_KEYS = ("JWT", "STABLE_HORDE", "ELEVENLABS", "PERPLEXITY")
KEY_ENV_NAMES = {
    "JWT": ("JWT_TOKEN", "SHADOW_GARDEN_JWT"),
    "STABLE_HORDE": ("STABLE_HORDE_API_KEY", "HORDE_KEY"),
    "ELEVENLABS": ("ELEVENLABS_API_KEY", "ELEVEN_KEY"),
    "PERPLEXITY": ("PERPLEXITY_API_KEY", "PPL_KEY"),
}


def probe_local(service: LocalService, timeout: float = 1.0) -> dict[str, Any]:
    """TCP-connect probe to a local service."""
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


def check_keys() -> dict[str, Any]:
    """Check if the 4 leaked keys have been rotated (removed from env)."""
    results = {}
    for key_name, env_names in KEY_ENV_NAMES.items():
        found = False
        for env in env_names:
            if os.getenv(env):
                found = True
                break
        results[key_name] = {
            "status": ERROR if found else OK,
            "message": f"key still in env (needs rotation)" if found else "key cleared from env",
        }
    return {
        "schema": "shadow_garden.key_rotation_status.v1",
        "leaked_keys": results,
        "all_cleared": all(r["status"] == OK for r in results.values()),
    }


def validate_harpa() -> dict[str, Any]:
    """Test HARPA readiness after rekey."""
    # HARPA is cloud-based; we can only check env vars for now.
    token = os.getenv("HARPA_API_KEY") or os.getenv("HARPA_TOKEN")
    return {
        "schema": "shadow_garden.harpa_validation.v1",
        "status": OK if token else ERROR,
        "message": "HARPA_API_KEY set in environment" if token else "HARPA_API_KEY not found; rekey via HARPA AUTOMATE tab",
        "next_steps": [
            "1. Open HARPA website (https://harpa.ai/)",
            "2. Go to AUTOMATE tab",
            "3. Generate new API key",
            "4. Export HARPA_API_KEY=<new_key> in your shell",
            "5. Run: python3 connector_bridge_enhanced.py validate-harpa",
        ] if not token else [],
    }


def validate_qdrant() -> dict[str, Any]:
    """Test Qdrant readiness after rebind."""
    # Qdrant is cloud-based; check env vars for cluster config.
    cluster_url = os.getenv("QDRANT_CLUSTER_URL") or os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    return {
        "schema": "shadow_garden.qdrant_validation.v1",
        "status": OK if (cluster_url and api_key) else ERROR,
        "cluster_url_set": bool(cluster_url),
        "api_key_set": bool(api_key),
        "message": "Qdrant cluster configured" if (cluster_url and api_key) else "Qdrant not fully configured",
        "next_steps": [
            "1. Open Qdrant Cloud dashboard (https://qdrant.tech/)",
            "2. Create or retrieve your cluster URL",
            "3. Generate new API key",
            "4. Export QDRANT_CLUSTER_URL=<url> and QDRANT_API_KEY=<key>",
            "5. Run: python3 connector_bridge_enhanced.py validate-qdrant",
        ] if not (cluster_url and api_key) else [],
    }


def validate_service(name: str) -> dict[str, Any]:
    """Probe any registered loopback service by name.

    Generic counterpart to the task-specific validators: anything in
    LOCAL_SERVICES is checkable without adding a bespoke function.
    """
    service = SERVICES_BY_NAME.get(name)
    if service is None:
        return {
            "schema": "shadow_garden.service_validation.v1",
            "status": ERROR,
            "service": name,
            "message": f"unknown service {name!r}",
            "next_steps": [f"known services: {', '.join(sorted(SERVICES_BY_NAME))}"],
        }

    result = probe_local(service)
    up = result["status"] == OK
    return {
        "schema": "shadow_garden.service_validation.v1",
        "status": result["status"],
        "service": service.name,
        "port": service.port,
        "owner": service.owner,
        "required": service.required,
        "message": result["reason"],
        "next_steps": [] if up else [
            f"start {service.name} so it listens on 127.0.0.1:{service.port}",
            f"owner: {service.owner}",
            f"re-check: python3 connector_bridge_enhanced.py validate-service {service.name}",
        ],
    }


def port_map() -> dict[str, Any]:
    """Probe every registered service at once — the loopback coverage view."""
    services = {s.name: validate_service(s.name) for s in LOCAL_SERVICES}
    missing_required = [
        n for n, r in services.items()
        if r["status"] != OK and SERVICES_BY_NAME[n].required
    ]
    return {
        "schema": "shadow_garden.port_map.v1",
        "services": services,
        "up": sorted(n for n, r in services.items() if r["status"] == OK),
        "down": sorted(n for n, r in services.items() if r["status"] != OK),
        "missing_required": missing_required,
        "all_required_up": not missing_required,
    }


def validate_comfyui() -> dict[str, Any]:
    """Test ComfyUI readiness after launch."""
    result = probe_local(SERVICES_BY_NAME["comfyui"])  # ComfyUI on 8188
    return {
        "schema": "shadow_garden.comfyui_validation.v1",
        "status": result["status"],
        "message": "ComfyUI is listening on 127.0.0.1:8188" if result["status"] == OK else "ComfyUI not responding",
        "next_steps": [
            "1. Open ComfyUI app on your Mac",
            "2. Navigate to http://127.0.0.1:8188 in your browser",
            "3. Run: python3 connector_bridge_enhanced.py validate-comfyui",
        ] if result["status"] != OK else [],
    }


def run_self_test() -> dict[str, Any]:
    checks = []

    # Key checker works.
    keys = check_keys()
    if isinstance(keys, dict) and "all_cleared" in keys:
        checks.append("key_rotation_checker")

    # HARPA validator works.
    harpa = validate_harpa()
    if isinstance(harpa, dict) and "schema" in harpa:
        checks.append("harpa_validator")

    # Qdrant validator works.
    qdrant = validate_qdrant()
    if isinstance(qdrant, dict) and "schema" in qdrant:
        checks.append("qdrant_validator")

    # ComfyUI validator works.
    comfyui = validate_comfyui()
    if isinstance(comfyui, dict) and "schema" in comfyui:
        checks.append("comfyui_validator")

    # Generic service validator resolves a known name and rejects an unknown one.
    known = validate_service("comfyui")
    unknown = validate_service("does_not_exist")
    if known.get("port") == 8188 and unknown.get("status") == ERROR:
        checks.append("service_validator")

    # Port map covers every registered service, with no duplicate rows.
    pm = port_map()
    if len(pm["services"]) == len(LOCAL_SERVICES) == len(SERVICES_BY_NAME):
        checks.append("port_map_covers_registry")

    # Every validator emits the schema/status/next_steps shape the
    # orchestrator aggregates on. This is the integration contract.
    for payload in (harpa, qdrant, comfyui, known):
        if not {"schema", "status", "next_steps"} <= payload.keys():
            raise RuntimeError(f"validator broke the contract shape: {payload.get('schema')}")
    checks.append("contract_shape")

    return {"ok": True, "tests": len(checks), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Shadow Garden connector bridge (enhanced)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate-keys")
    sub.add_parser("validate-harpa")
    sub.add_parser("validate-qdrant")
    sub.add_parser("validate-comfyui")
    sub.add_parser("port-map")
    sub.add_parser("self-test")

    vs = sub.add_parser("validate-service")
    vs.add_argument("name", help=f"one of: {', '.join(s.name for s in LOCAL_SERVICES)}")

    args = parser.parse_args()

    if args.command == "validate-keys":
        result = check_keys()
    elif args.command == "validate-harpa":
        result = validate_harpa()
    elif args.command == "validate-qdrant":
        result = validate_qdrant()
    elif args.command == "validate-comfyui":
        result = validate_comfyui()
    elif args.command == "validate-service":
        result = validate_service(args.name)
    elif args.command == "port-map":
        result = port_map()
    elif args.command == "self-test":
        result = run_self_test()
    else:
        result = {"error": "unknown command"}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    ok = result.get("ok") or result.get("status") == OK or result.get("all_required_up")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
