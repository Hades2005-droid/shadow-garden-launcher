# Eden Conductor — Perplexity-led Fable 5 + Devin

One goal, one seamless pipeline. **Perplexity leads**: it researches your goal,
splits it into tasks, delegates reasoning / authoring / review to **Claude
Fable 5** and long-horizon code execution to **Devin**, then synthesizes the
results into a final briefing.

```
                 +------------------------------+
   your goal --> |  PERPLEXITY  (lead)          |  research + plan (JSON)
                 +---------------+--------------+
                     +-----------+-----------+
                     v                       v
             +---------------+       +----------------+
             | CLAUDE FABLE 5|       |     DEVIN      |
             | reason/author |       | code execution |
             | /review       |       | (session URL)  |
             +-------+-------+       +-------+--------+
                     +-----------+-----------+
                                 v
                 +------------------------------+
                 |  PERPLEXITY (lead) synthesize| --> final briefing
                 +------------------------------+
```

## Run

```bash
python eden/conductor.py "add OAuth login to the web app"
python eden/conductor.py --wait "..."   # block until Devin sessions finish
python eden/conductor.py --json "..."    # machine-readable result on stdout
```

## Wiring (all optional; every provider degrades gracefully)

| Env var | Role | If missing |
|---|---|---|
| `PERPLEXITY_API_KEY` | Perplexity leads (plan + synthesis) | Fable 5 leads; else a static plan |
| `ANTHROPIC_API_KEY` / `ANTHROPIC_AUTH_TOKEN` | Claude Fable 5 reasoning/review | task becomes a handoff packet |
| `DEVIN_API_KEY` | Devin code execution | spec becomes a handoff packet |

With **no keys at all** the conductor still runs end-to-end: it prints the plan
and a handoff packet per task, so you always get a usable output.

## Files

```
eden/
  conductor.py   -> the orchestrator (Perplexity -> Fable 5 -> Devin -> synthesis)
  perplexity.py  -> Perplexity Sonar client (LEAD), stdlib-only
  devin.py       -> Devin v1 session client (EXECUTION), stdlib-only
  fable5.py      -> Claude Fable 5 client (REASONING), anthropic SDK
```

Only `fable5.py` needs a package (`pip install anthropic`). The Perplexity and
Devin clients use the Python standard library, so they run on a bare machine.

## Endpoints used

- **Perplexity**: `POST https://api.perplexity.ai/v1/sonar` — default model
  `sonar-reasoning-pro` (override with `PERPLEXITY_MODEL` / `PERPLEXITY_ENDPOINT`).
- **Devin**: `POST /v1/sessions`, `GET /v1/session/{id}`, `POST /v1/session/{id}/message`
  (base override with `DEVIN_BASE_URL`).
- **Fable 5**: `claude-fable-5` with server-side refusal fallback to `claude-opus-4-8`.

## Verified

Syntax-checked and dry-run end-to-end with no provider keys (exit 0): static plan,
per-task handoff packets, synthesis fallback, and clean JSON on stdout under
`--json` (progress is routed to stderr).

## Note on live calls

The dry-run path is fully verified here. The first *live* call needs the relevant
keys set and, for Fable 5, `pip install anthropic`. The Perplexity endpoint/model
and Devin session paths track the public docs as of July 2026; if a provider
changes a path, override it via the env vars above without touching code.
