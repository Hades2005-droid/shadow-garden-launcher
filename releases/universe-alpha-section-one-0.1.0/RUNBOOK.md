# Runbook — Universe Alpha, Section One "Boundless Playground v0"

Task: `2366bfee-b78c-4ddc-9f86-304c30c67c4d`
Thread: https://www.perplexity.ai/computer/tasks/2366bfee-b78c-4ddc-9f86-304c30c67c4d?view=thread

## Scope

Section One is the bounded, offline Black Sun learning loop plus the read-only
EDEN shell that surfaces its latest packet. Nothing here posts, pushes, browses,
calls connectors, mutates source, or grants authority.

## Invariants (must hold)

- 22-node Taiji constellation (`section_one.node_count == 22`).
- Routing: North -> Lunar; South -> Solar; cross-type / cross-application -> Tera.
- Black Sun is `symbolic_only` narrative metadata, never authority.
- No self-modification: `source_code_mutation == false`.
- No external fetch / browser / broadcast / credentials.
- X is read-only (`x_read_only == true`).
- The loop performs no external writes (`external_write == false`).

`validate_source()` rejects any packet that breaks the task id, section name,
node count, routing contract, or the control flags above.

## Run the loop

```bash
cd releases/universe-alpha-section-one-0.1.0
python3 black_sun_learning/test_black_sun_recursive_loop.py   # unit tests
python3 black_sun_learning/black_sun_recursive_loop.py        # observe->...->emit
```

Sequence: `observe -> validate -> compare -> propose -> gate -> emit`.
Artifacts land under `black_sun_learning/state/` (latest.json, history.json)
and `black_sun_learning/outbox/section_one_<run_id>.json`. History is capped at
64 entries. All writes are atomic and stay inside this release directory.

## EDEN shell

```bash
cd releases/universe-alpha-section-one-0.1.0
python3 eden_burst_alpha.py          # serves the Burst-Alpha field on :8790
```

- `GET http://localhost:8790/api/black-sun` returns the latest loop packet
  (read from `black_sun_learning/state`). Override the port with `EDEN_PORT`.

## Gating

Proposals that require external writes (e.g. HARPA key repair, Qdrant URL) are
held under `gate.held_for_user_approval` and are never auto-executed. Safe,
in-section proposals appear under `gate.auto_safe_proposals`.
`external_actions_executed` and `source_mutations_executed` are always `0`.

## Handoff

Slack / X / Atlassian / HARPA / Qdrant handoffs are performed by the main agent
in a separate, user-authorized step. This package does not perform them.
