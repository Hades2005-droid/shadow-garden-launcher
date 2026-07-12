# Runbook — Fable5 + ComfyUI Open-Weight Local Orchestrator

Canonical unification task: `37bce2fb-1ba6-471f-854f-3871d9c19947`
Lead/assistant task: `2366bfee-b78c-4ddc-9f86-304c30c67c4d`
Policy: `no_scrape_pointer_only`

## Scope

This orchestrator is a **local control point**, not an authority holder. It
coordinates Fable5 and ComfyUI open-weight generation by producing signed/hashed
handoff manifests that a human runs manually. It never posts, pushes, browses,
calls connectors, writes to external systems, echoes credentials, downloads
weights, or renders on its own.

Compatible with, and does not replace, the existing surfaces:
- EDEN Burst-Alpha shell (`../universe-alpha-section-one-0.1.0/eden_burst_alpha.py`)
- Black Sun learning loop (`../universe-alpha-section-one-0.1.0/black_sun_learning/`)
- Local terminal / connector bridge (`monitors/connector_bridge.py`)

Authority stays with those surfaces and with the user. This tool only observes,
validates, health-checks, compiles manifests, and gates.

## Invariants (must hold)

- Roles present: `unification_target`, `fable5_comfyui_open_merge_target`.
- Endpoints loopback-only: Fable5 `127.0.0.1:5619`, ComfyUI `127.0.0.1:8188`
  (`/system_stats`), EDEN `127.0.0.1:8791`.
- `media.default_mode == "manifest_only"`, `requires_user_approval == true`.
- `max_video_seconds == 30`, `auto_weight_downloads == false`.
- Controls all safe: no external fetch/write, no connector writes, no X writes,
  no agent broadcast, no credential echo, no hidden authority, no real-person
  likeness engine, `training_allowed == false`.

`validate_source()` rejects any source that breaks the task ids, policy, roles,
endpoints, media defaults, or control flags above.

## Pipeline

`observe -> validate -> health -> compile -> gate -> emit`

Artifacts land under `state/latest.json`, `state/history.json` (capped at 64),
and `outbox/job_<run_id>.json`. All writes are atomic and stay inside this
release directory. `state/` and `outbox/` contents are git-ignored (runtime
artifacts); only `.gitkeep` placeholders are tracked.

## Gating (approval flow)

1. `dispatch` / `compile_job_manifest` defaults to `manifest_only`,
   `ready=false` until the spell passes quality + safety checks.
2. When ready, status becomes `ready_for_user_approval`.
3. Only `approve=true` **and** `executionMode="queue"` moves the manifest to
   `local_queue_pending_user_run` (a local slot). No remote render, no download.
4. `gate()` reports `external_actions_executed == 0`,
   `weight_downloads_executed == 0`, `source_mutations_executed == 0`.

## catalyst_light physics vs symbolic metadata

Every manifest carries two strictly separated namespaces:
- `manifest.physics` — `catalyst_light` factual constants (`symbolic_only: false`):
  fps, frame budget, color space. Used only for local budgeting.
- `manifest.symbolic` — narrative/carrier metadata (`symbolic_only: true`):
  carries no physics facts and no authority.

Tests assert the namespaces never merge.

## Signing / handoff

- Every manifest is `sha256`-hashed under `signature.sha256`.
- If `ORCHESTRATOR_HMAC_KEY` is present, `signature.hmac_sha256` is added and
  `signature.signed=true`. The key is never persisted or echoed.
- Downstream (Fable5 / ComfyUI) consumers read the manifest and run it manually
  under user authorization. This package performs no handoff itself.

## Run

```bash
cd releases/fable5-comfyui-open-orchestrator-0.1.0
python3 orchestrator.py self-test
python3 -m unittest test_orchestrator -v
python3 orchestrator.py run --no-probe
```

## Blockers / external steps (held, never auto-executed)

- Starting Fable5 (`:5619`) and ComfyUI (`:8188`) is a user action on the Mac.
- Providing local open weights is a user action; this tool never downloads them.
- Any Slack / X / Atlassian / HARPA / Qdrant handoff is a separate,
  user-authorized step performed elsewhere. This package does not perform it.
