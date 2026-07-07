"""Unit tests for Asana adapter with mocked HTTP responses.

These tests use mocked Asana API responses and do NOT make live calls.
Safe to run in CI without environment configuration.
"""

import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from adapters.asana_adapter import (
    ShadowGardenAsanaReporter,
    VoiceSynthesisMetrics,
    ChatSyncMetrics,
)
from asana_connector.config import AsanaConfig


class MockAsanaClient:
    """Mock Asana API client for testing."""

    def __init__(self, api_token, workspace_id):
        self.api_token = api_token
        self.workspace_id = workspace_id
        self.created_tasks = []

    def create_task(self, name, project_id, description=None, custom_fields=None):
        """Mock task creation."""
        task = {
            "gid": f"mock-task-{len(self.created_tasks) + 1}",
            "name": name,
            "project_id": project_id,
            "notes": description,
            "custom_fields": custom_fields or {},
        }
        self.created_tasks.append(task)
        return task

    def add_task_comment(self, task_id, text):
        """Mock comment addition."""
        return {
            "gid": f"mock-comment-{task_id}",
            "text": text,
            "task_id": task_id,
        }

    def get_project(self, project_id):
        """Mock project retrieval."""
        return {"gid": project_id, "name": f"Mock Project {project_id}"}

    def test_connection(self):
        """Mock connection test."""
        return True


class TestAsanaConfig(unittest.TestCase):
    """Test AsanaConfig initialization and validation."""

    def test_config_from_env(self):
        """Test loading config from environment variables."""
        with patch.dict(
            os.environ,
            {
                "ASANA_API_TOKEN": "test-token",
                "ASANA_WORKSPACE_ID": "test-workspace",
                "ASANA_PROJECT_SHADOWGARDEN": "test-project",
            },
        ):
            config = AsanaConfig()
            self.assertEqual(config.api_token, "test-token")
            self.assertEqual(config.workspace_id, "test-workspace")
            self.assertEqual(config.project_ids["shadow_garden"], "test-project")

    def test_config_missing_token_raises(self):
        """Test that missing API token raises error."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                AsanaConfig()

    def test_config_from_constructor(self):
        """Test loading config from constructor arguments."""
        config = AsanaConfig(
            api_token="ctor-token",
            workspace_id="ctor-workspace",
            project_ids={"shadow_garden": "ctor-project"},
        )
        self.assertEqual(config.api_token, "ctor-token")
        self.assertEqual(config.workspace_id, "ctor-workspace")


class TestVoiceSynthesisMetrics(unittest.TestCase):
    """Test voice synthesis metrics dataclass."""

    def test_metrics_creation(self):
        """Test creating voice synthesis metrics."""
        metrics = VoiceSynthesisMetrics(
            timestamp="2026-07-05T12:00:00Z",
            voice="Angela",
            prompt_length=150,
            synthesis_latency_ms=1200.5,
            quality_score=92.5,
            success=True,
        )
        self.assertEqual(metrics.voice, "Angela")
        self.assertEqual(metrics.quality_score, 92.5)
        self.assertTrue(metrics.success)

    def test_failed_synthesis_metrics(self):
        """Test metrics for failed synthesis."""
        metrics = VoiceSynthesisMetrics(
            timestamp="2026-07-05T12:00:00Z",
            voice="Angela",
            prompt_length=150,
            synthesis_latency_ms=5000,
            quality_score=0,
            success=False,
            error_message="Synthesis timeout",
        )
        self.assertFalse(metrics.success)
        self.assertIsNotNone(metrics.error_message)


class TestShadowGardenReporter(unittest.TestCase):
    """Test ShadowGardenAsanaReporter with mocked client."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = AsanaConfig(
            api_token="test-token",
            workspace_id="test-workspace",
            project_ids={"shadow_garden": "test-project-id"},
        )

    @patch("adapters.asana_adapter.AsanaClient", MockAsanaClient)
    def test_report_voice_synthesis(self):
        """Test reporting voice synthesis metrics."""
        reporter = ShadowGardenAsanaReporter(self.config)

        metrics = VoiceSynthesisMetrics(
            timestamp="2026-07-05T12:00:00Z",
            voice="Angela",
            prompt_length=150,
            synthesis_latency_ms=1200.5,
            quality_score=92.5,
            success=True,
        )

        # Mock the field IDs
        reporter.field_ids = {
            "resonance_score": "field-1",
            "technique_mastery": "field-2",
            "soul_alignment": "field-3",
            "last_reported": "field-4",
            "metrics_json": "field-5",
        }

        task = reporter.report_voice_synthesis(metrics)

        self.assertIn("task", str(task).lower() or "gid" in task)
        self.assertIsNotNone(task.get("gid"))

    @patch("adapters.asana_adapter.AsanaClient", MockAsanaClient)
    def test_report_chat_sync(self):
        """Test reporting chat sync metrics."""
        reporter = ShadowGardenAsanaReporter(self.config)

        metrics = ChatSyncMetrics(
            timestamp="2026-07-05T12:00:00Z",
            messages_synced=150,
            sync_duration_ms=850.0,
            success_rate=98.5,
            conflicts_found=0,
            conflicts_resolved=0,
        )

        reporter.field_ids = {
            "resonance_score": "field-1",
            "technique_mastery": "field-2",
            "soul_alignment": "field-3",
            "last_reported": "field-4",
            "metrics_json": "field-5",
        }

        task = reporter.report_chat_sync(metrics)
        self.assertIsNotNone(task)

    @patch("adapters.asana_adapter.AsanaClient", MockAsanaClient)
    def test_health_check_passes(self):
        """Test health check with mocked client."""
        reporter = ShadowGardenAsanaReporter(self.config)
        self.assertTrue(reporter.health_check())


class TestNoSecretsInCode(unittest.TestCase):
    """Verify no hardcoded secrets exist in the codebase."""

    def test_no_hardcoded_tokens(self):
        """Scan adapter files for hardcoded token patterns."""
        adapter_file = Path(__file__).parent.parent / "adapters" / "asana_adapter.py"
        content = adapter_file.read_text()

        # Patterns that indicate hardcoded secrets
        forbidden_patterns = [
            "api_token=",
            "token=",
            '"Bearer ',
            "0/projects/",  # Asana GID patterns
        ]

        for pattern in forbidden_patterns:
            # Ignore patterns in comments or docstrings
            for line in content.split("\n"):
                if line.strip().startswith("#") or line.strip().startswith('"""'):
                    continue
                # Real hardcoded secrets should not appear
                if pattern in line and "environ" not in line and "getenv" not in line:
                    if not any(
                        x in line for x in ["example", "placeholder", "your-", "<"]
                    ):
                        self.fail(
                            f"Possible hardcoded secret found: {pattern} in {line}"
                        )


class TestSafeTestConfig(unittest.TestCase):
    """Verify tests are safe for CI/offline execution."""

    def test_no_live_calls_by_default(self):
        """Verify live API calls are disabled by default."""
        # Check that RUN_LIVE_ASANA_TESTS env var is required for live tests
        self.assertNotIn("RUN_LIVE_ASANA_TESTS", os.environ)
        # In CI, this should be false/unset, so live tests won't run


if __name__ == "__main__":
    unittest.main()
