#!/usr/bin/env python3
"""Shadow Garden task orchestrator — master workflow for 5 pending human tasks.

Orchestrates:
  1. Rotate 4 leaked API keys
  2. Rekey HARPA (403 error)
  3. Rebind Qdrant (transport fail)
  4. Launch ComfyUI + re-run bridge probe
  5. Set up Steamworks Partner account

Each task is independent and can be run in any order, but this script
provides a guided checklist workflow.

Usage:
    python3 task_orchestrator.py status              # show current status
    python3 task_orchestrator.py task <N>            # guide for task N (1-5)
    python3 task_orchestrator.py task <N> --quick    # brief output
    python3 task_orchestrator.py verify-all          # test all tasks
    python3 task_orchestrator.py self-test
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

# Import the helper modules (they must be in the same directory).
try:
    import connector_bridge_enhanced as bridge_enh
    import key_rotation_helper as key_rot
    import steamworks_integration as steamworks
except ImportError as e:
    print(f"Error: Could not import helper modules. {e}", file=sys.stderr)
    sys.exit(1)


TASKS = [
    {
        "id": 1,
        "title": "Rotate 4 Leaked API Keys",
        "priority": "CRITICAL",
        "keys": ["JWT", "STABLE_HORDE", "ELEVENLABS", "PERPLEXITY"],
        "description": "All 4 API keys were exposed and must be rotated immediately.",
        "time_estimate": "20 minutes",
        "steps_module": "key_rotation_helper",
        "verification_command": "python3 key_rotation_helper.py verify",
    },
    {
        "id": 2,
        "title": "Rekey HARPA (Fix 403 Error)",
        "priority": "HIGH",
        "description": "HARPA API key is invalid (403 error). Regenerate in HARPA AUTOMATE tab.",
        "time_estimate": "5 minutes",
        "steps_module": "connector_bridge_enhanced",
        "verification_command": "python3 connector_bridge_enhanced.py validate-harpa",
    },
    {
        "id": 3,
        "title": "Rebind Qdrant (Fix Transport Fail)",
        "priority": "HIGH",
        "description": "Qdrant cluster connection failed. Update cluster URL and API key.",
        "time_estimate": "10 minutes",
        "steps_module": "connector_bridge_enhanced",
        "verification_command": "python3 connector_bridge_enhanced.py validate-qdrant",
    },
    {
        "id": 4,
        "title": "Launch ComfyUI + Re-run Bridge Probe",
        "priority": "MEDIUM",
        "description": "Launch the ComfyUI app on your Mac, then verify it's listening.",
        "time_estimate": "5 minutes",
        "steps_module": "connector_bridge_enhanced",
        "verification_command": "python3 connector_bridge_enhanced.py validate-comfyui",
    },
    {
        "id": 5,
        "title": "Set Up Steamworks Partner Account",
        "priority": "MEDIUM",
        "description": "Create separate Steamworks Partner account (not personal) for publishing.",
        "time_estimate": "30 minutes (+ 1-2 days for tax/banking setup)",
        "steps_module": "steamworks_integration",
        "verification_command": "python3 steamworks_integration.py readiness",
    },
]


def get_status() -> dict[str, Any]:
    """Get the current status of all 5 tasks."""
    status = {
        "schema": "shadow_garden.task_orchestrator_status.v1",
        "tasks": [],
    }

    # Task 1: Key rotation
    key_status = key_rot.verify_rotation()
    status["tasks"].append({
        "id": 1,
        "title": TASKS[0]["title"],
        "all_rotated": key_status.get("all_keys_rotated", False),
        "status": "COMPLETE" if key_status.get("all_keys_rotated") else "PENDING",
    })

    # Task 2: HARPA
    harpa_status = bridge_enh.validate_harpa()
    status["tasks"].append({
        "id": 2,
        "title": TASKS[1]["title"],
        "status": "COMPLETE" if harpa_status.get("status") == "ok" else "PENDING",
    })

    # Task 3: Qdrant
    qdrant_status = bridge_enh.validate_qdrant()
    status["tasks"].append({
        "id": 3,
        "title": TASKS[2]["title"],
        "status": "COMPLETE" if qdrant_status.get("status") == "ok" else "PENDING",
    })

    # Task 4: ComfyUI
    comfyui_status = bridge_enh.validate_comfyui()
    status["tasks"].append({
        "id": 4,
        "title": TASKS[3]["title"],
        "status": "COMPLETE" if comfyui_status.get("status") == "ok" else "PENDING",
    })

    # Task 5: Steamworks
    steam_status = steamworks.check_readiness()
    status["tasks"].append({
        "id": 5,
        "title": TASKS[4]["title"],
        "status": "COMPLETE" if steam_status.get("overall_ready") else "PENDING",
    })

    completed = sum(1 for t in status["tasks"] if t["status"] == "COMPLETE")
    status["summary"] = {
        "total_tasks": len(TASKS),
        "completed": completed,
        "pending": len(TASKS) - completed,
        "progress_pct": int((completed / len(TASKS)) * 100),
    }

    return status


def get_task_guidance(task_id: int, quick: bool = False) -> dict[str, Any]:
    """Get detailed guidance for a specific task."""
    if task_id < 1 or task_id > len(TASKS):
        return {"error": f"invalid task id; must be 1-{len(TASKS)}"}

    task = TASKS[task_id - 1]

    if task_id == 1:
        guidance = key_rot.get_checklist()
    elif task_id == 2:
        guidance = bridge_enh.validate_harpa()
    elif task_id == 3:
        guidance = bridge_enh.validate_qdrant()
    elif task_id == 4:
        guidance = bridge_enh.validate_comfyui()
    elif task_id == 5:
        guidance = steamworks.get_checklist()
    else:
        return {"error": "unknown task"}

    if quick:
        return {
            "task_id": task_id,
            "title": task["title"],
            "priority": task["priority"],
            "time_estimate": task["time_estimate"],
            "next_step": guidance.get("next_steps", ["See full guidance below"])[:1],
        }

    return {
        "task_id": task_id,
        "title": task["title"],
        "priority": task["priority"],
        "time_estimate": task["time_estimate"],
        "description": task["description"],
        "verification_command": task["verification_command"],
        "full_guidance": guidance,
    }


def verify_all_tasks() -> dict[str, Any]:
    """Run verification for all 5 tasks."""
    verifications = {}

    verifications["1_key_rotation"] = key_rot.verify_rotation()
    verifications["2_harpa"] = bridge_enh.validate_harpa()
    verifications["3_qdrant"] = bridge_enh.validate_qdrant()
    verifications["4_comfyui"] = bridge_enh.validate_comfyui()
    verifications["5_steamworks"] = steamworks.check_readiness()

    all_ok = all(
        v.get("status") == "ok" or v.get("all_keys_rotated") or v.get("overall_ready")
        for v in verifications.values()
    )

    return {
        "schema": "shadow_garden.task_orchestrator_verify.v1",
        "all_tasks_ok": all_ok,
        "verifications": verifications,
    }


def run_self_test() -> dict[str, Any]:
    """Test all helper modules."""
    checks = []

    try:
        key_rot.run_self_test()
        checks.append("key_rotation_helper")
    except Exception as e:
        return {"error": f"key_rotation_helper failed: {e}"}

    try:
        bridge_enh.run_self_test()
        checks.append("connector_bridge_enhanced")
    except Exception as e:
        return {"error": f"connector_bridge_enhanced failed: {e}"}

    try:
        steamworks.run_self_test()
        checks.append("steamworks_integration")
    except Exception as e:
        return {"error": f"steamworks_integration failed: {e}"}

    return {"ok": True, "tests": len(checks), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Shadow Garden task orchestrator (5 pending human tasks)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status")
    sub.add_parser("verify-all")
    sub.add_parser("self-test")

    task_parser = sub.add_parser("task")
    task_parser.add_argument("task_id", type=int, help="Task ID (1-5)")
    task_parser.add_argument("--quick", action="store_true", help="Brief output")

    args = parser.parse_args()

    if args.command == "status":
        result = get_status()
    elif args.command == "verify-all":
        result = verify_all_tasks()
    elif args.command == "self-test":
        result = run_self_test()
    elif args.command == "task":
        result = get_task_guidance(args.task_id, args.quick)
    else:
        result = {"error": "unknown command"}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") or result.get("all_tasks_ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
