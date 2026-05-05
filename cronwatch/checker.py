"""Core checker that evaluates cron jobs and produces alerts."""

from __future__ import annotations

from datetime import datetime
from typing import List

from cronwatch.alerting import Alert, AlertLevel, AlertHandler
from cronwatch.schedule import CronJob


class CronChecker:
    """Evaluates a list of CronJob instances and dispatches alerts."""

    def __init__(self, handler: AlertHandler) -> None:
        self._handler = handler

    def check(self, jobs: List[CronJob], now: datetime | None = None) -> List[Alert]:
        """Check all jobs and return a list of alerts that were fired."""
        if now is None:
            now = datetime.utcnow()

        fired: List[Alert] = []
        for job in jobs:
            alert = self._evaluate(job, now)
            if alert is not None:
                self._handler.send(alert)
                fired.append(alert)
        return fired

    def _evaluate(self, job: CronJob, now: datetime) -> Alert | None:
        """Return an Alert if the job is overdue or missed, else None."""
        if not job.is_overdue(now):
            return None

        expected = job.expected_run_at(now)
        if expected is None:
            return None

        overdue_seconds = (now - expected).total_seconds()
        level = self._severity(overdue_seconds, job.grace_period)

        return Alert(
            level=level,
            job_name=job.name,
            message=(
                f"Job '{job.name}' is overdue by {int(overdue_seconds)}s "
                f"(expected at {expected.isoformat()})"
            ),
            expected_at=expected,
            checked_at=now,
        )

    @staticmethod
    def _severity(overdue_seconds: float, grace_period: int) -> AlertLevel:
        """Escalate to CRITICAL when overdue by more than twice the grace period."""
        if overdue_seconds >= grace_period * 2:
            return AlertLevel.CRITICAL
        return AlertLevel.WARNING
