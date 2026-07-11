"""
Shadow-Garden-Launcher Asana Adapter.
Reports voice synthesis and Grok chat metrics to Asana.

Integrates with bridge.py to capture voice quality and chat sync metrics,
then pushes them to Asana as tasks with resonance tracking.
"""

import os
import json
from typing import Dict, Optional, Any
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict

# Import shared connector
import sys
# Repo root (where the asana_connector/ package lives) is two levels up:
# adapters/asana_adapter.py -> adapters/ -> <repo root>.
sys.path.insert(0, str(Path(__file__).parent.parent))
from asana_connector import (
    AsanaClient,
    AsanaConfig,
    DataMapper,
)


@dataclass
class VoiceSynthesisMetrics:
    """Voice synthesis execution metrics."""

    timestamp: str  # ISO format
    voice: str  # Voice actor name
    prompt_length: int  # Characters
    synthesis_latency_ms: float  # Milliseconds
    quality_score: float  # 0-100
    success: bool  # Did synthesis succeed?
    output_file: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ChatSyncMetrics:
    """Grok chat synchronization metrics."""

    timestamp: str  # ISO format
    messages_synced: int  # Count of messages
    sync_duration_ms: float  # Duration
    success_rate: float  # 0-100
    conflicts_found: int  # Count
    conflicts_resolved: int  # Count


class ShadowGardenAsanaReporter:
    """
    Report voice synthesis and chat sync metrics to Asana.

    Real-time reporting:
    - Individual execution → Asana task created immediately
    - Metrics stored in custom fields
    - Aggregate rollups (daily/weekly)
    """

    def __init__(self, config: Optional[AsanaConfig] = None):
        """
        Initialize shadow-garden reporter.

        Args:
            config: AsanaConfig instance (uses env vars if not provided)
        """
        self.config = config or AsanaConfig()
        self.client = AsanaClient(self.config.api_token, self.config.workspace_id)

        # Map field IDs from config (set during bootstrap)
        self.field_ids = self._load_field_ids()
        self.mapper = DataMapper(self.field_ids)

        self.project_id = self.config.project_ids.get("shadow_garden")
        if not self.project_id:
            raise ValueError("ASANA_PROJECT_SHADOWGARDEN not configured")

    def _load_field_ids(self) -> Dict[str, str]:
        """
        Load custom field IDs from environment or config.
        Set during bootstrap; must match Asana workspace.
        """
        # These would normally come from bootstrap output or saved config
        return {
            "resonance_score": os.getenv("ASANA_FIELD_RESONANCE_SCORE"),
            "technique_mastery": os.getenv("ASANA_FIELD_TECHNIQUE_MASTERY"),
            "soul_alignment": os.getenv("ASANA_FIELD_SOUL_ALIGNMENT"),
            "last_reported": os.getenv("ASANA_FIELD_LAST_REPORTED"),
            "metrics_json": os.getenv("ASANA_FIELD_METRICS_JSON"),
        }

    # ============ Voice Synthesis Reporting ============

    def report_voice_synthesis(
        self,
        metrics: VoiceSynthesisMetrics,
        include_in_aggregates: bool = True,
    ) -> Dict[str, Any]:
        """
        Report a single voice synthesis execution to Asana.

        Args:
            metrics: VoiceSynthesisMetrics instance
            include_in_aggregates: Whether to include in rollup summaries

        Returns:
            Created Asana task data
        """
        task_name = f"Voice Synthesis: {metrics.voice} - {metrics.timestamp[:10]}"
        task_description = self._build_voice_description(metrics)

        # Map metrics to custom fields
        custom_fields = self._map_voice_metrics(metrics)

        # Create task
        task = self.client.create_task(
            name=task_name,
            project_id=self.project_id,
            description=task_description,
            custom_fields=custom_fields,
        )

        # Add metric comment for detailed tracking
        metric_summary = self._format_metric_summary(
            metrics, "Voice Synthesis", include_in_aggregates
        )
        self.client.add_task_comment(task.get("gid"), metric_summary)

        return task

    def _build_voice_description(self, metrics: VoiceSynthesisMetrics) -> str:
        """Build detailed task description for voice synthesis."""
        status = "✅ Success" if metrics.success else "❌ Failed"
        return f"""{status}

**Voice**: {metrics.voice}
**Timestamp**: {metrics.timestamp}
**Prompt Length**: {metrics.prompt_length} chars
**Synthesis Latency**: {metrics.synthesis_latency_ms:.1f}ms
**Quality Score**: {metrics.quality_score:.1f}/100

{f"**Output**: {metrics.output_file}" if metrics.output_file else ""}
{f"**Error**: {metrics.error_message}" if metrics.error_message else ""}
"""

    def _map_voice_metrics(self, metrics: VoiceSynthesisMetrics) -> Dict[str, Any]:
        """Map voice synthesis metrics to Asana custom fields."""
        quality_score = metrics.quality_score if metrics.success else 0

        return {
            **self.mapper.map_resonance_score(quality_score),
            **self.mapper.map_technique_mastery(
                "Master" if quality_score >= 90 else "Expert" if quality_score >= 75 else "Adept"
            ),
            **self.mapper.map_soul_alignment(
                "Resonant Synthesis" if quality_score >= 85 else "Emerging Voice"
            ),
            **self.mapper.map_metrics_json({
                "voice": metrics.voice,
                "prompt_length": metrics.prompt_length,
                "latency_ms": metrics.synthesis_latency_ms,
                "quality": metrics.quality_score,
                "success": metrics.success,
            }),
            **self.mapper.map_last_reported(),
        }

    # ============ Chat Sync Reporting ============

    def report_chat_sync(
        self,
        metrics: ChatSyncMetrics,
        include_in_aggregates: bool = True,
    ) -> Dict[str, Any]:
        """
        Report a Grok chat synchronization to Asana.

        Args:
            metrics: ChatSyncMetrics instance
            include_in_aggregates: Whether to include in rollup summaries

        Returns:
            Created Asana task data
        """
        task_name = f"Grok Chat Sync - {metrics.timestamp[:10]}"
        task_description = self._build_chat_description(metrics)

        # Map metrics to custom fields
        custom_fields = self._map_chat_metrics(metrics)

        # Create task
        task = self.client.create_task(
            name=task_name,
            project_id=self.project_id,
            description=task_description,
            custom_fields=custom_fields,
        )

        # Add metric comment
        metric_summary = self._format_metric_summary(
            metrics, "Chat Sync", include_in_aggregates
        )
        self.client.add_task_comment(task.get("gid"), metric_summary)

        return task

    def _build_chat_description(self, metrics: ChatSyncMetrics) -> str:
        """Build detailed task description for chat sync."""
        status = "✅ Success" if metrics.success_rate >= 90 else "⚠️ Partial" if metrics.success_rate >= 70 else "❌ Failed"
        return f"""{status}

**Timestamp**: {metrics.timestamp}
**Messages Synced**: {metrics.messages_synced}
**Sync Duration**: {metrics.sync_duration_ms:.1f}ms
**Success Rate**: {metrics.success_rate:.1f}%
**Conflicts Found**: {metrics.conflicts_found}
**Conflicts Resolved**: {metrics.conflicts_resolved}
"""

    def _map_chat_metrics(self, metrics: ChatSyncMetrics) -> Dict[str, Any]:
        """Map chat sync metrics to Asana custom fields."""
        return {
            **self.mapper.map_resonance_score(metrics.success_rate),
            **self.mapper.map_technique_mastery(
                "Master" if metrics.success_rate >= 95 else "Expert" if metrics.success_rate >= 85 else "Adept"
            ),
            **self.mapper.map_soul_alignment(
                "Synchronized Harmony" if metrics.success_rate >= 90 else "Seeking Resonance"
            ),
            **self.mapper.map_metrics_json({
                "messages_synced": metrics.messages_synced,
                "duration_ms": metrics.sync_duration_ms,
                "success_rate": metrics.success_rate,
                "conflicts_found": metrics.conflicts_found,
                "conflicts_resolved": metrics.conflicts_resolved,
            }),
            **self.mapper.map_last_reported(),
        }

    # ============ Aggregates & Summaries ============

    def create_daily_summary(self, date: str = None) -> Dict[str, Any]:
        """
        Create a daily aggregated summary task.

        Args:
            date: Date string (YYYY-MM-DD, defaults to today)

        Returns:
            Created summary task data
        """
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        task_name = f"Daily Resonance Summary - {date}"
        task_description = f"""**Voice Resonance & Chat Synchronization Daily Report**

Date: {date}

_This is an automated aggregated summary of all voice synthesis and chat sync
activities for this day. Individual execution tasks are linked in the project._

See related tasks tagged with date `{date}`."""

        # Create summary task (with baseline metrics)
        task = self.client.create_task(
            name=task_name,
            project_id=self.project_id,
            description=task_description,
            custom_fields=self.mapper.map_last_reported(),
        )

        return task

    # ============ Utilities ============

    @staticmethod
    def _format_metric_summary(
        metrics: Any,
        metric_type: str,
        include_in_aggregates: bool,
    ) -> str:
        """Format metrics as a comment on the task."""
        aggregate_note = (
            "📊 Included in daily/weekly aggregates"
            if include_in_aggregates
            else "📌 Standalone metric (not included in aggregates)"
        )

        return f"""**{metric_type} Metric Report**

{aggregate_note}

Raw Data (JSON):
```json
{json.dumps(asdict(metrics), indent=2, default=str)}
```
"""

    def health_check(self) -> bool:
        """Test that Asana connection and project are valid."""
        try:
            project = self.client.get_project(self.project_id)
            return bool(project and project.get("gid"))
        except Exception as e:
            print(f"⚠️ Health check failed: {e}")
            return False


# ============ Convenience Functions ============

def report_synthesis_metrics(
    voice: str,
    prompt_length: int,
    latency_ms: float,
    quality_score: float,
    success: bool = True,
    output_file: str = None,
    error: str = None,
) -> Dict[str, Any]:
    """
    Convenience function to report voice synthesis metrics.

    Usage:
        from adapters.asana_adapter import report_synthesis_metrics
        report_synthesis_metrics(
            voice="Angela",
            prompt_length=150,
            latency_ms=1200.5,
            quality_score=92.5,
        )
    """
    reporter = ShadowGardenAsanaReporter()
    metrics = VoiceSynthesisMetrics(
        timestamp=datetime.now().isoformat(),
        voice=voice,
        prompt_length=prompt_length,
        synthesis_latency_ms=latency_ms,
        quality_score=quality_score,
        success=success,
        output_file=output_file,
        error_message=error,
    )
    return reporter.report_voice_synthesis(metrics)


def report_chat_sync_metrics(
    messages_synced: int,
    sync_duration_ms: float,
    success_rate: float,
    conflicts_found: int = 0,
    conflicts_resolved: int = 0,
) -> Dict[str, Any]:
    """
    Convenience function to report chat sync metrics.

    Usage:
        from adapters.asana_adapter import report_chat_sync_metrics
        report_chat_sync_metrics(
            messages_synced=150,
            sync_duration_ms=850.0,
            success_rate=98.5,
        )
    """
    reporter = ShadowGardenAsanaReporter()
    metrics = ChatSyncMetrics(
        timestamp=datetime.now().isoformat(),
        messages_synced=messages_synced,
        sync_duration_ms=sync_duration_ms,
        success_rate=success_rate,
        conflicts_found=conflicts_found,
        conflicts_resolved=conflicts_resolved,
    )
    return reporter.report_chat_sync(metrics)
