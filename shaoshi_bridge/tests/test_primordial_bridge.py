#!/usr/bin/env python3
"""33 tests for primordial_bridge — stdlib unittest only."""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "south_star"))
from primordial_bridge import (
    CONTROLS, HANZI_STROKE_KEY, MAX_INPUT_CHARS, MAX_OUTPUT_TOKENS,
    SIGNATURE, apply_hanzi_overlay, bridge, decode_morse,
    generate_source, to_python_token, validate_morse, verify_signature,
)


class TestControls(unittest.TestCase):
    def test_external_fetch_false(self):       self.assertIs(CONTROLS["external_fetch"], False)
    def test_browser_automation_false(self):   self.assertIs(CONTROLS["browser_automation"], False)
    def test_agent_broadcast_false(self):      self.assertIs(CONTROLS["agent_broadcast"], False)
    def test_credentials_allowed_false(self):  self.assertIs(CONTROLS["credentials_allowed"], False)
    def test_generated_code_exec_false(self):  self.assertIs(CONTROLS["generated_code_execution"], False)
    def test_real_world_nav_false(self):       self.assertIs(CONTROLS["real_world_navigation"], False)
    def test_flight_instruction_false(self):   self.assertIs(CONTROLS["flight_instruction"], False)


class TestSignature(unittest.TestCase):
    def test_signature_constant(self):  self.assertEqual(SIGNATURE, "f2e596cd043d6819")
    def test_verify_signature(self):    self.assertTrue(verify_signature())


class TestBounds(unittest.TestCase):
    def test_short_input_ok(self):
        self.assertEqual(bridge(".-")["decoded"], "A")

    def test_input_too_long_raises(self):
        with self.assertRaises(ValueError) as ctx:
            bridge("." * (MAX_INPUT_CHARS + 1))
        self.assertIn(str(MAX_INPUT_CHARS), str(ctx.exception))

    def test_many_tokens_raises(self):
        long_morse = " ".join(["."] * 2048)
        with self.assertRaises(ValueError):
            bridge(long_morse)


class TestMorse(unittest.TestCase):
    def test_decode_single_letter(self):   self.assertEqual(decode_morse(".-"),           "A")
    def test_decode_sos(self):             self.assertEqual(decode_morse("... --- ..."),   "SOS")
    def test_decode_word_sep(self):        self.assertEqual(decode_morse(". / .."),        "E I")
    def test_decode_number(self):          self.assertEqual(decode_morse(".----"),          "1")
    def test_invalid_char_raises(self):
        with self.assertRaises(ValueError): validate_morse("abc")
    def test_unknown_code_raises(self):
        with self.assertRaises(ValueError): decode_morse("......")


class TestHanziOverlay(unittest.TestCase):
    def test_a_is_stroke_key(self):   self.assertTrue(apply_hanzi_overlay("A")[0]["is_stroke_key"])
    def test_a_hanzi(self):           self.assertEqual(apply_hanzi_overlay("A")[0]["hanzi"], "丶")
    def test_a_pinyin(self):          self.assertEqual(apply_hanzi_overlay("A")[0]["pinyin"], "dian")
    def test_a_position(self):        self.assertEqual(apply_hanzi_overlay("A")[0]["position"], 1)
    def test_d_hanzi(self):           self.assertEqual(apply_hanzi_overlay("D")[0]["hanzi"], "一")
    def test_d_position(self):        self.assertEqual(apply_hanzi_overlay("D")[0]["position"], 4)
    def test_x_hanzi(self):           self.assertEqual(apply_hanzi_overlay("X")[0]["hanzi"], "钩")
    def test_x_position(self):        self.assertEqual(apply_hanzi_overlay("X")[0]["position"], 24)
    def test_b_not_stroke_key(self):  self.assertFalse(apply_hanzi_overlay("B")[0]["is_stroke_key"])


class TestTokenGeneration(unittest.TestCase):
    def test_stroke_key_gets_pinyin_suffix(self):
        self.assertEqual(to_python_token("A", {"is_stroke_key": True, "pinyin": "dian"}), "a_dian")

    def test_regular_letter_unchanged(self):
        self.assertEqual(to_python_token("B", {"is_stroke_key": False, "pinyin": None}), "b")

    def test_space_becomes_underscore(self):
        self.assertEqual(to_python_token(" ", {"is_stroke_key": False, "pinyin": None}), "_")


class TestBridgePipeline(unittest.TestCase):
    def test_result_signature(self):
        self.assertEqual(bridge(".-")["signature"], "f2e596cd043d6819")

    def test_result_has_decoded(self):
        self.assertIn("decoded", bridge(".-"))

    def test_result_controls_external_fetch(self):
        self.assertFalse(bridge(".-")["controls"]["external_fetch"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
