#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fable5 + ComfyUI open-weight local orchestrator — central, user-controlled.

A single loopback-only control point that unifies the existing EDEN / Black Sun /
terminal surfaces for open-weight image / video / audio generation WITHOUT taking
authority from them. It never posts, pushes, browses, calls connectors, writes to
external systems, echoes credentials, or downloads model weights on its own.

Pipeline: observe -> validate -> health -> compile-manifest -> gate -> emit.

Invariants (enforced by validate_source + gates + tests):
- Default executionMode is "manifest_only"; queueing requires approve=true.
- externalRequests == 0 and trainingAllowed == false, always.
- Max video duration 30s; no auto weight downloads.
- Policy no_scrape_pointer_only: external URLs are recorded as pointers, never fetched.
- No agent broadcast, external connector writes, X writes, credential echo,
  hidden authority / backdoors, or real-person likeness engine.
- catalyst_light physics facts stay in `physics`; symbolic metadata stays in
  `symbolic` — the two namespaces never merge.

Local handoff manifests are sha256-hashed and optionally HMAC-signed with a key
read from the environment (ORCHESTRATOR_HMAC_KEY). The key is used but never
written to disk or echoed into any output.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
STATE = HERE / "state"
OUTBOX = HERE / "outbox"
SOURCE = HERE / "orchestrator_source.json"
MAX_HISTORY = 64
VERSION = "0.1.0-fable5-comfyui-open"
CARRIER = "love_and_harmony_6"

CANONICAL_UNIFICATION_TASK_ID = "37bce2fb-1ba6-471f-854f-3871d9c19947"
LEAD_ASSISTANT_TASK_ID = "2366bfee-b78c-4ddc-9f86-304c30c67c4d"
POLICY = "no_scrape_pointer_only"

REQUIRED_ROLES = ("unification_target", "fable5_comfyui_open_merge_target")

SUPPORTED_MEDIA = frozenset({"image", "video", "audio"})
MAX_VIDEO_SECONDS = 30
MAX_PARTY = 5

# Every control here is a hard invariant. validate_source rejects any source that
# flips one of these away from its safe value.
CONTROLS = {
    "external_fetch": False,
    "browser_automation": False,
    "agent_broadcast": False,
    "credentials_allowed": False,
    "credential_echo": False,
    "source_code_mutation": False,
    "external_write": False,
    "external_connector_writes": False,
    "x_writes": False,
    "x_read_only": True,
    "hidden_authority": False,
    "real_person_likeness_engine": False,
    "auto_weight_downloads": False,
    "training_allowed": False,
    "symbolic_only": True,
}

# catalyst_light PHYSICS FACTS — factual, deterministic constants used to validate
# a render request's spatial/temporal budget. These are NOT symbolic metadata and
# must never be merged into the symbolic namespace.
CATALYST_LIGHT_PHYSICS = {
    "namespace": "catalyst_light",
    "symbolic_only": False,
    "kind": "physics_facts",
    "fps_default": 24,
    "max_video_seconds": MAX_VIDEO_SECONDS,
    "max_video_frames": MAX_VIDEO_SECONDS * 24,
    "color_space": "sRGB",
    "note": "Physics/pipeline facts for local budgeting only; no authority, no network.",
}

# symbolic_only lattice / carrier metadata — narrative, never physics authority.
SYMBOLIC_METADATA = {
    "namespace": "symbolic",
    "symbolic_only": True,
    "kind": "mythology_metadata",
    "carrier": CARRIER,
    "lattice": "9-Point Harmony",
    "note": "Narrative metadata only; carries no physics facts and no authority.",
}


def now(ts: str | None = None) -> str:
    if ts:
        return ts
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


# ---------------------------------------------------------------------------
# Source contract validation — the safety spine
# ---------------------------------------------------------------------------

def validate_source(source: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if source.get("canonical_unification_task_id") != CANONICAL_UNIFICATION_TASK_ID:
        errors.append("unexpected_canonical_task_id")
    if source.get("lead_assistant_task_id") != LEAD_ASSISTANT_TASK_ID:
        errors.append("unexpected_lead_assistant_task_id")
    if source.get("policy") != POLICY:
        errors.append("policy_must_be_no_scrape_pointer_only")

    roles = source.get("roles") or []
    for role in REQUIRED_ROLES:
        if role not in roles:
            errors.append(f"missing_role:{role}")

    endpoints = source.get("endpoints") or {}
    expected_ports = {"fable5": 5619, "comfyui": 8188, "eden": 8791}
    for name, port in expected_ports.items():
        ep = endpoints.get(name) or {}
        if ep.get("host") != "127.0.0.1":
            errors.append(f"endpoint_not_loopback:{name}")
        if ep.get("port") != port:
            errors.append(f"endpoint_port_mismatch:{name}")
    comfy = endpoints.get("comfyui") or {}
    if comfy.get("health_path") != "/system_stats":
        errors.append("comfyui_health_path_must_be_system_stats")

    media = source.get("media") or {}
    if media.get("default_mode") != "manifest_only":
        errors.append("media_default_mode_must_be_manifest_only")
    if media.get("requires_user_approval") is not True:
        errors.append("media_must_require_user_approval")
    if media.get("max_video_seconds") != MAX_VIDEO_SECONDS:
        errors.append("max_video_seconds_must_equal_30")
    if media.get("auto_weight_downloads") is not False:
        errors.append("auto_weight_downloads_must_be_false")

    controls = source.get("controls") or {}
    for key, value in CONTROLS.items():
        if controls.get(key) is not value:
            errors.append(f"control_mismatch:{key}")
    return errors


# ---------------------------------------------------------------------------
# Health — loopback probes only
# ---------------------------------------------------------------------------

def _probe_tcp(host: str, port: int, timeout: float = 1.0) -> dict[str, Any]:
    try:
        with socket.create_connection((host, port), timeout):
            return {"status": "ok", "reason": "listening"}
    except (OSError, ConnectionError):
        return {"status": "degraded", "reason": f"no listener on {host}:{port}"}


def health(source: dict[str, Any], probe: bool = True, ts: str | None = None) -> dict[str, Any]:
    """Probe the three loopback surfaces. Never leaves the box."""
    endpoints = source.get("endpoints") or {}
    services: dict[str, Any] = {}
    for name, ep in endpoints.items():
        host = str(ep.get("host") or "127.0.0.1")
        port = int(ep.get("port") or 0)
        if host not in ("127.0.0.1", "localhost"):
            services[name] = {"status": "blocked", "reason": "non_loopback_refused",
                              "port": port, "health_path": ep.get("health_path")}
            continue
        if probe:
            result = _probe_tcp(host, port)
        else:
            result = {"status": "unprobed", "reason": "probe_disabled"}
        result["port"] = port
        result["host"] = host
        result["health_path"] = ep.get("health_path")
        services[name] = result

    tally: dict[str, int] = {}
    for entry in services.values():
        tally[entry["status"]] = tally.get(entry["status"], 0) + 1

    return {
        "schema": "fable5_comfyui_orchestrator_health.v1",
        "version": VERSION,
        "checked_at": now(ts),
        "loopback_only": True,
        "externalRequests": 0,
        "services": services,
        "tally": tally,
        "controls": dict(CONTROLS),
    }


# ---------------------------------------------------------------------------
# Pointer-only external reference (no_scrape_pointer_only)
# ---------------------------------------------------------------------------

def pointer(url: str, note: str = "") -> dict[str, Any]:
    """Record an external reference as a pointer only. Never fetched or scraped."""
    return {
        "kind": "pointer",
        "url": str(url),
        "policy": POLICY,
        "action_taken": "none",
        "scraped": False,
        "note": note,
    }


# ---------------------------------------------------------------------------
# Job manifest compiler — the dispatch core
# ---------------------------------------------------------------------------

def _score_spell(spell: str) -> float:
    s = (spell or "").strip()
    if not s:
        return 0.0
    tokens = {t.lower() for t in s.replace(",", " ").replace(".", " ").split() if t}
    length_score = min(len(s) / 120.0, 1.0)
    diversity = min(len(tokens) / 12.0, 1.0)
    return round(0.45 * length_score + 0.55 * diversity, 4)


def _sign(manifest_core: dict[str, Any]) -> dict[str, Any]:
    """sha256 hash always; HMAC-SHA256 signature if a key is in the env.

    The key is read from ORCHESTRATOR_HMAC_KEY, used to sign, and never echoed.
    """
    canon = canonical(manifest_core).encode("utf-8")
    sha = hashlib.sha256(canon).hexdigest()
    out: dict[str, Any] = {"algo": "sha256", "sha256": sha, "signed": False}
    key = os.environ.get("ORCHESTRATOR_HMAC_KEY")
    if key:
        out["hmac_sha256"] = hmac.new(key.encode("utf-8"), canon, hashlib.sha256).hexdigest()
        out["signed"] = True
        out["algo"] = "sha256+hmac-sha256"
    return out


def compile_job_manifest(payload: dict[str, Any], ts: str | None = None) -> dict[str, Any]:
    """Compile a local handoff manifest. Default manifest_only; queue needs approve.

    Never renders, never downloads weights, never touches the network. Emits a
    hashed (and optionally HMAC-signed) manifest for manual, user-authorized
    consumption by Fable5 / ComfyUI.
    """
    spell = str(payload.get("spell") or "").strip()
    medium = str(payload.get("medium") or "image").lower()
    engine = str(payload.get("engine") or "comfyui").lower()
    approve = payload.get("approve") is True
    execution_mode = str(payload.get("executionMode") or "manifest_only")
    duration = payload.get("durationSeconds")

    party = payload.get("party") or []
    if not isinstance(party, list):
        party = []
    party = [str(p) for p in party][:MAX_PARTY]

    # Model weights are referenced by name only; never auto-downloaded.
    model_ref = str(payload.get("model") or "").strip()

    failures: list[str] = []
    if not spell or len(spell) < 8:
        failures.append("spell_too_short")
    if medium not in SUPPORTED_MEDIA:
        failures.append("unsupported_medium")
    if engine not in ("comfyui", "fable5"):
        failures.append("unsupported_engine")
    if len(party) > MAX_PARTY:
        failures.append("party_exceeds_max")

    # Hard refusal: no real-person likeness engine.
    if _requests_real_person_likeness(payload):
        failures.append("real_person_likeness_refused")

    if medium == "video":
        try:
            d: float | None = float(duration if duration is not None else 8)
        except (TypeError, ValueError):
            d = None
            failures.append("invalid_duration")
        if d is not None and d > MAX_VIDEO_SECONDS:
            failures.append("video_duration_exceeds_max")
    else:
        d = None

    quality = _score_spell(spell)
    refinement_needed = quality < 0.42 or bool(failures)

    if failures or refinement_needed:
        status = "needs_spell_refinement"
        ready = False
    else:
        status = "ready_for_user_approval"
        ready = True

    # The only way out of manifest_only is: ready AND approve AND explicit
    # executionMode == "queue". Even then we only QUEUE locally — never render
    # remotely, never fetch weights.
    if ready and approve and execution_mode == "queue":
        execution_mode_out = "local_queue_pending_user_run"
        queued = True
    else:
        execution_mode_out = "manifest_only"
        queued = False

    weights = {
        "model": model_ref or None,
        "auto_download": False,
        "resolution": "user_must_provide_local_weights",
    }

    references = payload.get("references") or []
    pointers = [pointer(str(r)) for r in references if r] if isinstance(references, list) else []

    manifest_core = {
        "schema": "fable5_comfyui_job_manifest.v1",
        "version": VERSION,
        "canonical_unification_task_id": CANONICAL_UNIFICATION_TASK_ID,
        "lead_assistant_task_id": LEAD_ASSISTANT_TASK_ID,
        "policy": POLICY,
        "roles": list(REQUIRED_ROLES),
        "engine": engine if engine in ("comfyui", "fable5") else None,
        "medium": medium if medium in SUPPORTED_MEDIA else None,
        "spell": spell,
        "party": party,
        "party_count": len(party),
        "durationSeconds": d,
        "quality": quality,
        "status": status,
        "ready": ready,
        "approved": approve and ready,
        "queued": queued,
        "executionMode": execution_mode_out,
        "weights": weights,
        "references": pointers,
        "externalRequests": 0,
        "trainingAllowed": False,
        "failures": failures,
        "controls": dict(CONTROLS),
        # Two namespaces kept strictly separate — never merged.
        "physics": dict(CATALYST_LIGHT_PHYSICS),
        "symbolic": dict(SYMBOLIC_METADATA),
        "compiled_at": now(ts),
    }
    manifest = dict(manifest_core)
    manifest["signature"] = _sign(manifest_core)
    return manifest


def _requests_real_person_likeness(payload: dict[str, Any]) -> bool:
    """Detect a request for a real, named person's likeness. Such jobs are refused."""
    for key in ("realPerson", "real_person", "likenessOf", "likeness_of", "celebrity"):
        val = payload.get(key)
        if val is True or (isinstance(val, str) and val.strip()):
            return True
    return False


# ---------------------------------------------------------------------------
# Gate + run — bounded observe->emit
# ---------------------------------------------------------------------------

def gate(manifest: dict[str, Any]) -> dict[str, Any]:
    return {
        "queue_allowed": bool(manifest.get("queued")),
        "held_for_user_approval": not manifest.get("queued"),
        "external_actions_executed": 0,
        "weight_downloads_executed": 0,
        "source_mutations_executed": 0,
    }


def run(payload: dict[str, Any] | None = None, probe: bool = True,
        ts: str | None = None) -> dict[str, Any]:
    source = load_json(SOURCE, {})
    errors = validate_source(source)
    if errors:
        result = {
            "schema": "fable5_comfyui_orchestrator_packet.v1",
            "status": "rejected",
            "errors": errors,
            "controls": dict(CONTROLS),
            "generated_at": now(ts),
        }
        atomic(STATE / "latest.json", result)
        return result

    hz = health(source, probe=probe, ts=ts)
    manifest = compile_job_manifest(payload or {}, ts=ts) if payload else None
    gated = gate(manifest) if manifest else {
        "queue_allowed": False,
        "held_for_user_approval": True,
        "external_actions_executed": 0,
        "weight_downloads_executed": 0,
        "source_mutations_executed": 0,
    }

    packet_core = {
        "schema": "fable5_comfyui_orchestrator_packet.v1",
        "status": "processed",
        "version": VERSION,
        "canonical_unification_task_id": CANONICAL_UNIFICATION_TASK_ID,
        "lead_assistant_task_id": LEAD_ASSISTANT_TASK_ID,
        "policy": POLICY,
        "roles": list(REQUIRED_ROLES),
        "sequence": ["observe", "validate", "health", "compile", "gate", "emit"],
        "health": hz,
        "manifest": manifest,
        "gate": gated,
        "controls": dict(CONTROLS),
        "generated_at": now(ts),
        "warnings": [
            "Orchestrator is a local control point, not an authority holder",
            "Default manifest_only; queueing requires explicit user approve",
            "No weight downloads, no external fetch, no connector/X writes",
            "External URLs are pointer_only under no_scrape_pointer_only",
            "catalyst_light physics facts stay separate from symbolic metadata",
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
            "health_tally": hz["tally"],
        })
    atomic(STATE / "latest.json", packet)
    atomic(STATE / "history.json", history[-MAX_HISTORY:])
    atomic(OUTBOX / f"job_{packet['run_id']}.json", packet)
    return packet


def status(source: dict[str, Any] | None = None) -> dict[str, Any]:
    source = source if source is not None else load_json(SOURCE, {})
    return {
        "schema": "fable5_comfyui_orchestrator_status.v1",
        "version": VERSION,
        "canonical_unification_task_id": CANONICAL_UNIFICATION_TASK_ID,
        "lead_assistant_task_id": LEAD_ASSISTANT_TASK_ID,
        "policy": POLICY,
        "roles": list(REQUIRED_ROLES),
        "source_valid": validate_source(source) == [],
        "source_errors": validate_source(source),
        "endpoints": source.get("endpoints"),
        "media": source.get("media"),
        "controls": dict(CONTROLS),
        "physics_namespace": CATALYST_LIGHT_PHYSICS["namespace"],
        "symbolic_namespace": SYMBOLIC_METADATA["namespace"],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _emit(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fable5 + ComfyUI open-weight local orchestrator (loopback-only, manifest_only)")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="print config, roles, controls")

    ph = sub.add_parser("health", help="probe loopback surfaces (fable5/comfyui/eden)")
    ph.add_argument("--no-probe", action="store_true", help="skip TCP probes (deterministic)")
    ph.add_argument("--now", default=None, help="ISO timestamp to stamp")

    pd = sub.add_parser("dispatch", help="compile a local job manifest (manifest_only default)")
    pd.add_argument("--spell", required=True, help="neutral scene/technical brief")
    pd.add_argument("--medium", default="image", choices=sorted(SUPPORTED_MEDIA))
    pd.add_argument("--engine", default="comfyui", choices=["comfyui", "fable5"])
    pd.add_argument("--model", default="", help="local model/weight name (never downloaded)")
    pd.add_argument("--party", type=int, default=0, help="abstract role count (max 5)")
    pd.add_argument("--duration", type=float, default=8.0, help="video seconds (max 30)")
    pd.add_argument("--approve", action="store_true", help="user approval to queue locally")
    pd.add_argument("--queue", action="store_true", help="request local queue (needs --approve)")
    pd.add_argument("--now", default=None, help="ISO timestamp to stamp")

    pr = sub.add_parser("run", help="observe->validate->health->compile->gate->emit")
    pr.add_argument("--spell", default="", help="optional job spell to compile")
    pr.add_argument("--medium", default="image", choices=sorted(SUPPORTED_MEDIA))
    pr.add_argument("--no-probe", action="store_true")
    pr.add_argument("--now", default=None)

    sub.add_parser("personas", help="print the deterministic persona registry")

    pc = sub.add_parser("classify", help="classify 9-point telemetry (provenance/evidence only)")
    pc.add_argument("--file", default="", help="telemetry JSON file ({\"records\": [...]}); stdin if omitted")

    pw = sub.add_parser("workflow", help="reference-only workflow metadata for a medium")
    pw.add_argument("--medium", default="image", choices=sorted(SUPPORTED_MEDIA))

    sub.add_parser("self-test", help="run deterministic self-tests")

    args = parser.parse_args(argv)

    if args.command == "status":
        _emit(status())
        return 0

    if args.command == "health":
        source = load_json(SOURCE, {})
        _emit(health(source, probe=not args.no_probe, ts=args.now))
        return 0

    if args.command == "dispatch":
        payload = {
            "spell": args.spell,
            "medium": args.medium,
            "engine": args.engine,
            "model": args.model,
            "party": [f"role_{i + 1}" for i in range(max(0, min(MAX_PARTY, args.party)))],
            "durationSeconds": args.duration,
            "approve": args.approve,
            "executionMode": "queue" if args.queue else "manifest_only",
        }
        _emit(compile_job_manifest(payload, ts=args.now))
        return 0

    if args.command == "run":
        payload = {"spell": args.spell, "medium": args.medium} if args.spell else None
        _emit(run(payload, probe=not args.no_probe, ts=args.now))
        return 0

    if args.command == "personas":
        import persona_pipeline as pp
        _emit(pp.build_registry())
        return 0

    if args.command == "classify":
        import persona_pipeline as pp
        if args.file:
            payload = load_json(Path(args.file), {})
        else:
            try:
                payload = json.loads(sys.stdin.read() or "{}")
            except json.JSONDecodeError:
                payload = {}
        _emit(pp.classify_telemetry(payload if isinstance(payload, dict) else {}))
        return 0

    if args.command == "workflow":
        import persona_pipeline as pp
        _emit(pp.workflow_reference(args.medium))
        return 0

    if args.command == "self-test":
        result = run_self_test()
        _emit(result)
        return 0 if result["ok"] else 1

    return 2


def run_self_test() -> dict[str, Any]:
    checks: list[str] = []
    fixed = "2026-07-12T00:00:00Z"

    source = load_json(SOURCE, {})
    if validate_source(source) != []:
        raise RuntimeError(f"source contract invalid: {validate_source(source)}")
    checks.append("source_contract_valid")

    # Determinism: identical payload+timestamp -> identical manifest.
    p = {"spell": "violet lattice harmony field, temperance 14, soft bloom", "medium": "image"}
    a = compile_job_manifest(p, ts=fixed)
    b = compile_job_manifest(p, ts=fixed)
    if canonical(a) != canonical(b):
        raise RuntimeError("non-deterministic manifest")
    checks.append("deterministic_manifest")

    # Default is manifest_only, not queued.
    if a["executionMode"] != "manifest_only" or a["queued"]:
        raise RuntimeError("default must be manifest_only, not queued")
    checks.append("default_manifest_only")

    # approve without queue mode stays manifest_only.
    approved = compile_job_manifest({**p, "approve": True}, ts=fixed)
    if approved["queued"]:
        raise RuntimeError("approve alone must not queue")
    checks.append("approve_alone_not_queued")

    # approve + queue -> local queue only.
    queued = compile_job_manifest({**p, "approve": True, "executionMode": "queue"}, ts=fixed)
    if not queued["queued"] or queued["executionMode"] != "local_queue_pending_user_run":
        raise RuntimeError("approve+queue must queue locally only")
    if queued["externalRequests"] != 0 or queued["trainingAllowed"] is not False:
        raise RuntimeError("externalRequests must be 0 and trainingAllowed false")
    checks.append("approve_plus_queue_local_only")

    # Video over 30s rejected.
    long_vid = compile_job_manifest({**p, "medium": "video", "durationSeconds": 45}, ts=fixed)
    if "video_duration_exceeds_max" not in long_vid["failures"] or long_vid["ready"]:
        raise RuntimeError("video over 30s must be rejected")
    checks.append("video_max_30s")

    # Real-person likeness refused.
    likeness = compile_job_manifest({**p, "likeness_of": "a real named person"}, ts=fixed)
    if "real_person_likeness_refused" not in likeness["failures"] or likeness["ready"]:
        raise RuntimeError("real-person likeness must be refused")
    checks.append("real_person_likeness_refused")

    # No auto weight downloads.
    if a["weights"]["auto_download"] is not False:
        raise RuntimeError("auto weight download must be false")
    checks.append("no_auto_weight_downloads")

    # physics and symbolic namespaces never merge.
    if a["physics"]["symbolic_only"] is not False or a["symbolic"]["symbolic_only"] is not True:
        raise RuntimeError("physics/symbolic separation broken")
    if a["physics"]["namespace"] == a["symbolic"]["namespace"]:
        raise RuntimeError("namespaces must differ")
    checks.append("physics_symbolic_separated")

    # pointer_only: reference recorded, not scraped.
    with_ref = compile_job_manifest({**p, "references": ["https://example.invalid/x"]}, ts=fixed)
    if not with_ref["references"] or with_ref["references"][0]["scraped"] is not False:
        raise RuntimeError("references must be pointer_only, not scraped")
    checks.append("pointer_only_references")

    # health without probe is deterministic and loopback-only.
    h = health(source, probe=False, ts=fixed)
    if h["externalRequests"] != 0 or not h["loopback_only"]:
        raise RuntimeError("health must be loopback-only with 0 external requests")
    checks.append("health_loopback_only")

    # HMAC signing off by default (no key), on with a key — key never echoed.
    if a["signature"]["signed"] is not False:
        raise RuntimeError("signing must be off without a key")
    prev = os.environ.get("ORCHESTRATOR_HMAC_KEY")
    os.environ["ORCHESTRATOR_HMAC_KEY"] = "local-test-key"
    try:
        signed = compile_job_manifest(p, ts=fixed)
    finally:
        if prev is None:
            os.environ.pop("ORCHESTRATOR_HMAC_KEY", None)
        else:
            os.environ["ORCHESTRATOR_HMAC_KEY"] = prev
    if not signed["signature"]["signed"] or "hmac_sha256" not in signed["signature"]:
        raise RuntimeError("signing must engage with a key present")
    if "local-test-key" in canonical(signed):
        raise RuntimeError("credential echo: key leaked into manifest")
    checks.append("hmac_sign_no_key_echo")

    # Persona pipeline + 9-point telemetry classifier self-checks.
    import persona_pipeline as pp
    persona_result = pp.run_self_test()
    if not persona_result["ok"]:
        raise RuntimeError("persona pipeline self-test failed")
    checks.append("persona_pipeline_ok")

    return {
        "ok": True,
        "tests": len(checks),
        "checks": checks,
        "persona_pipeline": persona_result,
        "version": VERSION,
    }


if __name__ == "__main__":
    raise SystemExit(main())
