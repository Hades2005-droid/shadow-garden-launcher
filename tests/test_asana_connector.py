#!/usr/bin/env python3
"""Unit tests for the NWW Asana Connector.

All Asana HTTP calls are mocked by default. Live calls only run when
RUN_LIVE_ASANA_TESTS=1 is set (and are skipped otherwise).
"""
import io
import json
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asana_connector import (  # noqa: E402
    AsanaConfig,
    AsanaConfigError,
    AsanaConnector,
    sanitize_text,
)


def _fake_response(payload: dict):
    """Build a context-manager stub mimicking urllib's response object."""
    body = json.dumps(payload).encode("utf-8")
    cm = mock.MagicMock()
    cm.__enter__.return_value.read.return_value = body
    cm.__exit__.return_value = False
    return cm


class ConfigTests(unittest.TestCase):
    def test_disabled_without_token(self):
        cfg = AsanaConfig.from_env({})
        self.assertFalse(cfg.enabled)
        with self.assertRaises(AsanaConfigError):
            cfg.require_enabled()

    def test_enabled_with_token(self):
        cfg = AsanaConfig.from_env({"ASANA_ACCESS_TOKEN": "tok"})
        self.assertTrue(cfg.enabled)
        cfg.require_enabled()  # should not raise

    def test_reads_all_fields(self):
        cfg = AsanaConfig.from_env(
            {
                "ASANA_ACCESS_TOKEN": "tok",
                "ASANA_WORKSPACE_ID": "ws1",
                "ASANA_PROJECT_SHADOWGARDEN": "proj1",
                "ASANA_BASE_URL": "https://example.test/api",
            }
        )
        self.assertEqual(cfg.workspace_id, "ws1")
        self.assertEqual(cfg.project_id, "proj1")
        self.assertEqual(cfg.base_url, "https://example.test/api")

    def test_blank_base_url_falls_back_to_default(self):
        cfg = AsanaConfig.from_env({"ASANA_ACCESS_TOKEN": "t", "ASANA_BASE_URL": ""})
        self.assertTrue(cfg.base_url.startswith("https://app.asana.com"))


class SanitizeTests(unittest.TestCase):
    def test_redacts_api_key_assignment(self):
        out = sanitize_text("here XAI_API_KEY=xai-abcdef0123456789abcdef done")
        self.assertNotIn("xai-abcdef", out)
        self.assertIn("[REDACTED]", out)

    def test_redacts_bare_sk_token(self):
        out = sanitize_text("token sk-0123456789abcdefABCD here")
        self.assertNotIn("sk-0123456789", out)

    def test_redacts_email(self):
        out = sanitize_text("contact alice@example.com now")
        self.assertNotIn("alice@example.com", out)

    def test_clamps_length(self):
        out = sanitize_text("a" * 5000, max_chars=100)
        self.assertLessEqual(len(out), 100)
        self.assertTrue(out.endswith("…"))

    def test_empty(self):
        self.assertEqual(sanitize_text(""), "")


class ConnectorTests(unittest.TestCase):
    def setUp(self):
        self.cfg = AsanaConfig.from_env(
            {
                "ASANA_ACCESS_TOKEN": "secret-token",
                "ASANA_WORKSPACE_ID": "ws1",
                "ASANA_PROJECT_SHADOWGARDEN": "proj1",
            }
        )
        self.opener = mock.MagicMock(return_value=_fake_response({"data": {"gid": "123"}}))
        self.conn = AsanaConnector(self.cfg, _opener=self.opener)

    def _sent_request(self):
        self.assertTrue(self.opener.called)
        return self.opener.call_args.args[0]

    def test_create_task_posts_with_auth_and_payload(self):
        result = self.conn.create_task("hello", "world")
        self.assertEqual(result["data"]["gid"], "123")
        req = self._sent_request()
        self.assertEqual(req.method, "POST")
        self.assertTrue(req.full_url.endswith("/tasks"))
        self.assertEqual(req.get_header("Authorization"), "Bearer secret-token")
        payload = json.loads(req.data.decode("utf-8"))["data"]
        self.assertEqual(payload["name"], "hello")
        self.assertEqual(payload["projects"], ["proj1"])
        self.assertEqual(payload["workspace"], "ws1")

    def test_token_never_appears_in_payload(self):
        self.conn.create_task("t", "n")
        body = self._sent_request().data.decode("utf-8")
        self.assertNotIn("secret-token", body)

    def test_report_voice_synthesis(self):
        self.conn.report_voice_synthesis("Angela", latency_ms=812.4, quality=0.93)
        payload = json.loads(self._sent_request().data.decode("utf-8"))["data"]
        self.assertIn("Angela", payload["name"])
        self.assertIn("812", payload["name"])
        self.assertIn("0.930", payload["notes"])

    def test_report_grok_sync(self):
        self.conn.report_grok_sync("ok", 42, detail="synced fine")
        payload = json.loads(self._sent_request().data.decode("utf-8"))["data"]
        self.assertIn("42 msgs", payload["name"])
        self.assertIn("ok", payload["notes"])

    def test_report_conversation_summary_sanitizes(self):
        self.conn.report_conversation_summary(
            "Nightly", "user said XAI_API_KEY=xai-abcdef0123456789 secret", message_count=3
        )
        payload = json.loads(self._sent_request().data.decode("utf-8"))["data"]
        self.assertNotIn("xai-abcdef", payload["notes"])
        self.assertIn("[REDACTED]", payload["notes"])

    def test_disabled_connector_raises_and_makes_no_call(self):
        cfg = AsanaConfig.from_env({})
        conn = AsanaConnector(cfg, _opener=self.opener)
        with self.assertRaises(AsanaConfigError):
            conn.create_task("x")
        self.opener.assert_not_called()


class CliTests(unittest.TestCase):
    def test_check_disabled(self):
        from asana_connector import main

        buf = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True), mock.patch("sys.stdout", buf):
            rc = main(["--check"])
        self.assertEqual(rc, 0)
        self.assertIn("disabled", buf.getvalue())


@unittest.skipUnless(os.environ.get("RUN_LIVE_ASANA_TESTS") == "1", "live Asana tests opt-in only")
class LiveAsanaTests(unittest.TestCase):
    def test_live_create_task(self):
        cfg = AsanaConfig.from_env()
        cfg.require_enabled()
        conn = AsanaConnector(cfg)
        result = conn.report_grok_sync("live-test", 0, detail="live smoke test")
        self.assertIn("data", result)


if __name__ == "__main__":
    unittest.main()
