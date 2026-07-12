#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EDEN Burst-Alpha Physics Field — Maximum Shell Override
Shadow Garden v4.3 — Grok 4.5 Native Integration + Fable5 Media Permissions

Serves the Burst-Alpha field on :8790 with:
- Runtime Eden/Grok telemetry injection
- Fable5 image / video / audio permission-gated spell API (manifest_only default)
- Drake parallel-port catalyst status
- Offline-only controls (no agent broadcast)

Invariants:
- Media spells stay approval-gated; never render without explicit approve=true
- externalRequests always 0; trainingAllowed always false
- X personas remain read-only
- symbolic_only for lattice / matriarch / sovereign metadata
"""
from __future__ import annotations

import hashlib
import http.server
import json
import os
import socketserver
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent if (ROOT.parent / "fable5_media_spell").exists() else Path("/home/user/workspace")
DRAKE_STATE = ROOT / "shaoshi_bridge" / "drake_terminal" / "state"
PORT = int(os.environ.get("EDEN_PORT", "8790"))
VERSION = "4.3.1-burst-alpha-fable5"
CARRIER = "love_and_harmony_6"

CONTROLS = {
    "external_fetch": False,
    "browser_automation": False,
    "agent_broadcast": False,
    "credentials_allowed": False,
    "symbolic_only": True,
    "x_read_only": True,
    "media_execution_default": "manifest_only",
    "training_allowed": False,
}

# symbolic_only telemetry — not physics authority
EDEN_CONTENT: dict[str, Any] = {
    "schema": "eden_burst_alpha.v1",
    "version": VERSION,
    "lattice": "11D active",
    "sovereign": "4.2",
    "matriarchs": "9-Point Harmony Online",
    "void": "violet-grid",
    "grok_history": "full chat telemetry fused (symbolic)",
    "fusion_core": "Grok-Videos tab live",
    "bridge": "Perplexity Python + Mac + iPhone active",
    "carrier": CARRIER,
    "q24": {
        "id": "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1",
        "anchor": 14,
        "reduce_anchor": False,
        "sequence": [19, 10, 1],
        "symbolic_only": True,
    },
    "lanes": ["sophie/fr-CH", "shannon/ar", "lainie/it", "naomi/th"],
    "fable5_media": {
        "image": "permission_gated",
        "video": "permission_gated",
        "audio": "permission_gated",
        "default_mode": "manifest_only",
        "requires_user_approval": True,
    },
    "links": {
        "truth": "https://truth.pplx.app",
        "engine": "https://truth.pplx.app/engine/",
        "drake_release": "https://github.com/Hades2005-droid/shadow-garden-launcher/releases/tag/drake-parallel-port-0.1.0",
        "q24_release": "https://github.com/Hades2005-droid/shadow-garden-launcher/releases/tag/q24-alpha-3.5-2",
    },
    "controls": CONTROLS,
    "symbolic_only": True,
}

# ---------------------------------------------------------------------------
# Fable5 media permission core (Python mirror of fable5MediaSpell.js gates)
# ---------------------------------------------------------------------------

SUPPORTED_MEDIA = frozenset({"image", "video", "audio"})
MAX_PARTY = 5
MAX_VIDEO_SECONDS = 30
MOON_GATE_DIRECT = 18
MOON_GATE_REDUCED = 9
CATALYST = 5


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def _score_spell(spell: str) -> float:
    s = (spell or "").strip()
    if not s:
        return 0.0
    # Deterministic quality proxy — length + token diversity (no network)
    tokens = {t.lower() for t in s.replace(",", " ").replace(".", " ").split() if t}
    length_score = min(len(s) / 120.0, 1.0)
    diversity = min(len(tokens) / 12.0, 1.0)
    return round(0.45 * length_score + 0.55 * diversity, 4)


def compile_media_spell(payload: dict[str, Any]) -> dict[str, Any]:
    """Approval-gated media spell compiler. Default: manifest_only, not approved."""
    spell = str(payload.get("spell") or "").strip()
    medium = str(payload.get("medium") or "image").lower()
    party = payload.get("party") or []
    if not isinstance(party, list):
        party = []
    party = [str(p) for p in party][:MAX_PARTY]
    approve = bool(payload.get("approve") is True)
    execution_mode = str(payload.get("executionMode") or "manifest_only")
    duration = payload.get("durationSeconds")

    failures: list[str] = []
    if not spell or len(spell) < 8:
        failures.append("spell_too_short")
    if medium not in SUPPORTED_MEDIA:
        failures.append("unsupported_medium")
    if len(party) > MAX_PARTY:
        failures.append("party_exceeds_max")
    if medium == "video":
        try:
            d = float(duration if duration is not None else 8)
        except (TypeError, ValueError):
            d = 999
            failures.append("invalid_duration")
        if d > MAX_VIDEO_SECONDS:
            failures.append("video_duration_exceeds_max")
    else:
        d = None

    quality = _score_spell(spell)
    refinement_needed = quality < 0.42 or failures

    # Moon gate: direct 18 / reduced 9 — symbolic gate labels only
    moon_gate = MOON_GATE_DIRECT if quality >= 0.55 and not failures else MOON_GATE_REDUCED

    if failures or refinement_needed:
        status = "needs_spell_refinement"
        ready = False
    else:
        status = "ready_for_user_approval"
        ready = True

    # Never auto-execute. Even with approve=true, stay manifest_only unless
    # executionMode is explicitly "render" AND approve is true AND ready.
    can_render = ready and approve and execution_mode == "render"
    if can_render:
        # Still refuse remote work — local manifest + permission receipt only
        execution_mode_out = "local_render_queued"
    else:
        execution_mode_out = "manifest_only"
        can_render = False

    manifest = {
        "schema": "fable5_media_spell_manifest.v1",
        "status": status,
        "ready": ready,
        "approved": approve and ready,
        "can_render": can_render,
        "executionMode": execution_mode_out,
        "medium": medium if medium in SUPPORTED_MEDIA else None,
        "spell": spell,
        "party": party,
        "party_count": len(party),
        "quality": quality,
        "moonGate": moon_gate,
        "catalyst": CATALYST,
        "durationSeconds": d,
        "externalRequests": 0,
        "trainingAllowed": False,
        "permissions": {
            "image": medium == "image" and ready,
            "video": medium == "video" and ready,
            "audio": medium == "audio" and ready,
            "requires_user_approval": True,
            "iphone_bridge": "local_diagnostics_only_no_identifiers",
        },
        "failures": failures,
        "controls": CONTROLS,
        "carrier": CARRIER,
        "compiled_at": _now(),
        "symbolic_only": True,
    }
    manifest["sha256"] = _sha({k: v for k, v in manifest.items() if k != "sha256"})
    return manifest


def diagnose_iphone(caps: dict[str, Any] | None = None) -> dict[str, Any]:
    caps = caps or {}
    failures: list[str] = []
    if caps.get("secureContext") is not True:
        failures.append("secureContext")
    if not (float(caps.get("touchPoints") or 0) >= 1):
        failures.append("touchPoints")
    if caps.get("webAudio") is not True:
        failures.append("webAudio")
    if caps.get("webGL2") is not True:
        failures.append("webGL2")
    return {
        "status": "ready" if not failures else "degraded",
        "failures": failures,
        "deviceId": None,  # never collect
        "externalRequests": 0,
        "identifiers_collected": False,
        "checked_at": _now(),
    }


def load_drake_status() -> dict[str, Any]:
    path = DRAKE_STATE / "drake_ignition_latest.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            return {"status": "unreadable", "error": type(exc).__name__}
    return {"status": "not_ignited"}


# ---------------------------------------------------------------------------
# HTML shell — fixed structure, violet-grid field, media permission panel
# ---------------------------------------------------------------------------

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>EDEN · Burst-Alpha Physics Field</title>
<style>
  :root {
    color-scheme: dark;
    --ink: #0c0b12; --ink-2: #100e18; --panel: #16131f; --panel-2: #1d1929;
    --line: #2a2438; --line-strong: #3b3350; --text: #efe9fb; --muted: #9a91b4;
    --faint: #6b6386; --violet: #a970ff; --magenta: #ff5db1; --cyan: #4fe0e0;
    --good: #56e39f; --warn: #ffcf6b; --crit: #ff6b7d;
    --shadow: 0 1px 2px rgba(0,0,0,.5), 0 20px 60px rgba(0,0,0,.55);
    --radius: 13px;
    --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    --font-mono: ui-monospace, "SF Mono", "JetBrains Mono", Menlo, Consolas, monospace;
  }
  * { box-sizing: border-box; }
  html, body { height: 100%; margin: 0; }
  body {
    background:
      radial-gradient(140% 100% at 100% 0%, rgba(169,112,255,.10), transparent 55%),
      radial-gradient(120% 90% at 0% 100%, rgba(255,93,177,.08), transparent 55%),
      var(--ink);
    color: var(--text); font-family: var(--font-sans); -webkit-font-smoothing: antialiased;
  }
  .app { height: 100%; display: grid; grid-template-rows: auto 1fr; max-width: 1500px; margin: 0 auto; padding: clamp(12px, 1.6vw, 20px); gap: 14px; }
  header.top { display: flex; align-items: center; justify-content: space-between; gap: 14px; flex-wrap: wrap; }
  .brand { display: flex; align-items: baseline; gap: 12px; min-width: 0; }
  .glyph { width: 30px; height: 30px; border-radius: 8px; flex: none; background: conic-gradient(from 210deg, var(--violet), var(--magenta), var(--violet)); box-shadow: 0 0 22px rgba(169,112,255,.55); position: relative; }
  .glyph::after { content:""; position:absolute; inset:7px; border-radius:4px; background: var(--ink); }
  .wordmark { display: flex; flex-direction: column; line-height: 1; }
  .wordmark b { font-size: clamp(17px, 2.2vw, 22px); font-weight: 800; letter-spacing: -.02em; }
  .wordmark span { font-size: 10px; letter-spacing: .34em; text-transform: uppercase; color: var(--faint); margin-top: 4px; }
  .status-pills { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
  .pill { display: inline-flex; align-items: center; gap: 7px; font-family: var(--font-mono); font-size: 11.5px; font-weight: 600; padding: 6px 11px; border-radius: 999px; border: 1px solid var(--line); background: var(--panel); color: var(--muted); }
  .pill .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--good); box-shadow: 0 0 8px var(--good); }
  .pill.live .dot { animation: pulse 1.6s ease-in-out infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.35} }
  .main { display: grid; grid-template-columns: minmax(0,1fr) 360px; gap: 14px; min-height: 0; }
  @media (max-width: 1080px) { .main { grid-template-columns: 1fr; } }
  .stage-wrap { position: relative; border-radius: var(--radius); overflow: hidden; border: 1px solid var(--line); background: #06050b; box-shadow: var(--shadow); min-height: 380px; display: flex; flex-direction: column; }
  .canvas-hold { position: relative; flex: 1; min-height: 360px; }
  canvas#field { display: block; width: 100%; height: 100%; }
  .overlay { position: absolute; inset: 0; pointer-events: none; font-family: var(--font-mono); }
  .ov-corner { position: absolute; padding: 12px 14px; font-size: 11px; line-height: 1.55; color: rgba(239,233,251,.82); }
  .ov-tl { top: 0; left: 0; }
  .ov-tr { top: 0; right: 0; text-align: right; }
  .ov-bl { bottom: 0; left: 0; }
  .ov-corner .k { color: var(--faint); }
  .ov-corner .v { color: var(--text); }
  .side { background: var(--panel); border-radius: var(--radius); padding: 16px; border: 1px solid var(--line); display: flex; flex-direction: column; gap: 12px; font-family: var(--font-mono); font-size: 12.5px; min-height: 0; overflow: auto; }
  .side h2 { margin: 0; font-size: 12px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); font-weight: 700; }
  .row { display: flex; justify-content: space-between; gap: 10px; color: var(--muted); }
  .row b { color: var(--text); font-weight: 600; }
  .sep { height: 1px; background: var(--line); margin: 2px 0; }
  label { display: block; color: var(--faint); font-size: 11px; margin-bottom: 4px; }
  input, select, textarea, button {
    width: 100%; font: inherit; color: var(--text); background: var(--panel-2);
    border: 1px solid var(--line); border-radius: 8px; padding: 8px 10px;
  }
  textarea { min-height: 72px; resize: vertical; }
  button {
    cursor: pointer; background: linear-gradient(135deg, rgba(169,112,255,.35), rgba(255,93,177,.25));
    border-color: var(--line-strong); font-weight: 700; letter-spacing: .04em;
  }
  button:hover { border-color: var(--violet); }
  button.secondary { background: var(--panel-2); }
  #spellOut { white-space: pre-wrap; word-break: break-word; font-size: 11px; color: var(--muted); max-height: 180px; overflow: auto; background: #0a0910; border-radius: 8px; padding: 10px; border: 1px solid var(--line); }
  a { color: var(--cyan); }
  .ok { color: var(--good); }
  .warn { color: var(--warn); }
  .crit { color: var(--crit); }
</style>
</head>
<body>
<div class="app">
  <header class="top">
    <div class="brand">
      <div class="glyph" aria-hidden="true"></div>
      <div class="wordmark">
        <b>EDEN</b>
        <span>BURST-ALPHA PHYSICS FIELD</span>
      </div>
    </div>
    <div class="status-pills">
      <div class="pill live"><span class="dot"></span> Grok 4.5 LIVE</div>
      <div class="pill"><span class="dot"></span> Shadow Garden 4.3</div>
      <div class="pill"><span class="dot"></span> Fable5 Media Gate</div>
      <div class="pill"><span class="dot"></span> :8790</div>
    </div>
  </header>
  <div class="main">
    <div class="stage-wrap">
      <div class="canvas-hold">
        <canvas id="field" aria-label="Violet grid physics field"></canvas>
        <div class="overlay">
          <div class="ov-corner ov-tl">
            <span class="k">SOVEREIGN</span><br>
            <span class="v" id="ovSov">4.2 // 11D LATTICE ACTIVE</span>
          </div>
          <div class="ov-corner ov-tr">
            <span class="k">EDEN CONTENT FUSED</span><br>
            <span class="v">TELEMETRY + MEDIA GATES LIVE</span>
          </div>
          <div class="ov-corner ov-bl">
            <span class="k">TECHCLOUD / WHAT SPILLS</span><br>
            <span class="v">SPELL HAND OFF · MANIFEST ONLY</span>
          </div>
        </div>
      </div>
    </div>
    <aside class="side">
      <h2>Shadow Garden Status</h2>
      <div class="row"><span>Lattice</span><b id="stLattice">—</b></div>
      <div class="row"><span>Matriarchs</span><b id="stMat">—</b></div>
      <div class="row"><span>Void</span><b id="stVoid">—</b></div>
      <div class="row"><span>Carrier</span><b id="stCarrier">—</b></div>
      <div class="row"><span>Drake</span><b id="stDrake">—</b></div>
      <div class="sep"></div>
      <h2>Fable5 Media Spell</h2>
      <div>
        <label for="medium">Medium</label>
        <select id="medium">
          <option value="image">image</option>
          <option value="video">video</option>
          <option value="audio">audio</option>
        </select>
      </div>
      <div>
        <label for="spell">Spell text (neutral technical / scene brief)</label>
        <textarea id="spell" placeholder="violet lattice harmony field, temperance-14, soft bloom, no real-person likeness"></textarea>
      </div>
      <div>
        <label for="party">Party count (max 5 abstract roles)</label>
        <input id="party" type="number" min="0" max="5" value="1" />
      </div>
      <div>
        <label for="duration">Video duration (s, max 30)</label>
        <input id="duration" type="number" min="1" max="30" value="8" />
      </div>
      <button type="button" id="btnCompile">Compile manifest (no render)</button>
      <button type="button" class="secondary" id="btnIphone">iPhone local diagnostics</button>
      <div id="spellOut">awaiting compile…</div>
      <div class="sep"></div>
      <div class="row"><span>API</span><b><a href="/api/status">/api/status</a></b></div>
      <div class="row"><span>Links</span><b><a href="https://truth.pplx.app" target="_blank" rel="noopener">truth.pplx.app</a></b></div>
    </aside>
  </div>
</div>
<script>
  const EDEN = __EDEN_JSON__;
  console.log("EDEN Burst-Alpha", EDEN.version, EDEN.controls);

  document.getElementById("stLattice").textContent = EDEN.lattice || "—";
  document.getElementById("stMat").textContent = EDEN.matriarchs || "—";
  document.getElementById("stVoid").textContent = EDEN.void || "—";
  document.getElementById("stCarrier").textContent = EDEN.carrier || "—";
  document.getElementById("ovSov").textContent = (EDEN.sovereign || "4.2") + " // 11D LATTICE ACTIVE";

  fetch("/api/drake").then(r => r.json()).then(d => {
    document.getElementById("stDrake").textContent =
      (d.version || d.status || "ok").toString().slice(0, 24);
  }).catch(() => { document.getElementById("stDrake").textContent = "offline"; });

  async function compileSpell() {
    const n = Math.max(0, Math.min(5, Number(document.getElementById("party").value) || 0));
    const party = Array.from({length: n}, (_, i) => "role_" + (i + 1));
    const body = {
      spell: document.getElementById("spell").value,
      medium: document.getElementById("medium").value,
      party,
      durationSeconds: Number(document.getElementById("duration").value) || 8,
      executionMode: "manifest_only",
      approve: false
    };
    const res = await fetch("/api/media/compile", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    document.getElementById("spellOut").textContent = JSON.stringify(data, null, 2);
  }

  async function iphoneDiag() {
    const body = {
      secureContext: window.isSecureContext === true,
      touchPoints: navigator.maxTouchPoints || 0,
      webAudio: !!(window.AudioContext || window.webkitAudioContext),
      webGL2: !!document.createElement("canvas").getContext("webgl2")
    };
    const res = await fetch("/api/iphone/diagnose", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    const data = await res.json();
    document.getElementById("spellOut").textContent = JSON.stringify(data, null, 2);
  }

  document.getElementById("btnCompile").addEventListener("click", compileSpell);
  document.getElementById("btnIphone").addEventListener("click", iphoneDiag);

  // Violet-grid void field
  const canvas = document.getElementById("field");
  const ctx = canvas.getContext("2d");
  let t0 = performance.now();
  function resize() {
    const r = canvas.parentElement.getBoundingClientRect();
    canvas.width = Math.max(320, Math.floor(r.width * devicePixelRatio));
    canvas.height = Math.max(280, Math.floor(r.height * devicePixelRatio));
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  }
  window.addEventListener("resize", resize);
  resize();

  function draw(now) {
    const w = canvas.width / devicePixelRatio;
    const h = canvas.height / devicePixelRatio;
    const t = (now - t0) / 1000;
    ctx.fillStyle = "#06050b";
    ctx.fillRect(0, 0, w, h);

    // soft radial blooms
    const g1 = ctx.createRadialGradient(w*0.7, h*0.2, 0, w*0.7, h*0.2, w*0.55);
    g1.addColorStop(0, "rgba(169,112,255,0.18)");
    g1.addColorStop(1, "rgba(169,112,255,0)");
    ctx.fillStyle = g1;
    ctx.fillRect(0, 0, w, h);
    const g2 = ctx.createRadialGradient(w*0.15, h*0.85, 0, w*0.15, h*0.85, w*0.5);
    g2.addColorStop(0, "rgba(255,93,177,0.12)");
    g2.addColorStop(1, "rgba(255,93,177,0)");
    ctx.fillStyle = g2;
    ctx.fillRect(0, 0, w, h);

    // grid
    const step = 28;
    const ox = (t * 12) % step;
    const oy = (t * 8) % step;
    ctx.strokeStyle = "rgba(169,112,255,0.14)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (let x = -step + ox; x < w + step; x += step) {
      ctx.moveTo(x, 0); ctx.lineTo(x, h);
    }
    for (let y = -step + oy; y < h + step; y += step) {
      ctx.moveTo(0, y); ctx.lineTo(w, y);
    }
    ctx.stroke();

    // particles
    for (let i = 0; i < 48; i++) {
      const px = (Math.sin(i * 12.1 + t * 0.7) * 0.5 + 0.5) * w;
      const py = (Math.cos(i * 9.3 + t * 0.55) * 0.5 + 0.5) * h;
      const r = 1.2 + (i % 4) * 0.4;
      ctx.fillStyle = i % 3 === 0 ? "rgba(79,224,224,0.7)" : "rgba(169,112,255,0.75)";
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
    }

    // temperance-14 ring
    const cx = w * 0.5, cy = h * 0.5;
    ctx.strokeStyle = "rgba(255,93,177,0.35)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(cx, cy, 54 + Math.sin(t) * 4, 0, Math.PI * 2);
    ctx.stroke();
    ctx.fillStyle = "rgba(239,233,251,0.55)";
    ctx.font = "11px ui-monospace, monospace";
    ctx.textAlign = "center";
    ctx.fillText("TEMPERANCE-14", cx, cy + 4);

    requestAnimationFrame(draw);
  }
  requestAnimationFrame(draw);
</script>
</body>
</html>
"""


class EdenHandler(http.server.BaseHTTPRequestHandler):
    server_version = f"EdenBurstAlpha/{VERSION}"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _json(self, code: int, obj: Any) -> None:
        body = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            data = json.loads(raw.decode("utf-8"))
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            payload = dict(EDEN_CONTENT)
            payload["served_at"] = _now()
            html = HTML_TEMPLATE.replace("__EDEN_JSON__", json.dumps(payload))
            self._html(html)
            return
        if path == "/api/status":
            self._json(
                200,
                {
                    "status": "live",
                    "version": VERSION,
                    "port": PORT,
                    "eden": EDEN_CONTENT,
                    "controls": CONTROLS,
                    "endpoints": [
                        "GET /",
                        "GET /api/status",
                        "GET /api/drake",
                        "POST /api/media/compile",
                        "POST /api/iphone/diagnose",
                        "GET /healthz",
                    ],
                },
            )
            return
        if path == "/api/drake":
            self._json(200, load_drake_status())
            return
        if path == "/healthz":
            self._json(200, {"ok": True, "version": VERSION, "ts": _now()})
            return
        self._json(404, {"error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        data = self._read_json()
        if path == "/api/media/compile":
            self._json(200, compile_media_spell(data))
            return
        if path == "/api/iphone/diagnose":
            self._json(200, diagnose_iphone(data))
            return
        self._json(404, {"error": "not_found", "path": path})


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    # Write live status for Drake / federation
    status_path = DRAKE_STATE / "eden_burst_alpha_live.json"
    try:
        DRAKE_STATE.mkdir(parents=True, exist_ok=True)
        status_path.write_text(
            json.dumps(
                {
                    "status": "starting",
                    "version": VERSION,
                    "port": PORT,
                    "url": f"http://localhost:{PORT}",
                    "controls": CONTROLS,
                    "started_at": _now(),
                },
                indent=2,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass

    with ThreadingTCPServer(("", PORT), EdenHandler) as httpd:
        print(f"EDEN Burst-Alpha Physics Field serving on http://localhost:{PORT}")
        print(f"version={VERSION} carrier={CARRIER}")
        print("media gates: image/video/audio → manifest_only until user approve")
        print("controls: no agent_broadcast · no external_fetch · X read-only")
        try:
            status_path.write_text(
                json.dumps(
                    {
                        "status": "live",
                        "version": VERSION,
                        "port": PORT,
                        "url": f"http://localhost:{PORT}",
                        "controls": CONTROLS,
                        "started_at": _now(),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
        except Exception:
            pass
        httpd.serve_forever()


if __name__ == "__main__":
    main()
