#!/usr/bin/env python3
"""Bounded Black Sun learning loop for Universe Simulation Alpha, Section One.

Offline evidence loop: observe -> validate -> compare -> propose -> gate -> emit.
It never posts, pushes, browses, calls connectors, edits source code, or grants
authority. External systems consume its signed JSON packets manually.
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
MIRROR = HERE.parent
STATE = HERE / "state"
OUTBOX = HERE / "outbox"
SOURCE = HERE / "section_one_source.json"
MAX_HISTORY = 64

CONTROLS = {
    "external_fetch": False,
    "browser_automation": False,
    "agent_broadcast": False,
    "credentials_allowed": False,
    "source_code_mutation": False,
    "external_write": False,
    "x_read_only": True,
    "symbolic_only": True,
}

ROUTING = {
    "north": "lunar",
    "south": "solar",
    "cross_type": "tera",
    "invariant": "North->Lunar; South->Solar; cross-type/application->Tera",
}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def digest(obj: Any) -> str:
    return hashlib.sha256(canonical(obj).encode("utf-8")).hexdigest()


def atomic(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2)
    with tmp.open("w", encoding="utf-8") as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def validate_source(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if source.get("task_id") != "2366bfee-b78c-4ddc-9f86-304c30c67c4d":
        errors.append("unexpected_task_id")
    section = source.get("section_one") or {}
    if section.get("name") != "Boundless Playground v0":
        errors.append("unexpected_section_one_name")
    if section.get("node_count") != 22:
        errors.append("node_count_must_equal_22")
    if source.get("routing") != ROUTING:
        errors.append("routing_contract_mismatch")
    controls = source.get("controls") or {}
    for key, value in CONTROLS.items():
        if controls.get(key) is not value:
            errors.append(f"control_mismatch:{key}")
    return errors


def collect_observations(source: dict[str, Any]) -> dict[str, Any]:
    paths = {
        "eden_server": MIRROR / "eden_burst_alpha.py",
        "drake_port": MIRROR / "shaoshi_bridge/drake_terminal/drake_parallel_port.py",
        "fable5_game": MIRROR / "fable5_game/web/game.js",
        "black_sun_canon": MIRROR / "canon/black_sun_canon.md",
        "catalyst_light": MIRROR.parent / "catalyst_light/pipeline.py",
    }
    files = {
        name: {
            "present": path.exists(),
            "bytes": path.stat().st_size if path.exists() else 0,
            "path": str(path),
        }
        for name, path in paths.items()
    }
    return {
        "source_digest": digest(source),
        "files": files,
        "section_one_status": (source.get("section_one") or {}).get("status"),
        "known_blockers": source.get("blockers") or [],
    }


def compare(source: dict[str, Any], obs: dict[str, Any]) -> dict[str, Any]:
    required = source["section_one"]["required_capabilities"]
    present = obs["files"]
    capability_map = {
        "taiji_router": True,
        "node_constellation_22": source["section_one"]["node_count"] == 22,
        "fable5_adapter": present["fable5_game"]["present"],
        "eden_shell": present["eden_server"]["present"],
        "black_sun_learning": True,
        "catalyst_light_validation": present["catalyst_light"]["present"],
    }
    missing = [cap for cap in required if not capability_map.get(cap, False)]
    return {
        "capabilities": capability_map,
        "required": required,
        "missing": missing,
        "coverage": round(
            sum(1 for cap in required if capability_map.get(cap, False))
            / max(1, len(required)),
            4,
        ),
    }


def propose(source: dict[str, Any], delta: dict[str, Any]) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []
    for missing in delta["missing"]:
        proposals.append({
            "priority": "p0",
            "kind": "implementation",
            "capability": missing,
            "action": f"Implement and test {missing} inside Section One only",
            "route": "tera",
            "requires_human_approval": True,
        })
    for blocker in source.get("blockers") or []:
        proposals.append({
            "priority": blocker.get("priority", "p1"),
            "kind": "blocker",
            "capability": blocker.get("id"),
            "action": blocker.get("next_action"),
            "route": "tera",
            "requires_human_approval": bool(blocker.get("external_write", False)),
        })
    proposals.extend([
        {
            "priority": "p0",
            "kind": "gameplay",
            "capability": "first_playable_loop",
            "action": "Connect Taiji rotation, 22-node selection, and one Fable5 spell compile into a 90-second playable loop",
            "route": "tera",
            "requires_human_approval": False,
        },
        {
            "priority": "p1",
            "kind": "qa",
            "capability": "deterministic_replay",
            "action": "Record input seed and verify identical node routing and field state on replay",
            "route": "north",
            "requires_human_approval": False,
        },
    ])
    return proposals


def gate(proposals: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "auto_safe_proposals": [p for p in proposals if not p["requires_human_approval"]],
        "held_for_user_approval": [p for p in proposals if p["requires_human_approval"]],
        "external_actions_executed": 0,
        "source_mutations_executed": 0,
    }


def run() -> dict[str, Any]:
    source = load_json(SOURCE, {})
    errors = validate_source(source)
    if errors:
        result = {
            "schema": "black_sun_learning_packet.v1",
            "status": "rejected",
            "errors": errors,
            "controls": CONTROLS,
            "generated_at": now(),
        }
        atomic(STATE / "latest.json", result)
        return result

    observation = collect_observations(source)
    delta = compare(source, observation)
    gated = gate(propose(source, delta))
    packet_core = {
        "schema": "black_sun_learning_packet.v1",
        "status": "processed",
        "task_id": source["task_id"],
        "section": "universe_alpha.section_1",
        "section_name": source["section_one"]["name"],
        "sequence": ["observe", "validate", "compare", "propose", "gate", "emit"],
        "routing": ROUTING,
        "observation": observation,
        "delta": delta,
        "gate": gated,
        "controls": CONTROLS,
        "generated_at": now(),
        "warnings": [
            "Black Sun is symbolic_only mythology metadata, not authority",
            "This loop does not self-modify or write to external systems",
            "External connector actions require a separate user-authorized step",
        ],
    }
    packet = {**packet_core, "run_id": digest(packet_core)[:16]}
    history = load_json(STATE / "history.json", [])
    if not isinstance(history, list):
        history = []
    if not history or history[-1].get("run_id") != packet["run_id"]:
        history.append({
            "run_id": packet["run_id"],
            "generated_at": packet["generated_at"],
            "coverage": delta["coverage"],
            "source_digest": observation["source_digest"],
        })
    atomic(STATE / "latest.json", packet)
    atomic(STATE / "history.json", history[-MAX_HISTORY:])
    atomic(OUTBOX / f"section_one_{packet['run_id']}.json", packet)
    return packet


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2))
