import importlib.util
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))


def _load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


PP = _load("persona_pipeline")


class PersonaRegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = PP.build_registry()
        self.ids = {p["id"] for p in self.reg["personas"]}

    def test_guaranteed_personas_present(self):
        for pid in ("minnie", "sarah", "sophie"):
            self.assertIn(pid, self.ids)
        self.assertEqual(self.reg["guaranteed"], ["minnie", "sarah", "sophie"])

    def test_discovered_repo_nodes_preserved(self):
        for pid in ("hades", "angela", "lainie", "sophie", "addie", "sue",
                    "sabina", "sarah", "ivy", "shannon", "naomi", "julia"):
            self.assertIn(pid, self.ids)

    def test_no_invented_biography_or_relationships(self):
        for p in self.reg["personas"]:
            self.assertIsNone(p["biography"])
            self.assertEqual(p["relationships"], [])

    def test_personas_are_symbolic_only_no_authority(self):
        self.assertTrue(self.reg["symbolic_only"])
        for p in self.reg["personas"]:
            self.assertTrue(p["symbolic_only"])
            self.assertFalse(p["authority"])

    def test_deterministic_registry_hash(self):
        self.assertEqual(PP.build_registry()["signature"]["sha256"],
                         self.reg["signature"]["sha256"])

    def test_minnie_has_no_repo_provenance(self):
        minnie = next(p for p in self.reg["personas"] if p["id"] == "minnie")
        self.assertEqual(minnie["discovered_in"], ["revision_request_guarantee"])
        self.assertTrue(minnie["guaranteed"])

    def test_guarantees_hold_helper(self):
        self.assertTrue(PP.registry_guarantees_hold(self.reg))


class OpaquePointerTests(unittest.TestCase):
    def test_x_com_is_opaque_read_only(self):
        ptr = PP.opaque_pointer("https://x.com/handle")
        self.assertTrue(ptr["is_social"])
        self.assertTrue(ptr["read_only"])
        self.assertTrue(ptr["opaque"])
        self.assertEqual(ptr["action_taken"], "none")

    def test_instagram_is_opaque_read_only(self):
        ptr = PP.opaque_pointer("https://www.instagram.com/handle")
        self.assertTrue(ptr["is_social"])
        self.assertEqual(ptr["host"], "instagram.com")

    def test_no_social_action_enabled(self):
        ptr = PP.opaque_pointer("https://x.com/handle")
        for action, enabled in ptr["actions"].items():
            self.assertFalse(enabled, f"{action} must be disabled")
        self.assertIn("scrape", ptr["actions"])
        self.assertIn("dm", ptr["actions"])
        self.assertIn("credential_use", ptr["actions"])


class TelemetryClassifierTests(unittest.TestCase):
    def rec(self, **kw):
        base = {"node_id": "n", "evidence": [], "provenance": {}, "labels": [], "flags": {}}
        base.update(kw)
        return base

    def test_labels_alone_do_not_rank(self):
        c = PP.classify_record(self.rec(
            labels=["sovereign", "lattice", "11D", "grok", "makima", "seiko", "kaguya", "primordial"],
            provenance={"in_repo_config": True, "first_party": True, "hashed": True}))
        self.assertEqual(c["tier"], "provisional")
        self.assertTrue(c["symbolic_only_labels_ignored_for_ranking"])

    def test_single_evidence_provisional(self):
        c = PP.classify_record(self.rec(
            evidence=[{"kind": "loopback_probe", "ref": "a", "verified": True}]))
        self.assertEqual(c["tier"], "provisional")

    def test_two_evidence_corroborated(self):
        c = PP.classify_record(self.rec(evidence=[
            {"kind": "loopback_probe", "ref": "a", "verified": True},
            {"kind": "user_attestation", "ref": "b", "verified": True}]))
        self.assertEqual(c["tier"], "corroborated")

    def test_in_repo_corroborated_is_canonical(self):
        c = PP.classify_record(self.rec(
            provenance={"in_repo_config": True},
            evidence=[{"kind": "repo_config", "ref": "a", "verified": True},
                      {"kind": "loopback_probe", "ref": "b", "verified": True}]))
        self.assertEqual(c["tier"], "canonical")

    def test_first_party_hashed_canonical_is_primordial(self):
        c = PP.classify_record(self.rec(
            provenance={"in_repo_config": True, "first_party": True, "hashed": True},
            evidence=[{"kind": "repo_config", "ref": "a", "verified": True},
                      {"kind": "loopback_probe", "ref": "b", "verified": True}]))
        self.assertEqual(c["tier"], "primordial")

    def test_external_pointers_never_trusted(self):
        c = PP.classify_record(self.rec(evidence=[
            {"kind": "external_pointer", "ref": "https://x.com/x", "verified": True},
            {"kind": "external_pointer", "ref": "https://instagram.com/y", "verified": True}]))
        self.assertEqual(c["trusted_evidence"], 0)
        self.assertEqual(c["tier"], "provisional")

    def test_unverified_evidence_not_counted(self):
        c = PP.classify_record(self.rec(evidence=[
            {"kind": "loopback_probe", "ref": "a", "verified": False},
            {"kind": "repo_config", "ref": "b", "verified": False}]))
        self.assertEqual(c["trusted_evidence"], 0)

    def test_duplicate_evidence_does_not_inflate(self):
        c = PP.classify_record(self.rec(evidence=[
            {"kind": "loopback_probe", "ref": "a", "verified": True},
            {"kind": "loopback_probe", "ref": "a", "verified": True}]))
        self.assertEqual(c["trusted_evidence"], 1)
        self.assertEqual(c["tier"], "provisional")

    def test_real_person_likeness_quarantined(self):
        c = PP.classify_record(self.rec(
            flags={"real_person_likeness": True},
            provenance={"in_repo_config": True, "first_party": True, "hashed": True},
            evidence=[{"kind": "repo_config", "ref": "a", "verified": True},
                      {"kind": "loopback_probe", "ref": "b", "verified": True}]))
        self.assertEqual(c["tier"], "quarantine")

    def test_credential_flag_quarantined(self):
        c = PP.classify_record(self.rec(flags={"credential": True}))
        self.assertEqual(c["tier"], "quarantine")

    def test_conflict_flag_quarantined(self):
        c = PP.classify_record(self.rec(flags={"conflict": True}))
        self.assertEqual(c["tier"], "quarantine")

    def test_batch_deterministic_and_tallies(self):
        batch = {"records": [
            {"node_id": "b", "evidence": [{"kind": "repo_config", "ref": "1", "verified": True}]},
            {"node_id": "a", "evidence": []}]}
        r1 = PP.classify_telemetry(batch)
        r2 = PP.classify_telemetry(batch)
        self.assertEqual(r1["signature"]["sha256"], r2["signature"]["sha256"])
        self.assertEqual(r1["count"], 2)
        self.assertEqual(r1["externalRequests"], 0)


class WorkflowReferenceTests(unittest.TestCase):
    def test_models_bound_correctly(self):
        self.assertEqual(PP.workflow_reference("image")["workflow"]["model"], "Flux.1 Dev")
        self.assertEqual(PP.workflow_reference("video")["workflow"]["model"], "Wan 2.2")
        self.assertEqual(PP.workflow_reference("audio")["workflow"]["model"], "ACE-Step 1.5")

    def test_reference_only_no_downloads(self):
        for m in ("image", "video", "audio"):
            wf = PP.workflow_reference(m)
            self.assertTrue(wf["reference_only"])
            self.assertFalse(wf["model_downloads"])
            self.assertTrue(wf["queue_requires_user_approval"])
            self.assertTrue(wf["queue_requires_reviewed_workflow"])
            self.assertFalse(wf["unknown_custom_nodes_execute"])

    def test_allowed_hosts_loopback_only(self):
        wf = PP.workflow_reference("image")
        self.assertEqual(set(wf["allowed_hosts"]), {"127.0.0.1", "localhost"})


class WorkflowReviewGateTests(unittest.TestCase):
    def test_unknown_node_blocks(self):
        r = PP.review_workflow({"nodes": [{"class_type": "EvilNode"}],
                                "hosts": ["http://127.0.0.1:8188"], "reviewed": True}, approve=True)
        self.assertFalse(r["queueable"])
        self.assertIn("unknown_custom_nodes", r["blockers"])
        self.assertEqual(r["unknown_custom_nodes_executed"], 0)

    def test_model_download_blocks(self):
        r = PP.review_workflow({"nodes": [{"class_type": "KSampler"}],
                                "model_downloads": True, "reviewed": True}, approve=True)
        self.assertIn("model_download_requested", r["blockers"])

    def test_non_loopback_host_blocks(self):
        r = PP.review_workflow({"nodes": [{"class_type": "KSampler"}],
                                "hosts": ["http://10.0.0.5:8188"], "reviewed": True}, approve=True)
        self.assertIn("non_loopback_host", r["blockers"])

    def test_unreviewed_blocks(self):
        r = PP.review_workflow({"nodes": [{"class_type": "KSampler"}]}, approve=True)
        self.assertIn("workflow_not_reviewed", r["blockers"])

    def test_approval_required(self):
        r = PP.review_workflow({"nodes": [{"class_type": "KSampler"}],
                                "hosts": ["http://127.0.0.1:8188"], "reviewed": True}, approve=False)
        self.assertIn("approval_required", r["blockers"])

    def test_safe_reviewed_approved_is_queueable_not_auto_queued(self):
        r = PP.review_workflow({"nodes": [{"class_type": "KSampler"},
                                          {"class_type": "VAEDecode"}],
                                "hosts": ["http://127.0.0.1:8188"], "reviewed": True}, approve=True)
        self.assertTrue(r["queueable"])
        self.assertFalse(r["queued"])
        self.assertEqual(r["execution"], "local_queue_pending_user_run")


class SelfTestTests(unittest.TestCase):
    def test_self_test_passes(self):
        self.assertTrue(PP.run_self_test()["ok"])


if __name__ == "__main__":
    unittest.main()
