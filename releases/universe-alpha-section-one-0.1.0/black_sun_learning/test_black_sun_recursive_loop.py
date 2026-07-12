import copy
import importlib.util
import json
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("black_sun_recursive_loop.py")
SPEC = importlib.util.spec_from_file_location("black_sun_recursive_loop", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


def source():
    return json.loads(Path(__file__).with_name("section_one_source.json").read_text())


class BlackSunLoopTests(unittest.TestCase):
    def test_source_contract_passes(self):
        self.assertEqual(MOD.validate_source(source()), [])

    def test_wrong_node_count_rejected(self):
        bad = copy.deepcopy(source())
        bad["section_one"]["node_count"] = 21
        self.assertIn("node_count_must_equal_22", MOD.validate_source(bad))

    def test_controls_cannot_grant_external_write(self):
        bad = copy.deepcopy(source())
        bad["controls"]["external_write"] = True
        self.assertIn("control_mismatch:external_write", MOD.validate_source(bad))

    def test_routing_contract_is_exact(self):
        bad = copy.deepcopy(source())
        bad["routing"]["cross_type"] = "lunar"
        self.assertIn("routing_contract_mismatch", MOD.validate_source(bad))

    def test_gate_holds_external_actions(self):
        gated = MOD.gate(MOD.propose(source(), {"missing": []}))
        self.assertEqual(gated["external_actions_executed"], 0)
        self.assertEqual(gated["source_mutations_executed"], 0)
        self.assertTrue(
            all(p["requires_human_approval"] for p in gated["held_for_user_approval"])
        )

    def test_run_is_bounded_and_emits_packet(self):
        packet = MOD.run()
        self.assertEqual(packet["status"], "processed")
        self.assertEqual(
            packet["sequence"],
            ["observe", "validate", "compare", "propose", "gate", "emit"],
        )
        history = json.loads((MOD.STATE / "history.json").read_text())
        self.assertLessEqual(len(history), MOD.MAX_HISTORY)
        self.assertFalse(packet["controls"]["agent_broadcast"])


if __name__ == "__main__":
    unittest.main()
