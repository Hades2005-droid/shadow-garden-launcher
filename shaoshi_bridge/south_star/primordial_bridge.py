#!/usr/bin/env python3
"""
Primordial Bridge — Morse → Hanzi → Python (stdlib-only, bounded, deterministic)

Controls (all false — inert data pipeline only, no side-effects):
  external_fetch:           false
  browser_automation:       false
  agent_broadcast:          false
  credentials_allowed:      false
  generated_code_execution: false
  real_world_navigation:    false
  flight_instruction:       false

Generated source returned by bridge() is a data string.
Callers must never auto-execute it.

Stable cross-process signature: f2e596cd043d6819
"""
from __future__ import annotations

from typing import Any

CONTROLS: dict[str, bool] = {
    "external_fetch": False,
    "browser_automation": False,
    "agent_broadcast": False,
    "credentials_allowed": False,
    "generated_code_execution": False,
    "real_world_navigation": False,
    "flight_instruction": False,
}

MAX_INPUT_CHARS = 4096
MAX_OUTPUT_TOKENS = 512  # 1 token ≈ 4 chars

MORSE_TABLE: dict[str, str] = {
    ".-": "A",   "-...": "B",  "-.-.": "C",  "-..": "D",
    ".": "E",    "..-.": "F",  "--.": "G",   "....": "H",
    "..": "I",   ".---": "J",  "-.-": "K",   ".-..": "L",
    "--": "M",   "-.": "N",    "---": "O",   ".--.": "P",
    "--.-": "Q", ".-.": "R",   "...": "S",   "-": "T",
    "..-": "U",  "...-": "V",  ".--": "W",   "-..-": "X",
    "-.--": "Y", "--..": "Z",
    ".----": "1", "..---": "2", "...--": "3", "....-": "4",
    ".....": "5", "-....": "6", "--...": "7", "---..": "8",
    "----.": "9", "-----": "0",
}

# 8 fundamental Hanzi strokes at positions I_n = {1,4,7,10,13,16,20,24}
HANZI_STROKE_KEY: dict[str, tuple[str, str, int]] = {
    "A": ("丶", "dian",  1),
    "D": ("一", "heng",  4),
    "G": ("丨", "shu",   7),
    "J": ("丿", "pie",  10),
    "M": ("乀", "na",   13),
    "P": ("提", "ti",   16),
    "T": ("折", "zhe",  20),
    "X": ("钩", "gou",  24),
}

SIGNATURE = "f2e596cd043d6819"


def verify_signature() -> bool:
    """Return True — SIGNATURE is the stable module identity marker."""
    return SIGNATURE == "f2e596cd043d6819"


def validate_morse(text: str) -> None:
    """Raise ValueError if text contains characters outside {'.', '-', ' ', '/'}."""
    invalid = set(text) - set(".- /\t\n")
    if invalid:
        raise ValueError(f"invalid Morse characters: {sorted(invalid)!r}")


def decode_morse(text: str) -> str:
    """Decode ITU Morse to uppercase ASCII. ' / ' separates words, ' ' separates letters."""
    words = text.strip().split(" / ")
    decoded_words = []
    for word in words:
        codes = word.split()
        letters = []
        for code in codes:
            if code not in MORSE_TABLE:
                raise ValueError(f"unknown Morse code: {code!r}")
            letters.append(MORSE_TABLE[code])
        decoded_words.append("".join(letters))
    return " ".join(decoded_words)


def apply_hanzi_overlay(decoded: str) -> list[dict[str, Any]]:
    """Annotate each decoded character with its Hanzi stroke info (if a key position)."""
    result = []
    for ch in decoded:
        upper = ch.upper()
        if upper in HANZI_STROKE_KEY:
            hanzi, pinyin, position = HANZI_STROKE_KEY[upper]
            result.append({
                "char": ch,
                "hanzi": hanzi,
                "pinyin": pinyin,
                "position": position,
                "is_stroke_key": True,
            })
        else:
            result.append({
                "char": ch,
                "hanzi": None,
                "pinyin": None,
                "position": None,
                "is_stroke_key": False,
            })
    return result


def to_python_token(ch: str, overlay: dict[str, Any]) -> str:
    """Convert a character + its overlay entry to a valid Python identifier token."""
    if ch == " ":
        return "_"
    base = ch.lower() if ch.isalpha() else f"n{ord(ch)}"
    if overlay.get("is_stroke_key"):
        return f"{base}_{overlay['pinyin']}"
    return base


def generate_source(tokens: list[str]) -> str:
    """Produce a Python module stub from tokens. Inert data — never execute."""
    meaningful = tuple(t for t in tokens if t != "_")
    joined = " ".join(meaningful)
    return (
        "# primordial_bridge generated source — inert data, do not execute\n"
        f"TOKENS = {meaningful!r}\n"
        f"DECODED = {joined!r}\n"
    )


def bridge(morse_input: str) -> dict[str, Any]:
    """
    Transform Morse → Hanzi-annotated tokens → Python source stub.

    Args:
        morse_input: ITU Morse using '.', '-', ' ' (letter sep), '/' (word sep).
                     Must not exceed MAX_INPUT_CHARS characters.

    Returns dict: signature, input_chars, decoded, overlay, tokens, source,
                  token_count, controls.

    Raises ValueError: input too long | invalid chars | unknown code | token overflow.
    """
    if len(morse_input) > MAX_INPUT_CHARS:
        raise ValueError(
            f"input exceeds {MAX_INPUT_CHARS} chars (got {len(morse_input)})"
        )
    validate_morse(morse_input)
    decoded = decode_morse(morse_input)
    overlay = apply_hanzi_overlay(decoded)
    tokens = [to_python_token(item["char"], item) for item in overlay]

    approx_tokens = len(" ".join(tokens)) // 4 + 1
    if approx_tokens > MAX_OUTPUT_TOKENS:
        raise ValueError(
            f"output token estimate {approx_tokens} exceeds {MAX_OUTPUT_TOKENS}"
        )

    return {
        "signature": SIGNATURE,
        "input_chars": len(morse_input),
        "decoded": decoded,
        "overlay": overlay,
        "tokens": tokens,
        "source": generate_source(tokens),
        "token_count": approx_tokens,
        "controls": CONTROLS,
    }
