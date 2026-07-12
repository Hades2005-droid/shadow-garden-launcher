import copy
import importlib.util
import json
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("orchestrator.py")
SPEC = importlib.util.spec_from_file_location("orchestrator", MODULE_PATH)
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)

FIXED = "2026-07-12T00:00:00Z"


def source():
    return json.loads(Path(__file__).with_name("orchestrator_source.json").read_text())


class SourceContractTests(unittest.TestCase):
    def test_source_contract_passes(self):
        self.assertEqual(MOD.validate_source(source()), [])

    def test_missing_role_rejected(self):
        bad = copy.deepcopy(source())
        bad["roles"] = ["unification_target"]
        self.assertIn("missing_role:fable5_comfyui_open_merge_target",
                      MOD.validate_source(bad))

    def test_wrong_canonical_task_id_rejected(self):
        bad = copy.deepcopy(source())
        bad["canonical_unification_task_id"] = "deadbeef"
        self.assertIn("unexpected_canonical_task_id", MOD.validate_source(bad))

    def test_policy_must_be_pointer_only(self):
        bad = copy.deepcopy(source())
        bad["policy"] = "scrape_everything"
        self.assertIn("policy_must_be_no_scrape_pointer_only", MOD.validate_source(bad))

    def test_endpoints_must_be_loopback(self):
        bad = copy.deepcopy(source())
        bad["endpoints"]["comfyui"]["host"] = "0.0.0.0"
        self.assertIn("endpoint_not_loopback:comfyui", MOD.validate_source(bad))

    def test_comfyui_health_path_is_system_stats(self):
        bad = copy.deepcopy(source())
        bad["endpoints"]["comfyui"]["health_path"] = "/"
        self.assertIn("comfyui_health_path_must_be_system_stats",
                      MOD.validate_source(bad))

    def test_controls_cannot_enable_external_write(self):
        bad = copy.deepcopy(source())
        bad["controls"]["external_write"] = True
        self.assertIn("control_mismatch:external_write", MOD.validate_source(bad))

    def test_controls_cannot_enable_training(self):
        bad = copy.deepcopy(source())
        bad["controls"]["training_allowed"] = True
        self.assertIn("control_mismatch:training_allowed", MOD.validate_source(bad))

    def test_media_default_must_be_manifest_only(self):
        bad = copy.deepcopy(source())
        bad["media"]["default_mode"] = "render"
        self.assertIn("media_default_mode_must_be_manifest_only",
                      MOD.validate_source(bad))


class ManifestGateTests(unittest.TestCase):
    def payload(self, **kw):
        base = {"spell": "violet lattice harmony field, temperance 14, soft bloom",
                "medium": "image"}
        base.update(kw)
        return base

    def test_default_is_manifest_only(self):
        m = MOD.compile_job_manifest(self.payload(), ts=FIXED)
        self.assertEqual(m["executionMode"], "manifest_only")
        self.assertFalse(m["queued"])
        self.assertEqual(m["externalRequests"], 0)
        self.assertFalse(m["trainingAllowed"])

    def test_deterministic(self):
        a = MOD.compile_job_manifest(self.payload(), ts=FIXED)
        b = MOD.compile_job_manifest(self.payload(), ts=FIXED)
        self.assertEqual(MOD.canonical(a), MOD.canonical(b))
        self.assertEqual(a["signature"]["sha256"], b["signature"]["sha256"])

    def test_approve_alone_does_not_queue(self):
        m = MOD.compile_job_manifest(self.payload(approve=True), ts=FIXED)
        self.assertFalse(m["queued"])
        self.assertEqual(m["executionMode"], "manifest_only")

    def test_approve_plus_queue_is_local_only(self):
        m = MOD.compile_job_manifest(
            self.payload(approve=True, executionMode="queue"), ts=FIXED)
        self.assertTrue(m["queued"])
        self.assertEqual(m["executionMode"], "local_queue_pending_user_run")
        self.assertEqual(m["externalRequests"], 0)

    def test_video_over_30s_rejected(self):
        m = MOD.compile_job_manifest(
            self.payload(medium="video", durationSeconds=45), ts=FIXED)
        self.assertIn("video_duration_exceeds_max", m["failures"])
        self.assertFalse(m["ready"])

    def test_video_within_30s_ok(self):
        m = MOD.compile_job_manifest(
            self.payload(medium="video", durationSeconds=20), ts=FIXED)
        self.assertNotIn("video_duration_exceeds_max", m["failures"])

    def test_real_person_likeness_refused(self):
        m = MOD.compile_job_manifest(self.payload(likeness_of="a real named person"),
                                     ts=FIXED)
        self.assertIn("real_person_likeness_refused", m["failures"])
        self.assertFalse(m["ready"])

    def test_no_auto_weight_download(self):
        m = MOD.compile_job_manifest(self.payload(model="some-open-weight"), ts=FIXED)
        self.assertFalse(m["weights"]["auto_download"])
        self.assertEqual(m["weights"]["model"], "some-open-weight")

    def test_references_are_pointer_only(self):
        m = MOD.compile_job_manifest(
            self.payload(references=["https://example.invalid/x"]), ts=FIXED)
        self.assertTrue(m["references"])
        self.assertFalse(m["references"][0]["scraped"])
        self.assertEqual(m["references"][0]["action_taken"], "none")

    def test_physics_and_symbolic_are_separate(self):
        m = MOD.compile_job_manifest(self.payload(), ts=FIXED)
        self.assertFalse(m["physics"]["symbolic_only"])
        self.assertTrue(m["symbolic"]["symbolic_only"])
        self.assertNotEqual(m["physics"]["namespace"], m["symbolic"]["namespace"])

    def test_gate_holds_unapproved(self):
        m = MOD.compile_job_manifest(self.payload(), ts=FIXED)
        g = MOD.gate(m)
        self.assertFalse(g["queue_allowed"])
        self.assertTrue(g["held_for_user_approval"])
        self.assertEqual(g["external_actions_executed"], 0)
        self.assertEqual(g["weight_downloads_executed"], 0)


class HealthAndRunTests(unittest.TestCase):
    def test_health_loopback_only_deterministic(self):
        h = MOD.health(source(), probe=False, ts=FIXED)
        self.assertTrue(h["loopback_only"])
        self.assertEqual(h["externalRequests"], 0)
        self.assertEqual(set(h["services"]), {"fable5", "comfyui", "eden"})

    def test_run_emits_bounded_packet(self):
        packet = MOD.run(probe=False, ts=FIXED)
        self.assertEqual(packet["status"], "processed")
        self.assertEqual(
            packet["sequence"],
            ["observe", "validate", "health", "compile", "gate", "emit"])
        history = json.loads((MOD.STATE / "history.json").read_text())
        self.assertLessEqual(len(history), MOD.MAX_HISTORY)
        self.assertFalse(packet["controls"]["agent_broadcast"])
        self.assertFalse(packet["controls"]["auto_weight_downloads"])

    def test_self_test_passes(self):
        result = MOD.run_self_test()
        self.assertTrue(result["ok"])


if __name__ == "__main__":
    unittest.main()
