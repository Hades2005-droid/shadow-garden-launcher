"""Phase-A Perplexity research — carried forward into the mesh.

This is where the earlier Fable-5 Perplexity run left off: three completed
research tasks (Asana REST custom fields, portfolio tier support, idempotency
patterns). We replay them as contract-v1.0 AgentResults so the mesh chain
continues from real state instead of re-deriving it. The final finding hands
off to claude / code_review (Phase B).

Run:  python3 -m nww_bridge.findings.perplexity_phase_a > /dev/null
      # writes nww_bridge/agent-results.jsonl
"""
from __future__ import annotations

import json
import os
import sys

# Allow running both as a module and as a direct script.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from nww_bridge.contract import AgentResult, validate  # noqa: E402

# Stable trace across the Phase-A → Phase-B chain.
TRACE_ID = "unified-handoff-packet-v1"
TS = "2026-07-07T23:45:00Z"

PHASE_A_FINDINGS = [
    {
        "run_id": "perplexity-phase-a-task1-custom-fields",
        "question": "Asana REST API: how are custom fields created and attached, "
                    "and how should idempotent creation be handled?",
        "answer": (
            "POST /custom_fields requires workspace, name, resource_subtype "
            "(text|enum|multi_enum|number|date|people|reference). Attach to a "
            "project via POST /projects/{gid}/addCustomFieldSetting with "
            "{data:{custom_field: gid}}; same shape for portfolios. Asana has NO "
            "Idempotency-Key header — dedup by querying existing fields by name "
            "before POST and treating 409 Conflict as idempotent success."
        ),
        "citations": [
            "https://developers.asana.com/reference/createcustomfield",
            "https://developers.asana.com/reference/addcustomfieldsettingforproject",
            "https://developers.asana.com/reference/addcustomfieldsettingforportfolio",
        ],
        "handoff": None,
    },
    {
        "run_id": "perplexity-phase-a-task2-tier-support",
        "question": "Which Asana tier is required for portfolios, and what is the "
                    "free-tier fallback?",
        "answer": (
            "Portfolios are Advanced tier only (~$24.99/user/mo annual). Custom "
            "fields require Starter+. Free-tier fallback is Saved Searches "
            "(no status roll-up). Bootstrap must feature-detect: on 403/404 for "
            "portfolio creation, degrade gracefully instead of erroring — a 4xx "
            "on the portfolio endpoint is a tier gate, not a failure."
        ),
        "citations": [
            "https://asana.com/pricing",
            "https://help.asana.com/s/article/pricing-and-purchases",
        ],
        "handoff": None,
    },
    {
        "run_id": "perplexity-phase-a-task3-idempotency",
        "question": "Idempotency-key patterns for external task sync (Stripe, "
                    "GitHub, PagerDuty) applicable to Asana.",
        "answer": (
            "Business keys are derived, not random: Stripe Idempotency-Key, "
            "GitHub run_id, PagerDuty dedup_key. For Asana, the connector must "
            "own dedup: derive (trace_id, intent, payload_hash), check its own "
            "map before POST, store the external id in Asana's external_gid "
            "(1024 chars, OAuth-protected, user-visible — no PII). Retry network "
            "errors with backoff; treat 409 as success."
        ),
        "citations": [
            "https://docs.stripe.com/api/idempotent_requests",
            "https://developers.asana.com/docs/custom-external-data",
            "https://datatracker.ietf.org/doc/draft-ietf-httpapi-idempotency-key-header/",
        ],
        # Last finding hands the chain to Phase B (Claude code review).
        "handoff": {"to": "claude", "intent": "code_review",
                    "payload": {"phase": "B", "scope": "mesh seams + contract adherence"}},
    },
]


def build_results() -> list[AgentResult]:
    results = []
    for f in PHASE_A_FINDINGS:
        results.append(AgentResult(
            agent="perplexity",
            status="success",
            summary=f"[phase-a] {f['question'][:70]}",
            trace_id=TRACE_ID,
            run_id=f["run_id"],
            ts_start=TS,
            ts_end=TS,
            output={
                "mode": "carried-forward",
                "model": "fable-5",
                "answer": f["answer"],
                "citations": f["citations"],
            },
            handoff=f["handoff"],
        ))
    return results


def main() -> int:
    out_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                            "agent-results.jsonl")
    results = build_results()
    with open(out_path, "w", encoding="utf-8") as fh:
        for r in results:
            rec = r.to_dict()
            ok, errors = validate(rec)
            if not ok:
                print(f"INVALID: {errors}", file=sys.stderr)
                return 1
            fh.write(json.dumps(rec) + "\n")
    print(f"wrote {len(results)} Phase-A findings → {out_path}")
    print(f"chain trace_id = {TRACE_ID}; next hop = claude/code_review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
