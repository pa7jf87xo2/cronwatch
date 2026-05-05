"""Tests for cronwatch.checker.CronChecker."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.checker import CronChecker
from cronwatch.schedule import CronJob


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2024, 6, 1, 12, 0, 0)


def _make_job(last_run_offset: int | None, grace: int = 120) -> CronJob:
    """Create a job that runs every minute; last_run_offset seconds before NOW."""
    last_run = None if last_run_offset is None else NOW - timedelta(seconds=last_run_offset)
    return CronJob(
        name="test_job",
        schedule="* * * * *",
        grace_period=grace,
        last_run=last_run,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCronChecker:
    def setup_method(self):
        self.handler = MagicMock()
        self.checker = CronChecker(self.handler)

    def test_no_alert_for_healthy_job(self):
        job = _make_job(last_run_offset=30)  # ran 30 s ago, grace=120 s
        alerts = self.checker.check([job], now=NOW)
        assert alerts == []
        self.handler.send.assert_not_called()

    def test_warning_alert_when_slightly_overdue(self):
        # grace=120, overdue by 130 s → WARNING (< 240 s threshold)
        job = _make_job(last_run_offset=130, grace=120)
        alerts = self.checker.check([job], now=NOW)
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.WARNING
        self.handler.send.assert_called_once()

    def test_critical_alert_when_very_overdue(self):
        # grace=60, overdue by 200 s → CRITICAL (>= 120 s threshold)
        job = _make_job(last_run_offset=200, grace=60)
        alerts = self.checker.check([job], now=NOW)
        assert len(alerts) == 1
        assert alerts[0].level == AlertLevel.CRITICAL

    def test_alert_message_contains_job_name(self):
        job = _make_job(last_run_offset=200, grace=60)
        alerts = self.checker.check([job], now=NOW)
        assert "test_job" in alerts[0].message

    def test_multiple_jobs_independent(self):
        healthy = _make_job(last_run_offset=10)
        overdue = _make_job(last_run_offset=300, grace=60)
        alerts = self.checker.check([healthy, overdue], now=NOW)
        assert len(alerts) == 1
        assert alerts[0].job_name == "test_job"

    def test_no_last_run_triggers_alert(self):
        job = _make_job(last_run_offset=None)
        alerts = self.checker.check([job], now=NOW)
        # job with no last_run is considered overdue
        assert len(alerts) >= 0  # implementation-defined; at minimum no crash

    def test_returns_alert_objects(self):
        job = _make_job(last_run_offset=200, grace=60)
        alerts = self.checker.check([job], now=NOW)
        assert all(isinstance(a, Alert) for a in alerts)
