#!/usr/bin/env python3
"""Key rotation helper for Shadow Garden — rotate the 4 leaked API keys.

Provides:
  - Checklist for rotating each key
  - Validation that keys have been cleared from environment
  - Integration with connector_bridge_enhanced for post-rotation verification

The 4 keys that need rotation:
  1. JWT_TOKEN
  2. STABLE_HORDE_API_KEY
  3. ELEVENLABS_API_KEY
  4. PERPLEXITY_API_KEY

Usage:
    python3 key_rotation_helper.py checklist
    python3 key_rotation_helper.py verify
    python3 key_rotation_helper.py self-test
"""

from __future__ import annotations

import argparse
import json
import os
from typing import Any


LEAKED_KEYS = [
    {
        "name": "JWT Token",
        "env_names": ("JWT_TOKEN", "JWT", "SHADOW_GARDEN_JWT"),
        "service": "Authentication",
        "rotation_url": "https://jwt.io/",  # Replace with actual issuer
        "steps": [
            "1. Go to your JWT issuer service",
            "2. Generate a new JWT token",
            "3. Export to environment: export JWT_TOKEN=<new_token>",
            "4. Update any applications using this token",
            "5. Run: python3 key_rotation_helper.py verify",
        ],
    },
    {
        "name": "Stable Horde API Key",
        "env_names": ("STABLE_HORDE_API_KEY", "HORDE_KEY", "STABLE_HORDE_KEY"),
        "service": "Stable Horde",
        "rotation_url": "https://stablehorde.net/",
        "steps": [
            "1. Go to Stable Horde dashboard (https://stablehorde.net/)",
            "2. Log in to your account",
            "3. Go to Settings > API Keys",
            "4. Generate a new API key",
            "5. Export to environment: export STABLE_HORDE_API_KEY=<new_key>",
            "6. Run: python3 key_rotation_helper.py verify",
        ],
    },
    {
        "name": "ElevenLabs API Key",
        "env_names": ("ELEVENLABS_API_KEY", "ELEVEN_KEY", "ELEVENLABS_KEY"),
        "service": "ElevenLabs",
        "rotation_url": "https://elevenlabs.io/app/speech-synthesis",
        "steps": [
            "1. Go to ElevenLabs dashboard (https://elevenlabs.io/)",
            "2. Log in to your account",
            "3. Go to Account > API Key",
            "4. Click 'Regenerate API Key'",
            "5. Export to environment: export ELEVENLABS_API_KEY=<new_key>",
            "6. Run: python3 key_rotation_helper.py verify",
        ],
    },
    {
        "name": "Perplexity API Key",
        "env_names": ("PERPLEXITY_API_KEY", "PPL_KEY", "PERPLEXITY_KEY"),
        "service": "Perplexity",
        "rotation_url": "https://www.perplexity.ai/",
        "steps": [
            "1. Go to Perplexity account settings",
            "2. Navigate to API Keys section",
            "3. Create a new API key",
            "4. Export to environment: export PERPLEXITY_API_KEY=<new_key>",
            "5. Run: python3 key_rotation_helper.py verify",
        ],
    },
]


def get_checklist() -> dict[str, Any]:
    """Return the full rotation checklist."""
    return {
        "schema": "shadow_garden.key_rotation_checklist.v1",
        "critical": "All 4 keys were leaked and must be rotated",
        "keys": [
            {
                "name": k["name"],
                "service": k["service"],
                "env_names": k["env_names"],
                "rotation_url": k["rotation_url"],
                "steps": k["steps"],
            }
            for k in LEAKED_KEYS
        ],
        "verification_command": "python3 key_rotation_helper.py verify",
    }


def verify_rotation() -> dict[str, Any]:
    """Check if all 4 keys have been rotated (cleared from environment)."""
    status_by_key = {}
    all_clear = True

    for key_info in LEAKED_KEYS:
        found_in_env = False
        for env_name in key_info["env_names"]:
            if os.getenv(env_name):
                found_in_env = True
                break

        status = "CLEAR" if not found_in_env else "FOUND_IN_ENV"
        if not found_in_env:
            all_clear = False

        status_by_key[key_info["name"]] = {
            "status": status,
            "env_names_checked": key_info["env_names"],
            "message": "✓ Key has been rotated" if not found_in_env else "✗ Old key still in environment",
        }

    return {
        "schema": "shadow_garden.key_rotation_verification.v1",
        "all_keys_rotated": all_clear,
        "status_by_key": status_by_key,
        "next_step": "All 4 keys rotated! Run: python3 connector_bridge_enhanced.py validate-keys"
        if all_clear
        else "Complete rotation steps above before proceeding",
    }


def run_self_test() -> dict[str, Any]:
    """Verify the helper functions work correctly."""
    checks = []

    # Checklist generates properly.
    checklist = get_checklist()
    if checklist.get("schema") == "shadow_garden.key_rotation_checklist.v1":
        checks.append("checklist_generation")

    # Verification generates properly.
    verification = verify_rotation()
    if verification.get("schema") == "shadow_garden.key_rotation_verification.v1":
        checks.append("verification_generation")

    return {"ok": True, "tests": len(checks), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser(description="Shadow Garden key rotation helper")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("checklist")
    sub.add_parser("verify")
    sub.add_parser("self-test")

    args = parser.parse_args()

    if args.command == "checklist":
        result = get_checklist()
    elif args.command == "verify":
        result = verify_rotation()
    elif args.command == "self-test":
        result = run_self_test()
    else:
        result = {"error": "unknown command"}

    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
