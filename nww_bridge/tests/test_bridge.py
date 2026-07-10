"""Mocked tests for the Perplexity bridge. No live network calls, ever."""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from contract import validate, classify_health, AgentResult, INTENTS  # noqa: E402
from perplexity_bridge import PerplexityBridge  # noqa: E402
from router import Router  # noqa: E402


def fake_transport(status, payload, capture=None):
    def _t(url, headers, body, timeout):
        if capture is not None:
            capture["url"] = url
            capture["headers"] = headers
            capture["body"] = body
        return status, payload
    return _t


SONAR_OK = {"choices": [{"message": {"content": "The answer is 42."}}],
            "citations": ["https://example.com/a"]}


class TestContract(unittest.TestCase):
    def test_valid_success_result(self):
        r = AgentResult(agent="perplexity", status="success",
                        summary="ok", trace_id="t1").to_dict()
        ok, errors = validate(r)
        self.assertTrue(ok, errors)

    def test_error_absent_on_success(self):
        r = AgentResult(agent="a", status="success", summary="s",
                        trace_id="t").to_dict()
        self.assertNotIn("error", r)

    def test_blocked_requires_error(self):
        r = AgentResult(agent="a", status="blocked", summary="s",
                        trace_id="t").to_dict()
        ok, errors = validate(r)
        self.assertFalse(ok)
        self.assertTrue(any("error required" in e for e in errors))

    def test_bad_status_rejected(self):
        r = AgentResult(agent="a", status="exploded", summary="s",
                        trace_id="t").to_dict()
        ok, _ = validate(r)
        self.assertFalse(ok)

    def test_bad_error_class_rejected(self):
        r = {"contract_version": "1.0", "agent": "a", "run_id": "r",
             "trace_id": "t", "status": "blocked", "summary": "s",
             "ts_start": "x", "ts_end": "y",
             "error": {"class": "kaboom"}}
        ok, errors = validate(r)
        self.assertFalse(ok)
        self.assertTrue(any("error.class" in e for e in errors))

    def test_health_fresh_is_up(self):
        self.assertEqual(
            classify_health("2026-07-08T00:00:00Z", "2026-07-08T00:01:00Z"), "up")

    def test_health_stale_is_degraded_then_down(self):
        self.assertEqual(
            classify_health("2026-07-08T00:00:00Z", "2026-07-08T00:03:00Z"), "degraded")
        self.assertEqual(
            classify_health("2026-07-08T00:00:00Z", "2026-07-08T01:00:00Z"), "down")

    def test_health_missing_is_down(self):
        self.assertEqual(classify_health(None), "down")


class TestBridgeMock(unittest.TestCase):
    def test_mock_mode_no_key(self):
        b = PerplexityBridge(api_key=None)
        self.assertTrue(b.mock_mode)
        r = b.research("hello?")
        self.assertEqual(r.status, "success")
        self.assertEqual(r.output["mode"], "mock")
        ok, errors = validate(r.to_dict())
        self.assertTrue(ok, errors)

    def test_empty_question_blocked(self):
        b = PerplexityBridge(api_key=None)
        r = b.research("   ")
        self.assertEqual(r.status, "blocked")
        self.assertEqual(r.error["class"], "invalid_input")


class TestBridgeLive(unittest.TestCase):
    def _bridge(self, status, payload, capture=None):
        return PerplexityBridge(api_key="secret-key-123",
                                transport=fake_transport(status, payload, capture))

    def test_live_success(self):
        cap = {}
        b = self._bridge(200, SONAR_OK, cap)
        self.assertFalse(b.mock_mode)
        r = b.research("q", trace_id="trace-1")
        self.assertEqual(r.status, "success")
        self.assertEqual(r.output["answer"], "The answer is 42.")
        self.assertEqual(r.output["citations"], ["https://example.com/a"])
        self.assertEqual(r.trace_id, "trace-1")
        # Key is sent in the Authorization header...
        self.assertIn("secret-key-123", cap["headers"]["Authorization"])

    def test_key_never_serialized(self):
        b = self._bridge(200, SONAR_OK)
        r = b.research("q")
        self.assertNotIn("secret-key-123", str(r.to_dict()))

    def test_auth_error_maps(self):
        b = self._bridge(401, {"error": "bad token"})
        r = b.research("q")
        self.assertEqual(r.status, "blocked")
        self.assertEqual(r.error["class"], "auth_error")

    def test_rate_limit_maps(self):
        r = self._bridge(429, {}).research("q")
        self.assertEqual(r.error["class"], "rate_limited")

    def test_upstream_5xx_maps(self):
        r = self._bridge(503, {}).research("q")
        self.assertEqual(r.error["class"], "upstream_error")

    def test_bad_shape_is_contract_mismatch(self):
        r = self._bridge(200, {"nonsense": True}).research("q")
        self.assertEqual(r.error["class"], "contract_mismatch")

    def test_network_error_maps(self):
        import urllib.error

        def boom(*a, **k):
            raise urllib.error.URLError("no route to host")
        b = PerplexityBridge(api_key="k", transport=boom)
        r = b.research("q")
        self.assertEqual(r.error["class"], "network_error")

    def test_redaction_in_error_detail(self):
        import urllib.error

        def boom(*a, **k):
            raise urllib.error.URLError("failed with secret-key-123 in msg")
        b = PerplexityBridge(api_key="secret-key-123", transport=boom)
        r = b.research("q")
        self.assertNotIn("secret-key-123", str(r.to_dict()))


class TestRouter(unittest.TestCase):
    def test_route_and_log_chain(self):
        bridge = PerplexityBridge(api_key=None)  # mock
        with tempfile.NamedTemporaryFile("r", suffix=".jsonl", delete=False) as fh:
            log_path = fh.name
        router = Router(log_path=log_path)
        router.register("web_research",
                        lambda q, tid: bridge.research(q, trace_id=tid))
        chain = router.run("web_research", "what is the mesh?")
        self.assertEqual(len(chain), 1)
        self.assertTrue(chain[0]["_valid"])
        with open(log_path) as f:
            self.assertEqual(len(f.readlines()), 1)
        os.unlink(log_path)

    def test_unroutable_intent(self):
        router = Router()
        chain = router.run("nonexistent-intent", "q")
        self.assertEqual(chain[0]["status"], "blocked")
        self.assertEqual(chain[0]["error"]["class"], "not_implemented")

    def test_handoff_follows_chain(self):
        bridge = PerplexityBridge(api_key=None)
        router = Router()
        # research hands off to code_review
        router.register(
            "web_research",
            lambda q, tid: bridge.research(q, trace_id=tid,
                                           handoff_to="claude",
                                           handoff_intent="code_review"))
        reviewed = {"n": 0}

        def reviewer(q, tid):
            reviewed["n"] += 1
            return AgentResult(agent="claude", status="success",
                               summary="reviewed", trace_id=tid)
        router.register("code_review", reviewer)
        chain = router.run("web_research", "q")
        self.assertEqual(len(chain), 2)
        self.assertEqual(reviewed["n"], 1)
        self.assertTrue(all(c["_valid"] for c in chain))
        # trace_id stable across the hop
        self.assertEqual(chain[0]["trace_id"], chain[1]["trace_id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
