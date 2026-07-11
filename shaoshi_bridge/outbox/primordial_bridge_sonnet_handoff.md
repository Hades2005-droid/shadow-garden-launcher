# Primordial Bridge — Sonnet Handoff

**Branch:** `claude/nww-asana-connector-2gst3u`
**Signature:** `f2e596cd043d6819`
**Tests:** 45/45 pass (33 bridge + 12 game engine)

## Delivered Modules

| Module | Location | Purpose |
|--------|----------|---------|
| `primordial_bridge.py` | `south_star/` | Morse→Hanzi→Python pipeline |
| `shadowgarden_unified_game.py` | `south_star/` | Deterministic state-machine game |
| `devin_gift_taker.py` | `south_star/` | Bridge readiness observer + gift acceptance |

## Pipeline: Morse → Hanzi → Python

1. **validate_morse** — rejects any char outside `{. - / space}`
2. **decode_morse** — ITU table, `' / '` = word separator
3. **apply_hanzi_overlay** — annotates 8 stroke-key letters (A,D,G,J,M,P,T,X) with hanzi, pinyin, position
4. **to_python_token** — stroke-key letters get `letter_pinyin` suffix; spaces become `_`
5. **generate_source** — wraps tokens as inert Python module stub (never executed)

## Hanzi Stroke Positions

| Letter | Hanzi | Pinyin | Position |
|--------|-------|--------|----------|
| A | 丶 | dian | 1 |
| D | 一 | heng | 4 |
| G | 丨 | shu | 7 |
| J | 丿 | pie | 10 |
| M | 乀 | na | 13 |
| P | 提 | ti | 16 |
| T | 折 | zhe | 20 |
| X | 钩 | gou | 24 |

## Game Engine Verification Vectors

| Config | Actions | Status | Turns | Final Resonance |
|--------|---------|--------|-------|-----------------|
| seed=42, mastery=10 | launch hold correct hold land | complete | 5 | 10.298 |
| seed=1 | land | aborted | 1 | (illegal transition) |
| seed=1 | launch abort | aborted | 2 | (manual abort) |
| seed=3 | oscillation ×20 | aborted | ≤24 | (turn limit) |

## Controls (all false)

`external_fetch` · `browser_automation` · `agent_broadcast` ·
`credentials_allowed` · `generated_code_execution` ·
`real_world_navigation` · `flight_instruction`

Generated source is inert data — never auto-executed.
