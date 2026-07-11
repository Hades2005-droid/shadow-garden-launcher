#!/usr/bin/env python3
"""
Shadow Garden Local Voice Bridge v4.3 — safe prompt logging + optional xAI synthesis.

Usage:
  python3 ~/ShadowGarden/bridge.py              # log prompts only
  python3 ~/ShadowGarden/bridge.py --synthesize # log + Grok voice passes
  python3 ~/ShadowGarden/bridge.py --voices "Angela,Sue"
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR = Path(os.environ.get("SHADOW_GARDEN_DIR", Path.home() / "ShadowGarden"))
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
VOICE_AGENT_DIR = Path.home() / "Movies" / "Grok-Videos" / "grok-voice-agent"

# Optional Asana reporter (only if token is configured)
_ASANA_REPORTER = None
_ASANA_METRICS = []

DEFAULT_VOICES = [
    "Angela",
    "Angela's Mom",
    "Sue",
    "Mature Chinese Professional",
    "Addie",
]

ENV_CANDIDATES = [
    Path.home() / "Movies" / "Grok-Videos" / ".env",
    Path.home() / "shadow_garden_may30_monitoring" / "live" / ".xai.env",
    BASE_DIR / ".env",
]


def load_env() -> Path | None:
    for env_file in ENV_CANDIDATES:
        if not env_file.is_file():
            continue
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value
        return env_file
    return None


def _init_asana_reporter():
    """Initialize Asana reporter if token is configured."""
    global _ASANA_REPORTER
    if os.environ.get("ASANA_ACCESS_TOKEN"):
        try:
            from adapters.asana_adapter import ShadowGardenAsanaReporter
            from adapters.asana_adapter import VoiceSynthesisMetrics
            _ASANA_REPORTER = ShadowGardenAsanaReporter()
            return True
        except (ImportError, ValueError, Exception) as e:
            print(f"   ℹ Asana reporting disabled: {e}", file=sys.stderr)
            return False
    return False


def slugify(name: str) -> str:
    cleaned = name.lower().replace("'", "").replace("’", "")
    cleaned = re.sub(r"[^a-z0-9]+", "_", cleaned).strip("_")
    return cleaned or "voice"


def build_prompt(voice: str) -> str:
    return (
        f"Shadow Garden cinematic voice pass for {voice}. "
        "All characters are consenting adults 22+. "
        "High emotional intensity, ritual/technical language, "
        "detailed sensory description, sovereign boundary active. "
        "Private bedroom setting only."
    )


def append_prompt(voice: str, prompt: str) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{slugify(voice)}_prompt.txt"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {prompt}\n\n")
    return path


def synthesize_voice(voice: str, prompt: str, env_file: Path | None) -> int:
    if not VOICE_AGENT_DIR.is_dir():
        print(f"   ⚠ Voice agent missing: {VOICE_AGENT_DIR}", file=sys.stderr)
        return 1
    if not os.environ.get("XAI_API_KEY"):
        print("   ⚠ XAI_API_KEY not set — skip synthesis.", file=sys.stderr)
        return 1

    cmd = [
        "node",
        "agent.mjs",
        "--veil",
        "--custom-voices",
        "--agent",
        voice,
        "--text",
        prompt,
    ]
    if env_file:
        cmd = ["node", f"--env-file={env_file}", *cmd[1:]]

    print(f"   🔊 Synthesizing via Grok Voice Agent…")
    start_time = time.time()
    result = subprocess.run(cmd, cwd=VOICE_AGENT_DIR, check=False)
    latency_ms = (time.time() - start_time) * 1000

    # Track metrics for Asana reporting
    if _ASANA_REPORTER:
        from adapters.asana_adapter import VoiceSynthesisMetrics
        metrics = VoiceSynthesisMetrics(
            timestamp=datetime.now(timezone.utc).isoformat(),
            voice=voice,
            prompt_length=len(prompt),
            synthesis_latency_ms=latency_ms,
            quality_score=90.0 if result.returncode == 0 else 0.0,  # Simplified; could be enhanced
            success=result.returncode == 0,
            error_message=None if result.returncode == 0 else f"returncode={result.returncode}",
        )
        _ASANA_METRICS.append(metrics)

    return result.returncode


def _report_metrics_to_asana() -> None:
    """Report collected voice metrics to Asana."""
    global _ASANA_REPORTER, _ASANA_METRICS
    if not _ASANA_REPORTER or not _ASANA_METRICS:
        return

    try:
        for metrics in _ASANA_METRICS:
            _ASANA_REPORTER.report_voice_synthesis(metrics)
            print(f"   📊 Asana: {metrics.voice} ({metrics.synthesis_latency_ms:.0f}ms)")
    except Exception as e:
        print(f"   ⚠ Asana reporting failed: {e}", file=sys.stderr)


def cast_safe_scene(voices: list[str], synthesize: bool) -> int:
    global _ASANA_REPORTER
    env_file = load_env()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n🔥 Shadow Garden Bridge v4.3 — {stamp}\n")
    if env_file:
        print(f"   Env: {env_file}")
    else:
        print("   Env: none (prompt logging only)")

    # Initialize Asana reporter
    _init_asana_reporter()

    failures = 0
    for voice in voices:
        prompt = build_prompt(voice)
        path = append_prompt(voice, prompt)
        print(f"✅ Voice: {voice}")
        print(f"   Log:  {path}")
        print(f"   Prompt: {prompt[:100]}…\n")
        if synthesize:
            code = synthesize_voice(voice, prompt, env_file)
            if code != 0:
                failures += 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with (LOG_DIR / "bridge.log").open("a", encoding="utf-8") as log:
        log.write(f"[{stamp}] voices={len(voices)} synthesize={synthesize} failures={failures}\n")

    # Report metrics to Asana if configured
    if synthesize and _ASANA_REPORTER:
        _report_metrics_to_asana()

    print("✅ Safe Shadow Garden bridge complete.")
    print(f"   Prompts: {DATA_DIR}/")
    if synthesize:
        print(f"   Audio:   {VOICE_AGENT_DIR}/output/")
        if failures:
            print(f"   ⚠ {failures} synthesis run(s) failed.")
            return 1
    else:
        print("   Next: run with --synthesize for Grok voice WAV output.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Shadow Garden safe voice bridge v4.3")
    parser.add_argument(
        "--voices",
        help="Comma-separated voice list (default: Angela, Angela's Mom, Sue, …)",
    )
    parser.add_argument(
        "--synthesize",
        action="store_true",
        help="Run Grok Voice Agent text passes (uses local xAI env, not ElevenLabs)",
    )
    args = parser.parse_args()

    voices = DEFAULT_VOICES
    if args.voices:
        voices = [v.strip() for v in args.voices.split(",") if v.strip()]

    return cast_safe_scene(voices, synthesize=args.synthesize)


if __name__ == "__main__":
    raise SystemExit(main())