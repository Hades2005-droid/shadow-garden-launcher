---
name: eden-burst-alpha-force-merge
description: "Force-merge EDEN Burst-Alpha :8790 shell, Fable5 image/video/audio permission gates, and Drake terminal catalyst into Shadow Garden / TechCloud What Spills handoffs. Use when Fred asks for Eden burst alpha, maximum shell override, Grok-Videos tab fusion, TechCloud What Spills, Fable5 media permissions, or native terminal catalyst embed."
license: MIT
metadata:
  version: "1.0.0"
  author: "Shadow Garden / Perplexity Computer"
  carrier: "love_and_harmony_6"
---

# EDEN Burst-Alpha Force-Merge

## When to Use This Skill

Use when the user asks to:

- Start or repair the EDEN Burst-Alpha Physics Field (`:8790`)
- Force-merge Eden / Grok shell content into the Drake / Devin / Grok 4.5 terminal catalyst
- Wire **Fable5 native image / video / audio permission gates**
- Produce a **TechCloud What Spills** technical spell handoff
- Embed media-spell APIs into Shadow Garden fusion surfaces

## Invariants (never break)

1. **Offline catalyst core** — no agent broadcast, no autopost to X, no credential echo.
2. **Media default is `manifest_only`** — never render without explicit `approve: true` + user intent.
3. **`externalRequests: 0`** and **`trainingAllowed: false`** on every media manifest.
4. **No real-person likeness engines** — abstract Temperance-14 / scene briefs only.
5. **symbolic_only** for lattice / matriarch / sovereign / arcana metadata; physics facts stay separate (catalyst_light).
6. **X personas remain read-only.**
7. **Parallel port ≠ security backdoor** — approved offline file-drop only.

## Canonical paths

| Asset | Path |
|-------|------|
| EDEN server | `shadow_garden_mirror/eden_burst_alpha.py` |
| Force-merge | `shadow_garden_mirror/shaoshi_bridge/drake_terminal/force_merge_eden_fable5.py` |
| Drake port | `shadow_garden_mirror/shaoshi_bridge/drake_terminal/drake_parallel_port.py` |
| Fable5 JS | `fable5_media_spell/src/compiler/fable5MediaSpell.js` |
| Fable5 tests | `fable5_media_spell/test/fable5MediaSpell.test.js` |
| Handoff state | `…/drake_terminal/state/what_spills_handoff_latest.json` |
| Live URL | `http://localhost:8790` |

## Instructions

### 1. Start EDEN shell

```bash
cd /home/user/workspace/shadow_garden_mirror
python3 eden_burst_alpha.py
# → http://localhost:8790
```

Smoke:

```bash
curl -s http://127.0.0.1:8790/healthz
curl -s -X POST http://127.0.0.1:8790/api/media/compile \
  -H 'Content-Type: application/json' \
  -d '{"spell":"violet lattice temperance-14 abstract field","medium":"image","party":["role_1"],"approve":false}'
```

### 2. Force-merge into terminal catalyst

```bash
python3 shadow_garden_mirror/shaoshi_bridge/drake_terminal/force_merge_eden_fable5.py
```

This re-ignites Drake, writes bridge9 envelopes for `grok_45` / `devin` / `techcloud` / `lunar_mac`, and stamps `what_spills_handoff_latest.json`.

### 3. Fable5 media permissions

Supported media: `image` | `video` | `audio`

| Gate | Rule |
|------|------|
| spell | ≥ 8 chars; quality score ≥ 0.42 for ready |
| party | max 5 abstract roles |
| video duration | ≤ 30s |
| moonGate | 18 ready / 9 reduced |
| catalyst | always 5 |
| approve | required for any render queue |
| iPhone | local diagnostics only; **never** collect deviceId |

JS tests (must stay green):

```bash
cd fable5_media_spell && node --test test/fable5MediaSpell.test.js
```

### 4. TechCloud What Spills handoff

1. Commit under `releases/` on `Hades2005-droid/shadow-garden-launcher`
2. Comment KAN-13 with live links
3. Push key files to Mac:
   - `~/shadow_garden_may30_monitoring/DevinTerminalBridge/drake_terminal/`
   - `~/shadow_garden_may30_monitoring/fable5_media_spell/`
4. Manual gift only into Grok 4.5 terminal — no autopost

### 5. Optional skill package

After edits, validate:

```bash
agentskills validate /home/user/workspace/skills/eden-burst-alpha-force-merge/
```

Share SKILL.md (or zip if scripts/ added) via user skill settings.

## API surface (:8790)

- `GET /` — Burst-Alpha field UI + injected EDEN telemetry
- `GET /api/status` — full status
- `GET /api/drake` — Drake ignition snapshot
- `POST /api/media/compile` — Fable5 permission compile
- `POST /api/iphone/diagnose` — local capability check
- `GET /healthz` — liveness

## Safety rewrite

If a spell implies minors, non-consent, incest, trafficking, hidden-cam, or exploitation: refuse and return `needs_spell_refinement` with a safe failure reason. Consenting-adult abstract phrasing is allowed; graphic engines binding real people are not.
