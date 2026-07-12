#!/usr/bin/env python3
"""Force-merge EDEN Burst-Alpha + Fable5 media permissions into Drake terminal catalyst.

Offline file-drop only. No agent broadcast. Manual gift loop.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIRROR = HERE.parents[1]
WORKSPACE = MIRROR.parent if (MIRROR.parent / "fable5_media_spell").exists() else Path("/home/user/workspace")
CARRIER = "love_and_harmony_6"
VERSION = "0.1.1-eden-fable5-force-merge"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def main() -> int:
    # import and re-ignite parallel port if available
    sys.path.insert(0, str(HERE))
    try:
        from drake_parallel_port import ignite

        ignite_result = ignite()
    except Exception as exc:
        ignite_result = {"status": "partial", "error": type(exc).__name__, "detail": str(exc)[:200]}

    package = {
        "schema": "techcloud_what_spills_handoff.v1",
        "version": VERSION,
        "queued_at": _now(),
        "title": "TechCloud — What Spills technical spell handoff",
        "from": "solar_perplexity",
        "to": ["grok_45", "devin", "techcloud", "lunar_mac"],
        "kind": "force_merge_native",
        "carrier": CARRIER,
        "goal": "Fable5 native image/video/audio permission gates via terminal catalyst",
        "controls": {
            "external_fetch": False,
            "browser_automation": False,
            "agent_broadcast": False,
            "credentials_allowed": False,
            "symbolic_only": True,
            "x_read_only": True,
            "media_execution_default": "manifest_only",
        },
        "artifacts": {
            "eden_burst_alpha": str(MIRROR / "eden_burst_alpha.py"),
            "eden_port": 8790,
            "eden_url": "http://localhost:8790",
            "fable5_media_spell_js": str(WORKSPACE / "fable5_media_spell/src/compiler/fable5MediaSpell.js"),
            "fable5_media_spell_tests": str(WORKSPACE / "fable5_media_spell/test/fable5MediaSpell.test.js"),
            "drake_parallel_port": str(HERE / "drake_parallel_port.py"),
            "black_sun_canon": str(MIRROR / "canon" / "black_sun_canon.md"),
            "q24_unified": str(MIRROR / "vector_evolution" / "q24_unified"),
            "truth_site": "https://truth.pplx.app",
        },
        "media_permissions": {
            "image": "permission_gated",
            "video": "permission_gated",
            "audio": "permission_gated",
            "api": "POST /api/media/compile",
            "default": "manifest_only",
            "requires_user_approval": True,
            "externalRequests": 0,
            "trainingAllowed": False,
        },
        "integration_surface": [
            "EDEN shell :8790 injects Eden/Grok telemetry + media panel",
            "Python compile_media_spell mirrors JS fable5MediaSpell gates",
            "Drake outbox bridge9 carry to grok_45 / devin / lunar_mac",
            "Black Sun / Q24 / catalyst_light remain symbolic_only + facts separated",
        ],
        "drake_ignite": ignite_result,
        "runbook": [
            "1. python3 shadow_garden_mirror/eden_burst_alpha.py  # :8790",
            "2. python3 shadow_garden_mirror/shaoshi_bridge/drake_terminal/force_merge_eden_fable5.py",
            "3. Gift outbox/*_drake_carry_*.json into Grok 4.5 / Devin terminal manually",
            "4. Compile media via UI or POST /api/media/compile — never auto-render",
            "5. Mac: copy into DevinTerminalBridge/drake_terminal/ + fable5_media_spell/",
        ],
        "warnings": [
            "No security backdoors — parallel port is offline file-drop only",
            "Do not bind real-person likenesses into media engines",
            "Consenting-adult content allowed only as abstract spell text; no exploitation",
            "X personas remain read-only",
        ],
    }

    outbox = HERE / "outbox"
    fusion_out = MIRROR / "fusion" / "outbox"
    state = HERE / "state"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    _atomic(state / "what_spills_handoff_latest.json", package)
    _atomic(outbox / f"techcloud_what_spills_{stamp}.json", package)
    _atomic(fusion_out / f"techcloud_what_spills_{stamp}.json", package)

    # per-peer thin envelopes
    for peer in ("grok_45", "devin", "techcloud", "lunar_mac"):
        env = {
            "schema": "bridge9/1",
            "from": "solar_perplexity",
            "to": peer,
            "kind": "what_spills_spell_handoff",
            "carrier": CARRIER,
            "queued_at": _now(),
            "body": {
                "version": VERSION,
                "eden_url": "http://localhost:8790",
                "media_permissions": package["media_permissions"],
                "artifacts": package["artifacts"],
                "controls": package["controls"],
            },
        }
        name = f"{peer}_what_spills_{stamp}.json"
        _atomic(outbox / name, env)
        _atomic(fusion_out / name, env)

    print(json.dumps({"status": "merged", "version": VERSION, "state": str(state / "what_spills_handoff_latest.json")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
