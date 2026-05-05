"""Tests for cronwatch.daemon.CronWatchDaemon._tick behaviour."""

from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.daemon import CronWatchDaemon
from cronwatch.schedule import CronJob


NOW = datetime(2024, 6, 1, 12, 0, 0)


def _overdue_job() -> CronJob:
    return CronJob(
        name="overdue",
        schedule="* * * * *",
        grace_period=60,
        last_run=NOW - timedelta(seconds=300),
    )


def _healthy_job() -> CronJob:
    return CronJob(
        name="healthy",
        schedule="* * * * *",
        grace_period=120,
        last_run=NOW - timedelta(seconds=10),
    )


class TestCronWatchDaemon:
    def setup_method(self):
        self.handler = MagicMock()

    def test_tick_dispatches_alert_for_overdue_job(self):
        daemon = CronWatchDaemon([_overdue_job()], self.handler)
        with patch("cronwatch.checker.datetime") as mock_dt:
            mock_dt.utcnow.return_value = NOW
            daemon._tick()
        self.handler.send.assert_called_once()

    def test_tick_no_alert_for_healthy_job(self):
        daemon = CronWatchDaemon([_healthy_job()], self.handler)
        with patch("cronwatch.checker.datetime") as mock_dt:
            mock_dt.utcnow.return_value = NOW
            daemon._tick()
        self.handler.send.assert_not_called()

    def test_stop_sets_running_false(self):
        daemon = CronWatchDaemon([], self.handler)
        daemon._running = True
        daemon.stop()
        assert daemon._running is False

    def test_default_poll_interval(self):
        daemon = CronWatchDaemon([], self.handler)
        assert daemon._poll_interval == 60

    def test_custom_poll_interval(self):
        daemon = CronWatchDaemon([], self.handler, poll_interval=30)
        assert daemon._poll_interval == 30
