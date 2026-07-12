# Fable5 + ComfyUI Open-Weight Local Orchestrator v0.1.0

Central, user-controlled local orchestrator that unifies the existing EDEN /
Black Sun / terminal surfaces for open-weight image / video / audio generation —
**without transferring authority** away from those surfaces.

- Canonical unification task: `37bce2fb-1ba6-471f-854f-3871d9c19947`
- Lead/assistant task: `2366bfee-b78c-4ddc-9f86-304c30c67c4d`
- Roles preserved: `unification_target`, `fable5_comfyui_open_merge_target`
- Policy: `no_scrape_pointer_only`

## What it is

A single loopback-only control point (CLI + importable library) that:

- reports config/roles/controls (`status`),
- probes the three local surfaces (`health`),
- compiles **hashed / optionally HMAC-signed** local handoff manifests for
  image / video / audio jobs (`dispatch`), and
- runs the bounded `observe -> validate -> health -> compile -> gate -> emit`
  pipeline (`run`).

## Endpoints (loopback only)

| Surface | Address | Health |
|---------|---------|--------|
| Fable5  | `127.0.0.1:5619` | `/` |
| ComfyUI | `127.0.0.1:8188` | `/system_stats` |
| EDEN    | `127.0.0.1:8791` | `/healthz` |

The source contract is rejected if any endpoint is non-loopback or if the
ComfyUI health path is not `/system_stats`.

## Hard invariants (enforced by code + tests)

- Default `executionMode` is `manifest_only`; local queueing requires
  `approve=true` **and** an explicit `queue` mode — and even then only queues
  locally (`local_queue_pending_user_run`), never renders remotely.
- `externalRequests == 0`, `trainingAllowed == false`, always.
- Max video duration **30s**; no auto weight downloads
  (`weights.auto_download == false`).
- `no_scrape_pointer_only`: external URLs are stored as pointers
  (`action_taken: "none"`, `scraped: false`), never fetched.
- No agent broadcast, external connector writes, X writes, credential echo,
  hidden authority/backdoors, or real-person likeness engine (such requests are
  refused with `real_person_likeness_refused`).
- `catalyst_light` physics facts live in `manifest.physics`
  (`symbolic_only: false`); symbolic metadata lives in `manifest.symbolic`
  (`symbolic_only: true`). The two namespaces never merge.

## Persona pipeline & 9-point telemetry

A deterministic, local-only persona registry and telemetry classifier extend the
orchestrator without changing any safety invariant. See **`PERSONA_CONTRACT.md`**
for the full contract. In brief:

- `personas` — build the signed persona registry (discovered repo nodes preserved;
  `minnie`/`sarah`/`sophie` guaranteed; **no biographies, no relationships, ever**).
- `classify` — classify `shadow_garden.9point_node_telemetry.v1` records into
  `primordial/canonical/corroborated/provisional/quarantine` by **provenance +
  verifiable evidence only** — mystical/character labels never rank a record.
- `workflow` — reference-only ComfyUI/EDEN metadata (image Flux.1 Dev, video
  Wan 2.2, audio ACE-Step 1.5); loopback hosts only, no model downloads, unknown
  custom nodes never execute, queue needs user approval + a reviewed workflow.
- X.com / Twitter / Instagram links are **opaque read-only pointers** — no scrape,
  fetch, post, like, reply, follow, DM, or credential use.
- Makima/Seiko/Kaguya and sovereign/lattice/11D/Grok are `symbolic_only` metadata,
  never authority or factual connectivity.

## Usage

```bash
cd releases/fable5-comfyui-open-orchestrator-0.1.0

python3 orchestrator.py status
python3 orchestrator.py health                 # TCP-probes loopback surfaces
python3 orchestrator.py health --no-probe      # deterministic, no probing

# Persona registry + telemetry (all local, deterministic, network-free)
python3 orchestrator.py personas               # signed persona registry
python3 orchestrator.py classify --file t.json # or pipe JSON on stdin
python3 orchestrator.py workflow --medium video # reference-only metadata

# Compile a manifest (manifest_only by default — no render, no download)
python3 orchestrator.py dispatch \
  --spell "violet lattice harmony field, temperance 14, soft bloom, no real-person likeness" \
  --medium image --engine comfyui --model my-local-sdxl

# Approve + request a LOCAL queue slot (still no remote work / downloads)
python3 orchestrator.py dispatch --spell "..." --approve --queue

python3 orchestrator.py run --no-probe         # full bounded pipeline
python3 orchestrator.py self-test              # deterministic self-checks
```

## Signing

Manifests are always `sha256`-hashed. If `ORCHESTRATOR_HMAC_KEY` is set in the
environment, an `hmac-sha256` signature is added. The key is used but **never**
written to disk or echoed into any manifest (verified by the `hmac_sign_no_key_echo`
self-test).

## Tests

```bash
python3 orchestrator.py self-test              # 12 checks + persona pipeline
python3 -m unittest test_orchestrator test_persona_pipeline -v   # 55 tests
```

See `RUNBOOK.md` for operational detail and the handoff contract, and
`PERSONA_CONTRACT.md` for the persona / telemetry / pointer / workflow contract.
