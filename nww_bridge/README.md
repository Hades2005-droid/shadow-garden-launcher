# NWW Perplexity Bridge (local prototype)

A local bridge that connects the NWW mesh to Perplexity's **Sonar API** for
research, and slots research into the planning/handoff chain via the shared
**AgentResult contract v1.0**.

## Why two layers

- **Technical bridge** (`perplexity_bridge.py`) — talks to `api.perplexity.ai`.
  Mock-by-default, live when a key is present, transport injectable for tests.
- **Planning layer** (`router.py`) — routes an *intent* to an agent, validates
  the result against the contract, logs the run to JSONL, and follows handoffs.
  This is the "planning-master" piece: research → review → implement as a chain
  with a stable `trace_id`.

## Files

| File | Role |
|------|------|
| `contract.py` | AgentResult v1.0, frozen enums, `validate()`, `classify_health()`, UTC-safe timestamps |
| `perplexity_bridge.py` | `PerplexityBridge.research()` → AgentResult (mock or live) |
| `router.py` | `Router.register()/run()` — intent dispatch + handoff chain + JSONL log |
| `cli.py` | `python cli.py "question"` |
| `tests/test_bridge.py` | 21 mocked tests, no network |

## Quick start

```bash
# Mock mode — no key, no network:
python3 cli.py "What changed in the Asana REST API in 2025?"

# Live mode — real Perplexity Sonar call:
export PERPLEXITY_API_KEY=pplx-...          # get one at perplexity.ai/settings/api
python3 cli.py --model sonar-pro "..."

# Tests:
python3 -m unittest tests.test_bridge -v
```

## Safety rules (same as the rest of NWW)

- **Secret only from env** (`PERPLEXITY_API_KEY`). Never hardcoded, never logged;
  error details are redacted so the key can't leak into an AgentResult.
- **Mock-by-default** — CI and any keyless run make zero network calls.
- **Frozen contract** — status ∈ {success, blocked, needs_input}; 9 error classes;
  `error` present only when status ≠ success.

## Sonar models

`sonar` (default, cheapest), `sonar-pro` (larger context / more citations),
`sonar-reasoning` (chain-of-thought). Pass with `--model`.

## Using it as a library

```python
from perplexity_bridge import PerplexityBridge
from router import Router

bridge = PerplexityBridge()                 # reads PERPLEXITY_API_KEY if set
router = Router(log_path="agent-results.jsonl")
router.register("web_research",
                lambda q, tid: bridge.research(q, trace_id=tid,
                                               handoff_to="claude",
                                               handoff_intent="code_review"))
chain = router.run("web_research", "Compare Asana vs Jira idempotency")
# chain[0] = perplexity result, chain[1] = whatever "code_review" resolves to
```

## Chain state (picked up from Phase-A Perplexity)

`findings/perplexity_phase_a.py` carries forward the three completed Fable-5
Perplexity research results (Asana REST custom fields, portfolio tier support,
idempotency patterns) as contract-v1.0 AgentResults. Regenerate the run log with:

```bash
python3 -m nww_bridge.findings.perplexity_phase_a   # writes nww_bridge/agent-results.jsonl
```

The chain uses a stable `trace_id` (`unified-handoff-packet-v1`); the last
finding hands off to `claude / code_review` (Phase B). This is where the mesh
resumes.

## Home

Lives in `shadow-garden-launcher/nww_bridge/` on branch
`claude/nww-asana-connector-2gst3u`, alongside the existing Asana connector.
Additive — it does not touch the voice `bridge.py` or the Jira flow.
