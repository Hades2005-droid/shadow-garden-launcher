# Eden — the Shadow Garden launch layer

One input, launches everywhere. This package is the hub of the Eden
constellation: it fires the catalyst artifact and, from a single command, wakes
the sibling repos and briefs the whole run through **Claude Fable 5**.

```
eden/
  index.html   →  the catalyst — a self-contained burst-alpha physics field
  launch.py    →  one-input launcher (opens the artifact + dispatches siblings + Fable 5 briefing)
  fable5.py    →  native communication layer to Claude Fable 5
```

## One input

```bash
python eden/launch.py "ignite"
```

That single command:

1. **Opens `eden/index.html`** in your browser — the EDEN burst-alpha physics
   field: real elastic-collision physics, an auto-recursive burst loop, and
   live telemetry data everywhere (energy, momentum, velocities, FPS,
   collisions) plus a streaming field console.
2. **Dispatches the same input** to sibling Eden repos when they are cloned
   next to this one:
   - `../wha-spell-simulator` → `node eden/eden_spell.mjs "<input>"`
   - `../gitmynotes` → `python eden/eden_notes.py "<input>"`
3. **Asks Fable 5 for a launch briefing** (only if an API key is set).

Everything degrades gracefully — a missing sibling repo, a missing Node runtime,
or an unset API key is reported and skipped. The launch still fires.

## Fable 5 native comms

`fable5.py` is the one place the Eden stack talks to Anthropic's Claude Fable 5,
so behaviour stays identical across all three repos. It defaults to
`claude-fable-5` and opts into a **server-side refusal fallback** to
`claude-opus-4-8`, so a safety decline is re-served inside the same call.

```python
from eden.fable5 import Fable5
print(Fable5().ask("Give me a one-line status for Shadow Garden."))
```

Set up auth first:

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...   # or run: ant auth login
```

## Honest scope

- **The artifact is a real, self-contained web page.** Its physics runs in the
  browser in JavaScript — not Python — because a page has no Python runtime.
- **"Launches everywhere" = orchestrated subprocess dispatch** to the sibling
  repos on your machine. It is not a hosted service and does not reach machines
  you have not cloned the repos onto.
- **Fable 5 comms require your own API key.** No key is bundled; nothing calls
  out unless you set one.

The matching `eden/fable5` client and per-repo hooks live in
`wha-spell-simulator` and `gitmynotes` on the same branch.
