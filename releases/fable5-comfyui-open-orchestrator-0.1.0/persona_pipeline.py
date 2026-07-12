#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Deterministic, local-only persona pipeline + 9-point telemetry classifier.

Extends the Fable5 + ComfyUI orchestrator with:
- A stable persona registry that preserves every persona node discovered in repo
  config and guarantees stable entries for Minnie, Sarah, and Sophie. No
  biographies or relationships are ever invented: `biography` is always null and
  `relationships` is always []. Persona metadata is symbolic_only.
- A 9-point telemetry classifier that ranks nodes into
  primordial / canonical / corroborated / provisional / quarantine using only
  provenance + verifiable evidence. Mystical / character labels (sovereign,
  lattice, 11D, grok, makima, seiko, kaguya) are symbolic_only and NEVER used to
  rank a record.
- Opaque read-only pointers for X.com / Instagram: no scraping, fetch, posting,
  liking, replying, following, DMs, or credential use — ever.
- Reference-only ComfyUI/EDEN workflow metadata (schema
  shadow_garden.9point_node_telemetry.v1) for image Flux.1 Dev, video Wan 2.2,
  audio ACE-Step 1.5. Runtime hosts are loopback-only, model downloads are false,
  unknown custom nodes never execute, and queueing needs explicit user approval
  plus a reviewed workflow.

Everything here is deterministic (no clocks, no randomness in the core outputs)
and network-free. It reuses the orchestrator's controls, hashing, and signing.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

# Load the orchestrator as a sibling module (works for `python3` and importlib).
try:
    import orchestrator as orch  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - importlib fallback
    _spec = importlib.util.spec_from_file_location("orchestrator", HERE / "orchestrator.py")
    orch = importlib.util.module_from_spec(_spec)  # type: ignore
    assert _spec and _spec.loader
    _spec.loader.exec_module(orch)  # type: ignore

PERSONA_SOURCE = HERE / "personas_source.json"
TELEMETRY_SCHEMA = HERE / "node_telemetry_schema.json"

CLASSIFICATION_TIERS = ("primordial", "canonical", "corroborated", "provisional", "quarantine")
GUARANTEED_PERSONAS = ("minnie", "sarah", "sophie")

# Evidence kinds that can be independently verified on this box. An external
# pointer (X/Instagram/etc.) is deliberately NOT trustable evidence.
TRUSTED_EVIDENCE_KINDS = frozenset({"loopback_probe", "repo_config", "user_attestation"})

# Hosts that opaque pointers refer to — read-only, never contacted.
OPAQUE_POINTER_HOSTS = ("x.com", "twitter.com", "instagram.com")

# Every social action is refused. This is the full prohibition surface.
SOCIAL_ACTIONS_REFUSED = {
    "scrape": False,
    "fetch": False,
    "post": False,
    "like": False,
    "reply": False,
    "follow": False,
    "dm": False,
    "credential_use": False,
}


def _norm(value: Any) -> str:
    return str(value or "").strip().lower()


# ---------------------------------------------------------------------------
# Opaque, read-only social pointers
# ---------------------------------------------------------------------------

def opaque_pointer(url: str) -> dict[str, Any]:
    """An opaque read-only pointer. The URL is stored verbatim; nothing is fetched.

    All social actions (scrape/fetch/post/like/reply/follow/dm/credentials) are
    hard-false. Applies to X.com and Instagram links per the no-scrape policy.
    """
    host = ""
    try:
        host = urlparse(str(url)).netloc.lower()
    except (ValueError, AttributeError):
        host = ""
    host = host[4:] if host.startswith("www.") else host
    return {
        "kind": "opaque_pointer",
        "url": str(url),
        "host": host,
        "policy": orch.POLICY,
        "opaque": True,
        "read_only": True,
        "action_taken": "none",
        "actions": dict(SOCIAL_ACTIONS_REFUSED),
        "is_social": any(host == h or host.endswith("." + h) for h in OPAQUE_POINTER_HOSTS),
    }


# ---------------------------------------------------------------------------
# Persona registry — preserves discovered nodes, guarantees Minnie/Sarah/Sophie
# ---------------------------------------------------------------------------

def _empty_persona(pid: str, discovered_in: list[str]) -> dict[str, Any]:
    # No biography or relationships are ever invented.
    return {
        "id": pid,
        "symbolic_only": True,
        "discovered_in": sorted(set(discovered_in)),
        "biography": None,
        "relationships": [],
        "pointers": [],
        "authority": False,
    }


def build_registry(source: dict[str, Any] | None = None) -> dict[str, Any]:
    """Build the deterministic persona registry from the source file.

    Preserves every discovered node and guarantees Minnie/Sarah/Sophie exist.
    Output is sorted by id and carries a stable content hash.
    """
    source = source if source is not None else orch.load_json(PERSONA_SOURCE, {})
    nodes: dict[str, dict[str, Any]] = {}

    for entry in source.get("discovered_nodes") or []:
        pid = _norm(entry.get("id"))
        if not pid:
            continue
        discovered = list(entry.get("discovered_in") or [])
        if pid in nodes:
            nodes[pid]["discovered_in"] = sorted(
                set(nodes[pid]["discovered_in"]) | set(discovered))
        else:
            nodes[pid] = _empty_persona(pid, discovered)

    guaranteed = [_norm(g) for g in (source.get("guaranteed_nodes") or GUARANTEED_PERSONAS)]
    guaranteed_only = source.get("guaranteed_only_source") or {}
    for pid in guaranteed:
        if pid not in nodes:
            extra = list(guaranteed_only.get(pid) or ["revision_request_guarantee"])
            nodes[pid] = _empty_persona(pid, extra)
        nodes[pid]["guaranteed"] = True

    for pid in nodes:
        nodes.setdefault(pid, {})
        nodes[pid].setdefault("guaranteed", pid in guaranteed)

    ordered = [nodes[pid] for pid in sorted(nodes)]
    registry_core = {
        "schema": "fable5_comfyui_persona_registry.v1",
        "policy": orch.POLICY,
        "symbolic_only": True,
        "count": len(ordered),
        "guaranteed": sorted(set(guaranteed)),
        "symbolic_bindings": source.get("symbolic_bindings") or {},
        "personas": ordered,
        "controls": dict(orch.CONTROLS),
    }
    registry = dict(registry_core)
    registry["signature"] = orch._sign(registry_core)
    return registry


def registry_guarantees_hold(registry: dict[str, Any]) -> bool:
    ids = {p["id"] for p in registry.get("personas") or []}
    if not all(g in ids for g in GUARANTEED_PERSONAS):
        return False
    for p in registry.get("personas") or []:
        # No invented biography or relationships, ever.
        if p.get("biography") is not None or p.get("relationships"):
            return False
    return True


# ---------------------------------------------------------------------------
# 9-point telemetry classifier — provenance + evidence only
# ---------------------------------------------------------------------------

def _trusted_evidence_count(record: dict[str, Any]) -> int:
    seen: set[str] = set()
    for ev in record.get("evidence") or []:
        if not isinstance(ev, dict):
            continue
        kind = _norm(ev.get("kind"))
        if kind in TRUSTED_EVIDENCE_KINDS and ev.get("verified") is True:
            # Independence keyed by (kind, ref) so duplicates don't inflate rank.
            seen.add(f"{kind}:{_norm(ev.get('ref'))}")
    return len(seen)


def classify_record(record: dict[str, Any]) -> dict[str, Any]:
    """Classify a single telemetry record by provenance + verifiable evidence.

    Mystical/character labels are stripped into `symbolic_labels` and never
    affect the tier. Prohibited flags force quarantine.
    """
    node_id = _norm(record.get("node_id"))
    flags = record.get("flags") or {}
    provenance = record.get("provenance") or {}
    labels = [str(l) for l in (record.get("labels") or [])]

    reasons: list[str] = []

    # Hard quarantine conditions — safety first, evidence irrelevant.
    if flags.get("real_person_likeness") is True:
        reasons.append("real_person_likeness_flag")
    if flags.get("credential") is True:
        reasons.append("credential_flag")
    if flags.get("conflict") is True:
        reasons.append("evidence_conflict")

    if reasons:
        tier = "quarantine"
        trusted = _trusted_evidence_count(record)
    else:
        trusted = _trusted_evidence_count(record)
        in_repo = provenance.get("in_repo_config") is True
        first_party = provenance.get("first_party") is True
        hashed = provenance.get("hashed") is True

        if trusted >= 2:
            tier = "corroborated"
            reasons.append(f"trusted_evidence={trusted}")
            if in_repo:
                tier = "canonical"
                reasons.append("in_repo_config")
                if first_party and hashed:
                    tier = "primordial"
                    reasons.append("first_party+hashed")
        elif trusted == 1:
            tier = "provisional"
            reasons.append("trusted_evidence=1")
        else:
            tier = "provisional"
            reasons.append("no_trusted_evidence")

    return {
        "node_id": node_id,
        "tier": tier,
        "trusted_evidence": trusted,
        "reasons": reasons,
        # Labels are preserved but explicitly marked as non-ranking metadata.
        "symbolic_labels": labels,
        "symbolic_only_labels_ignored_for_ranking": True,
    }


def classify_telemetry(payload: dict[str, Any]) -> dict[str, Any]:
    """Classify a batch of telemetry records against the v1 schema. Deterministic."""
    records = payload.get("records") or []
    classified = [classify_record(r) for r in records if isinstance(r, dict)]
    classified.sort(key=lambda c: (c["node_id"], c["tier"]))

    tally = {tier: 0 for tier in CLASSIFICATION_TIERS}
    for c in classified:
        tally[c["tier"]] = tally.get(c["tier"], 0) + 1

    result_core = {
        "schema": "shadow_garden.9point_node_telemetry.classified.v1",
        "source_schema": "shadow_garden.9point_node_telemetry.v1",
        "policy": orch.POLICY,
        "tiers": list(CLASSIFICATION_TIERS),
        "ranking_rule": "provenance + verifiable evidence only; mystical/character labels never rank",
        "count": len(classified),
        "tally": tally,
        "classified": classified,
        "externalRequests": 0,
        "controls": dict(orch.CONTROLS),
    }
    result = dict(result_core)
    result["signature"] = orch._sign(result_core)
    return result


# ---------------------------------------------------------------------------
# Reference-only workflow metadata + review gate
# ---------------------------------------------------------------------------

def workflow_reference(medium: str, schema: dict[str, Any] | None = None) -> dict[str, Any]:
    schema = schema if schema is not None else orch.load_json(TELEMETRY_SCHEMA, {})
    workflows = schema.get("workflows") or {}
    runtime = schema.get("runtime") or {}
    wf = workflows.get(_norm(medium))
    if not wf:
        return {"error": "unknown_medium", "medium": medium,
                "supported": sorted(workflows.keys())}
    return {
        "schema": schema.get("schema"),
        "medium": _norm(medium),
        "workflow": dict(wf),
        "reference_only": True,
        "model_downloads": False,
        "allowed_hosts": runtime.get("allowed_hosts") or ["127.0.0.1", "localhost"],
        "unknown_custom_nodes_execute": False,
        "queue_requires_user_approval": True,
        "queue_requires_reviewed_workflow": True,
    }


def review_workflow(workflow: dict[str, Any], approve: bool = False,
                    schema: dict[str, Any] | None = None) -> dict[str, Any]:
    """Gate a concrete ComfyUI/EDEN workflow. Queue only if fully safe + approved.

    Refuses unknown custom nodes, non-loopback hosts, any model download request,
    or a workflow not explicitly marked reviewed. Never executes anything.
    """
    schema = schema if schema is not None else orch.load_json(TELEMETRY_SCHEMA, {})
    runtime = schema.get("runtime") or {}
    allowlist = set(runtime.get("known_node_allowlist") or [])
    allowed_hosts = set(runtime.get("allowed_hosts") or ["127.0.0.1", "localhost"])

    blockers: list[str] = []

    nodes = workflow.get("nodes") or []
    unknown_nodes = sorted({str(n.get("class_type"))
                            for n in nodes if isinstance(n, dict)
                            and str(n.get("class_type")) not in allowlist})
    if unknown_nodes:
        blockers.append("unknown_custom_nodes")

    hosts = [str(h) for h in (workflow.get("hosts") or [])]
    non_loopback = sorted({h for h in hosts
                           if urlparse(h if "//" in h else "//" + h).hostname
                           not in allowed_hosts})
    if non_loopback:
        blockers.append("non_loopback_host")

    if workflow.get("model_downloads") is True:
        blockers.append("model_download_requested")

    reviewed = workflow.get("reviewed") is True
    if not reviewed:
        blockers.append("workflow_not_reviewed")
    if not approve:
        blockers.append("approval_required")

    queueable = not blockers
    result_core = {
        "schema": "fable5_comfyui_workflow_review.v1",
        "policy": orch.POLICY,
        "queueable": queueable,
        "queued": False,
        "execution": "manifest_only" if not queueable else "local_queue_pending_user_run",
        "blockers": blockers,
        "unknown_nodes": unknown_nodes,
        "non_loopback_hosts": non_loopback,
        "model_downloads": False,
        "unknown_custom_nodes_executed": 0,
        "externalRequests": 0,
        "trainingAllowed": False,
        "controls": dict(orch.CONTROLS),
    }
    result = dict(result_core)
    result["signature"] = orch._sign(result_core)
    return result


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def run_self_test() -> dict[str, Any]:
    checks: list[str] = []

    reg = build_registry()
    if not registry_guarantees_hold(reg):
        raise RuntimeError("persona guarantees broken")
    checks.append("persona_guarantees_hold")

    # Determinism: same input -> identical registry hash.
    if orch.canonical(build_registry()) != orch.canonical(reg):
        raise RuntimeError("non-deterministic registry")
    checks.append("deterministic_registry")

    # Discovered nodes preserved (sarah + sophie present from repo config).
    ids = {p["id"] for p in reg["personas"]}
    for expected in ("hades", "angela", "lainie", "sophie", "addie", "sue",
                     "sabina", "sarah", "ivy", "minnie"):
        if expected not in ids:
            raise RuntimeError(f"missing persona node: {expected}")
    checks.append("discovered_and_guaranteed_preserved")

    # No invented bios/relationships anywhere.
    for p in reg["personas"]:
        if p["biography"] is not None or p["relationships"] != []:
            raise RuntimeError("biography/relationships must stay empty")
    checks.append("no_invented_bio_or_relationships")

    # Opaque pointer refuses every social action; nothing fetched.
    ptr = opaque_pointer("https://x.com/someone")
    if not ptr["is_social"] or ptr["read_only"] is not True:
        raise RuntimeError("x.com pointer must be social + read_only")
    if any(v is not False for v in ptr["actions"].values()):
        raise RuntimeError("no social action may be enabled")
    insta = opaque_pointer("https://instagram.com/someone")
    if not insta["is_social"]:
        raise RuntimeError("instagram must be recognized as social pointer")
    checks.append("opaque_pointers_read_only")

    # Classifier: mystical labels alone must NOT promote a record.
    label_only = classify_record({
        "node_id": "sophie",
        "labels": ["sovereign", "11D", "grok", "makima", "primordial"],
        "provenance": {"in_repo_config": True, "first_party": True, "hashed": True},
        "evidence": [],
    })
    if label_only["tier"] != "provisional":
        raise RuntimeError("labels alone must not rank above provisional")
    checks.append("labels_alone_do_not_rank")

    # Tier ladder from evidence.
    prov = classify_record({"node_id": "n", "evidence": [
        {"kind": "loopback_probe", "ref": "a", "verified": True}]})
    if prov["tier"] != "provisional":
        raise RuntimeError("single evidence must be provisional")
    corr = classify_record({"node_id": "n", "evidence": [
        {"kind": "loopback_probe", "ref": "a", "verified": True},
        {"kind": "user_attestation", "ref": "b", "verified": True}]})
    if corr["tier"] != "corroborated":
        raise RuntimeError("two evidences must corroborate")
    canon = classify_record({"node_id": "n",
        "provenance": {"in_repo_config": True},
        "evidence": [
            {"kind": "repo_config", "ref": "a", "verified": True},
            {"kind": "loopback_probe", "ref": "b", "verified": True}]})
    if canon["tier"] != "canonical":
        raise RuntimeError("in-repo corroborated must be canonical")
    prim = classify_record({"node_id": "n",
        "provenance": {"in_repo_config": True, "first_party": True, "hashed": True},
        "evidence": [
            {"kind": "repo_config", "ref": "a", "verified": True},
            {"kind": "loopback_probe", "ref": "b", "verified": True}]})
    if prim["tier"] != "primordial":
        raise RuntimeError("first-party+hashed canonical must be primordial")
    checks.append("evidence_tier_ladder")

    # External pointer evidence is never trusted.
    ext = classify_record({"node_id": "n", "evidence": [
        {"kind": "external_pointer", "ref": "https://x.com/x", "verified": True},
        {"kind": "external_pointer", "ref": "https://instagram.com/y", "verified": True}]})
    if ext["tier"] != "provisional" or ext["trusted_evidence"] != 0:
        raise RuntimeError("external pointers must not count as trusted evidence")
    checks.append("external_pointers_not_trusted")

    # Prohibited flags force quarantine.
    q = classify_record({"node_id": "n", "flags": {"real_person_likeness": True},
        "provenance": {"in_repo_config": True, "first_party": True, "hashed": True},
        "evidence": [{"kind": "repo_config", "ref": "a", "verified": True},
                     {"kind": "loopback_probe", "ref": "b", "verified": True}]})
    if q["tier"] != "quarantine":
        raise RuntimeError("real-person likeness must quarantine")
    checks.append("prohibited_flags_quarantine")

    # Batch determinism.
    batch = {"records": [
        {"node_id": "b", "evidence": [{"kind": "repo_config", "ref": "1", "verified": True}]},
        {"node_id": "a", "evidence": []}]}
    if orch.canonical(classify_telemetry(batch)) != orch.canonical(classify_telemetry(batch)):
        raise RuntimeError("non-deterministic batch classification")
    checks.append("deterministic_classification")

    # Workflow references bind to the right open-weight models.
    img = workflow_reference("image")
    vid = workflow_reference("video")
    aud = workflow_reference("audio")
    if img["workflow"]["model"] != "Flux.1 Dev":
        raise RuntimeError("image must reference Flux.1 Dev")
    if vid["workflow"]["model"] != "Wan 2.2":
        raise RuntimeError("video must reference Wan 2.2")
    if aud["workflow"]["model"] != "ACE-Step 1.5":
        raise RuntimeError("audio must reference ACE-Step 1.5")
    for wf in (img, vid, aud):
        if wf["model_downloads"] is not False or wf["reference_only"] is not True:
            raise RuntimeError("workflows must be reference_only, no downloads")
    checks.append("workflow_reference_models")

    # Workflow review gate: unknown node blocks, model download blocks, needs approval + review.
    bad = review_workflow({"nodes": [{"class_type": "EvilCustomNode"}],
                           "hosts": ["http://127.0.0.1:8188"], "reviewed": True}, approve=True)
    if bad["queueable"] or "unknown_custom_nodes" not in bad["blockers"]:
        raise RuntimeError("unknown custom node must block")
    dl = review_workflow({"nodes": [{"class_type": "KSampler"}], "model_downloads": True,
                          "reviewed": True}, approve=True)
    if dl["queueable"] or "model_download_requested" not in dl["blockers"]:
        raise RuntimeError("model download must block")
    remote = review_workflow({"nodes": [{"class_type": "KSampler"}],
                              "hosts": ["http://10.0.0.5:8188"], "reviewed": True}, approve=True)
    if remote["queueable"] or "non_loopback_host" not in remote["blockers"]:
        raise RuntimeError("non-loopback host must block")
    unreviewed = review_workflow({"nodes": [{"class_type": "KSampler"}]}, approve=True)
    if unreviewed["queueable"] or "workflow_not_reviewed" not in unreviewed["blockers"]:
        raise RuntimeError("unreviewed workflow must block")
    ok = review_workflow({"nodes": [{"class_type": "KSampler"},
                                    {"class_type": "VAEDecode"}],
                          "hosts": ["http://127.0.0.1:8188"], "reviewed": True}, approve=True)
    if not ok["queueable"] or ok["queued"] is not False:
        raise RuntimeError("reviewed+approved+safe must be queueable but not auto-queued")
    if ok["unknown_custom_nodes_executed"] != 0:
        raise RuntimeError("no unknown custom node may execute")
    checks.append("workflow_review_gate")

    return {"ok": True, "tests": len(checks), "checks": checks}


if __name__ == "__main__":
    print(json.dumps(run_self_test(), ensure_ascii=False, indent=2))
