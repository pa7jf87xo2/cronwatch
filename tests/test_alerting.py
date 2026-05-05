"""Tests for the alerting module."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock

import pytest

from cronwatch.alerting import Alert, AlertLevel, AlertManager, LogAlertHandler
from cronwatch.schedule import CronJob


def _overdue_job(grace: int = 60) -> CronJob:
    """Return a job whose last run is well in the past so it is always overdue."""
    job = CronJob(
        name="test-job",
        schedule="* * * * *",  # every minute
        grace_period=grace,
        last_run_at=datetime.utcnow() - timedelta(hours=2),
    )
    return job


def _fresh_job() -> CronJob:
    job = CronJob(
        name="fresh-job",
        schedule="0 3 * * *",  # daily at 03:00
        grace_period=300,
        last_run_at=datetime.utcnow(),
    )
    return job


class TestAlert:
    def test_str_contains_level_and_name(self):
        alert = Alert(job_name="my-job", level=AlertLevel.WARNING, message="late")
        text = str(alert)
        assert "WARNING" in text
        assert "my-job" in text
        assert "late" in text

    def test_critical_str(self):
        alert = Alert(job_name="x", level=AlertLevel.CRITICAL, message="very late")
        assert "CRITICAL" in str(alert)


class TestLogAlertHandler:
    def test_warning_uses_logger_warning(self, caplog):
        import logging

        handler = LogAlertHandler()
        alert = Alert(job_name="j", level=AlertLevel.WARNING, message="msg")
        with caplog.at_level(logging.WARNING, logger="cronwatch.alerting"):
            handler.send(alert)
        assert any("WARNING" in r.message or "msg" in r.message for r in caplog.records)

    def test_critical_uses_logger_critical(self, caplog):
        import logging

        handler = LogAlertHandler()
        alert = Alert(job_name="j", level=AlertLevel.CRITICAL, message="critical-msg")
        with caplog.at_level(logging.CRITICAL, logger="cronwatch.alerting"):
            handler.send(alert)
        assert any(r.levelno == logging.CRITICAL for r in caplog.records)


class TestAlertManager:
    def test_no_alert_for_fresh_job(self):
        manager = AlertManager()
        result = manager.evaluate(_fresh_job())
        assert result is None

    def test_alert_returned_for_overdue_job(self):
        manager = AlertManager(handlers=[MagicMock()])
        alert = manager.evaluate(_overdue_job())
        assert alert is not None
        assert alert.job_name == "test-job"

    def test_alert_dispatched_to_handler(self):
        mock_handler = MagicMock()
        manager = AlertManager(handlers=[mock_handler])
        manager.evaluate(_overdue_job())
        mock_handler.send.assert_called_once()

    def test_evaluate_all_returns_only_overdue(self):
        mock_handler = MagicMock()
        manager = AlertManager(handlers=[mock_handler])
        jobs = [_overdue_job(), _fresh_job(), _overdue_job()]
        alerts = manager.evaluate_all(jobs)
        assert len(alerts) == 2

    def test_handler_exception_does_not_propagate(self):
        broken = MagicMock()
        broken.send.side_effect = RuntimeError("boom")
        manager = AlertManager(handlers=[broken])
        # Should not raise
        manager.evaluate(_overdue_job())

    def test_critical_level_when_very_overdue(self):
        mock_handler = MagicMock()
        manager = AlertManager(handlers=[mock_handler])
        job = _overdue_job(grace=1)  # tiny grace period → very overdue
        alert = manager.evaluate(job)
        assert alert is not None
        assert alert.level == AlertLevel.CRITICAL
