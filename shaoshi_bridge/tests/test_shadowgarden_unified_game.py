#!/usr/bin/env python3
"""Focused tests for shadowgarden_unified_game.py — stdlib unittest only."""
import json
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "south_star"))
from shadowgarden_unified_game import (
    DEFAULT_ACTIONS,
    MAX_TURNS,
    GameConfig,
    ShadowGardenUnifiedGame,
    main,
)


class TestDefaultSequence(unittest.TestCase):
    def test_default_sequence_completes(self):
        game = ShadowGardenUnifiedGame(GameConfig(seed=42, mastery_input=10))
        report = game.run(list(DEFAULT_ACTIONS))
        self.assertEqual(report["status"], "complete")
        self.assertEqual(report["final_state"], "complete")
        self.assertEqual(report["turns_used"], 5)
        self.assertEqual(len(report["events"]), 5)


class TestReplayDeterminism(unittest.TestCase):
    def test_identical_seed_config_actions_byte_equivalent(self):
        cfg = GameConfig(seed=7, mastery_input=6)
        r1 = ShadowGardenUnifiedGame(GameConfig(seed=cfg.seed, mastery_input=cfg.mastery_input)).run(
            ["launch", "correct", "hold", "land"])
        r2 = ShadowGardenUnifiedGame(GameConfig(seed=cfg.seed, mastery_input=cfg.mastery_input)).run(
            ["launch", "correct", "hold", "land"])
        self.assertEqual(
            json.dumps(r1, sort_keys=True),
            json.dumps(r2, sort_keys=True),
        )

    def test_different_seed_diverges(self):
        r1 = ShadowGardenUnifiedGame(GameConfig(seed=1)).run(list(DEFAULT_ACTIONS))
        r2 = ShadowGardenUnifiedGame(GameConfig(seed=2)).run(list(DEFAULT_ACTIONS))
        self.assertNotEqual(r1["final_resonance"], r2["final_resonance"])


class TestAbortPaths(unittest.TestCase):
    def test_illegal_transition_aborts(self):
        game = ShadowGardenUnifiedGame(GameConfig(seed=1))
        report = game.run(["land"])
        self.assertEqual(report["status"], "aborted")
        self.assertEqual(report["events"][-1]["to_state"], "aborted")
        self.assertEqual(report["events"][-1]["note"], "illegal transition")

    def test_manual_abort_action(self):
        game = ShadowGardenUnifiedGame(GameConfig(seed=1))
        report = game.run(["launch", "abort"])
        self.assertEqual(report["status"], "aborted")
        self.assertEqual(report["turns_used"], 2)
        self.assertEqual(report["events"][-1]["note"], "manual abort")

    def test_step_after_terminal_raises(self):
        game = ShadowGardenUnifiedGame(GameConfig(seed=1))
        game.run(["abort"])
        with self.assertRaises(RuntimeError):
            game.step("launch")


class TestTurnLimit(unittest.TestCase):
    def test_turn_limit_forces_abort(self):
        oscillation = ["launch"] + (["hold", "correct"] * 20)
        game = ShadowGardenUnifiedGame(GameConfig(seed=3))
        report = game.run(oscillation)
        self.assertEqual(report["status"], "aborted")
        self.assertLessEqual(report["turns_used"], MAX_TURNS)
        self.assertEqual(report["events"][-1]["note"], "turn limit reached")


class TestMasteryCap(unittest.TestCase):
    def test_mastery_input_capped_high(self):
        self.assertEqual(GameConfig(mastery_input=99).mastery_input, 10)

    def test_mastery_input_capped_low(self):
        self.assertEqual(GameConfig(mastery_input=-5).mastery_input, 0)


class TestEventHistory(unittest.TestCase):
    def test_every_transition_is_inspectable(self):
        game = ShadowGardenUnifiedGame(GameConfig(seed=42, mastery_input=10))
        report = game.run(list(DEFAULT_ACTIONS))
        for i, event in enumerate(report["events"], start=1):
            self.assertEqual(event["turn"], i)
            self.assertIn("from_state", event)
            self.assertIn("to_state", event)


class TestCLI(unittest.TestCase):
    def test_main_returns_zero_on_complete(self):
        self.assertEqual(main(["--seed", "42", "--mastery", "10", "--actions", *DEFAULT_ACTIONS]), 0)

    def test_main_returns_nonzero_on_abort(self):
        self.assertEqual(main(["--seed", "1", "--actions", "land"]), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
