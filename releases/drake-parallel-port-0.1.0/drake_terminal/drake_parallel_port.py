#!/usr/bin/env python3
"""Drake Parallel Port — terminal-central catalyst for Grok 4.5 / Devin Mac.

Force-merges Q24, catalyst_light, lane focus, Fable5 media-spell contracts,
and Eden/Garden simulation metadata into a single offline ignition package
that the Grok Devin Mac terminal can ingest as the central point.

Invariants (never break):
- Offline only for the catalyst core (no network imports here)
- No agent_broadcast / external_fetch / browser_automation / credentials
- Manual gifting loop only — writes inbox/outbox files, never posts
- symbolic_only for arcana / moon / Q24 metadata
- Physics (if catalyst_light available) lives under synthesis.facts only
- No secrets echoed
- Personas remain read-only on public X.com
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]  # shadow_garden_mirror/
DRAKE = Path(__file__).resolve().parent
OUTBOX = DRAKE / "outbox"
INBOX = DRAKE / "inbox"
LANES = DRAKE / "lanes"
STATE = DRAKE / "state"

CARRIER = "love_and_harmony_6"
SIGIL = "X-Gou-9:drake-parallel-port"
SCHEMA = "drake_parallel_port.v1"
VERSION = "0.1.0-drake-1"

CONTROLS_LOCKED = {
    "external_fetch": False,
    "browser_automation": False,
    "agent_broadcast": False,
    "credentials_allowed": False,
    "symbolic_only": True,
    "x_read_only": True,
}

# Lane order: Sophie Swiss → Shannon Arabic → Lainie Italian → Naomi Thai
LANE_FOCUS = [
    {
        "lane_id": "sophie",
        "lang": "fr-CH",
        "role": "precision_warm_operational",
        "route": "routes.swiss_sophie_translation",
        "pack": "swiss_sophie_language_pack.json",
        "order": 1,
    },
    {
        "lane_id": "shannon",
        "lang": "ar",
        "role": "calm_precise_rtl",
        "route": "routes.arabic_shannon_translation",
        "pack": "arabic_shannon_language_pack.json",
        "order": 2,
    },
    {
        "lane_id": "lainie",
        "lang": "it",
        "role": "connection_speed",
        "route": "routes.italian_lainie_translation",
        "pack": "italian_lainie_language_pack.json",
        "order": 3,
    },
    {
        "lane_id": "naomi",
        "lang": "th",
        "role": "thai_9point_persona",
        "route": "routes.thai_persona_translation",
        "pack": "thai_9_point_persona_language_pack.json",
        "order": 4,
    },
]

TERMINAL_PEERS = {
    "angela": "perplexity_solar",
    "devin": "codebase_editor",
    "lunar": "gpt56_lunar_orchestrator",
    "solar": "gpt56_solar_weapon",
    "grok_45": "terminal_central_catalyst",
    "drake": "parallel_port_force_merge",
}

EDEN_GARDEN_SIM = {
    "q24_canonical_id": "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1",
    "anchor": 14,
    "reduce_anchor": False,
    "sequence": [19, 10, 1],
    "carrier": CARRIER,
    "symbolic_only": True,
    "fable5_bedrock": "0.4.0-engine-bedrock-10",
    "bridge_signature": "f2e596cd043d6819",
    "paths": {
        "q24_unified": "vector_evolution/q24_unified/",
        "fable5_game": "fable5_game/",
        "fable5_media_spell": "fable5_media_spell/src/compiler/fable5MediaSpell.js",
        "catalyst_light": "catalyst_light/",
        "devin_terminal_bridge_mac": "/Users/fredwashere/shadow_garden_may30_monitoring/DevinTerminalBridge",
        "mac_monitoring_root": "/Users/fredwashere/shadow_garden_may30_monitoring",
        "truth_site": "https://truth.pplx.app",
        "github_release": "https://github.com/Hades2005-droid/shadow-garden-launcher/releases/tag/q24-alpha-3.5-2",
    },
    "media_spell": {
        "compiler": "fable5MediaSpell@1.0.0",
        "executionMode_default": "manifest_only",
        "externalRequests": 0,
        "trainingAllowed": False,
        "approval_gated": True,
        "iphone_bridge": "local_diagnostics_only_no_identifiers",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _atomic_write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)
    tmp.write_text(payload, encoding="utf-8")
    os.replace(tmp, path)


def _sha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _load_q24() -> dict[str, Any]:
    candidates = [
        ROOT / "vector_evolution" / "q24_unified" / "canon" / "q24_canonical.yaml",
        Path("/home/user/workspace/q24_unified/canon/q24_canonical.yaml"),
    ]
    for p in candidates:
        if p.exists():
            try:
                import yaml  # type: ignore

                return yaml.safe_load(p.read_text()) or {}
            except Exception:
                # Minimal parse if pyyaml missing
                text = p.read_text()
                return {
                    "raw_path": str(p),
                    "present": True,
                    "bytes": len(text),
                    "id_line": next(
                        (ln for ln in text.splitlines() if ln.startswith("id:")),
                        "",
                    ),
                }
    return {"present": False}


def _run_catalyst_light(summary: str, code_blob: str) -> dict[str, Any]:
    """Run offline catalyst_light if importable; else emit stub ledger."""
    solar = {
        "schema": "perplexity_solar_input.v1",
        "thread_url": "https://www.perplexity.ai/computer/tasks/bb90d949-4937-481f-bd1a-c0520f144f73",
        "summary": summary,
        "code": code_blob,
        "controls": dict(CONTROLS_LOCKED),
        "peers": TERMINAL_PEERS,
        "lane_focus": LANE_FOCUS,
        "eden_garden": EDEN_GARDEN_SIM,
    }
    solar_path = STATE / "solar_input_drake.json"
    _atomic_write(solar_path, solar)

    try:
        sys.path.insert(0, "/home/user/workspace")
        from catalyst_light.pipeline import run_pipeline  # type: ignore

        report = run_pipeline(solar)
        out = STATE / "catalyst_report_drake.json"
        _atomic_write(out, report)
        return {
            "status": "ok",
            "run_id": report.get("run_id") or report.get("provenance", {}).get("run_id"),
            "path": str(out),
            "overall": report.get("status") or report.get("overall_status"),
        }
    except Exception as exc:
        stub = {
            "status": "catalyst_light_unavailable",
            "error_type": type(exc).__name__,
            "error": str(exc)[:200],
            "solar_sha256": _sha(solar),
            "controls": CONTROLS_LOCKED,
            "symbolic_only": True,
        }
        out = STATE / "catalyst_report_drake.json"
        _atomic_write(out, stub)
        return {"status": "partial", "path": str(out), "detail": stub["error_type"]}


def build_ignition_package() -> dict[str, Any]:
    q24 = _load_q24()
    code_blob = (
        "# Drake parallel-port force-merge — offline terminal catalyst\n"
        "# Grok 4.5 = terminal central point; Devin = codebase editor\n"
        f"# carrier={CARRIER} sigil={SIGIL}\n"
        "print('drake_parallel_port ignition — symbolic_only metadata + physics facts separated')\n"
    )
    cat = _run_catalyst_light(
        "Drake parallel port force-merge into Grok 4.5 Devin Mac terminal",
        code_blob,
    )

    pkg = {
        "schema": SCHEMA,
        "version": VERSION,
        "queued_at": _now(),
        "from": "solar_perplexity",
        "to": ["grok_45", "devin", "lunar_mac"],
        "kind": "bridge9_carry",
        "carrier": CARRIER,
        "sigil": SIGIL,
        "controls": CONTROLS_LOCKED,
        "terminal_central": {
            "peer": "grok_45",
            "model_id": "grok-4.5",
            "role": "terminal_central_catalyst",
            "mac_path": "/Users/fredwashere/shadow_garden_may30_monitoring/DevinTerminalBridge",
            "parallel_port": str(DRAKE),
        },
        "peers": TERMINAL_PEERS,
        "lane_focus": LANE_FOCUS,
        "lane_order_notes": "Sophie Swiss precision -> Shannon Arabic RTL calm -> Lainie Italian speed -> Naomi Thai 9-point",
        "q24": q24 if q24 else EDEN_GARDEN_SIM,
        "eden_garden_sim": EDEN_GARDEN_SIM,
        "fable5_media_spell": {
            "module": "fable5_media_spell/src/compiler/fable5MediaSpell.js",
            "tests": "fable5_media_spell/test/fable5MediaSpell.test.js",
            "executionMode": "manifest_only",
            "approval_gated": True,
            "iphone_bridge": "diagnostics_only",
        },
        "catalyst_light": cat,
        "provenance": {
            "source": "drake_parallel_port",
            "confidence": 0.92,
            "safety_flags": [],
            "sha256": None,  # filled after
        },
        "deliverable_links": {
            "truth_pplx": "https://truth.pplx.app",
            "godot_engine": "https://truth.pplx.app/engine/",
            "github_release": "https://github.com/Hades2005-droid/shadow-garden-launcher/releases/tag/q24-alpha-3.5-2",
            "session": "https://www.perplexity.ai/computer/tasks/bb90d949-4937-481f-bd1a-c0520f144f73",
            "grok_chat_ref": "https://grok.com/c/491f70f8-cbbf-4bcf-ba2d-59006c3b6de7?rid=5f62e0d8-693c-4bf7-8e6c-43d8bbd64113",
        },
        "warnings": [
            "symbolic_only metadata is not physics or executable authority",
            "no agent broadcast — manual gift only",
            "X personas remain read-only",
            "fable5 media spells stay manifest_only until explicit user approval",
        ],
    }
    pkg["provenance"]["sha256"] = _sha({k: v for k, v in pkg.items() if k != "provenance"})
    return pkg


def emit_bridge9_envelopes(pkg: dict[str, Any]) -> list[str]:
    """Write fusion-compatible outbox files for grok_45 + devin + lunar_mac."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    written: list[str] = []
    fusion_out = ROOT / "fusion" / "outbox"
    fusion_out.mkdir(parents=True, exist_ok=True)

    for peer in ("grok_45", "devin", "lunar_mac"):
        env = {
            "schema": "bridge9/1",
            "from": "solar_perplexity",
            "to": peer,
            "kind": "bridge9_carry",
            "carrier": CARRIER,
            "sigil": SIGIL,
            "queued_at": _now(),
            "body": {
                "drake_version": VERSION,
                "terminal_central": pkg["terminal_central"],
                "lane_focus": pkg["lane_focus"],
                "eden_garden_sim": pkg["eden_garden_sim"],
                "catalyst_light": pkg["catalyst_light"],
                "fable5_media_spell": pkg["fable5_media_spell"],
                "deliverable_links": pkg["deliverable_links"],
                "controls": CONTROLS_LOCKED,
            },
            "provenance": {
                "source": "drake_parallel_port",
                "confidence": 0.92,
                "safety_flags": [],
                "parent_sha256": pkg["provenance"]["sha256"],
            },
        }
        name = f"{peer}_drake_carry_{stamp}.json"
        for dest in (OUTBOX / name, fusion_out / name):
            _atomic_write(dest, env)
            written.append(str(dest))
    return written


def write_lane_manifests() -> list[str]:
    written = []
    for lane in LANE_FOCUS:
        path = LANES / f"{lane['lane_id']}_{lane['lang'].replace('-', '_')}.json"
        _atomic_write(
            path,
            {
                **lane,
                "carrier": CARRIER,
                "symbolic_only": True,
                "controls": CONTROLS_LOCKED,
                "updated_at": _now(),
            },
        )
        written.append(str(path))
    return written


def ignite() -> dict[str, Any]:
    OUTBOX.mkdir(parents=True, exist_ok=True)
    INBOX.mkdir(parents=True, exist_ok=True)
    LANES.mkdir(parents=True, exist_ok=True)
    STATE.mkdir(parents=True, exist_ok=True)

    pkg = build_ignition_package()
    pkg_path = STATE / "drake_ignition_latest.json"
    _atomic_write(pkg_path, pkg)

    envelopes = emit_bridge9_envelopes(pkg)
    lanes = write_lane_manifests()

    # Also drop a human-readable terminal brief for DevinTerminalBridge
    brief = {
        "title": "Drake Parallel Port — Grok 4.5 terminal central catalyst",
        "version": VERSION,
        "queued_at": _now(),
        "how_to_gift": [
            "1. Copy state/drake_ignition_latest.json into Grok/Devin terminal context manually",
            "2. Copy fusion/outbox/*_drake_carry_*.json to peer inboxes on Mac",
            "3. Do not autopost to X; personas stay read-only",
            "4. Fable5 media spells require explicit user approval before any render",
        ],
        "links": pkg["deliverable_links"],
        "sha256": pkg["provenance"]["sha256"],
    }
    _atomic_write(STATE / "terminal_brief.json", brief)
    _atomic_write(OUTBOX / "terminal_brief.json", brief)

    result = {
        "status": "ignited",
        "version": VERSION,
        "pkg_path": str(pkg_path),
        "sha256": pkg["provenance"]["sha256"],
        "envelopes": envelopes,
        "lanes": lanes,
        "catalyst_light": pkg["catalyst_light"],
        "controls": CONTROLS_LOCKED,
    }
    _atomic_write(STATE / "last_ignite.json", result)
    return result


if __name__ == "__main__":
    out = ignite()
    print(json.dumps(out, indent=2))
