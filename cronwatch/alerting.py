"""Alerting module for cronwatch — handles notifications for missed/overdue jobs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional

from cronwatch.schedule import CronJob

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


@dataclass
class Alert:
    job_name: str
    level: AlertLevel
    message: str
    triggered_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return f"[{self.level.value}] {self.triggered_at.isoformat()} — {self.job_name}: {self.message}"


class AlertHandler:
    """Base class for alert handlers."""

    def send(self, alert: Alert) -> None:
        raise NotImplementedError


class LogAlertHandler(AlertHandler):
    """Writes alerts to the Python logging system."""

    def send(self, alert: Alert) -> None:
        if alert.level == AlertLevel.CRITICAL:
            logger.critical(str(alert))
        else:
            logger.warning(str(alert))


class AlertManager:
    """Evaluates CronJob states and dispatches alerts via registered handlers."""

    def __init__(self, handlers: Optional[List[AlertHandler]] = None) -> None:
        self.handlers: List[AlertHandler] = handlers or [LogAlertHandler()]

    def register(self, handler: AlertHandler) -> None:
        self.handlers.append(handler)

    def evaluate(self, job: CronJob) -> Optional[Alert]:
        """Check a single job and return an Alert if action is needed."""
        if not job.is_overdue():
            return None

        overdue_seconds = job.overdue_by().total_seconds()  # type: ignore[union-attr]
        level = AlertLevel.CRITICAL if overdue_seconds > job.grace_period * 2 else AlertLevel.WARNING
        message = (
            f"Job has not run since {job.last_run_at}. "
            f"Expected around {job.expected_run_at()}. "
            f"Overdue by {int(overdue_seconds)}s."
        )
        alert = Alert(job_name=job.name, level=level, message=message)
        self._dispatch(alert)
        return alert

    def evaluate_all(self, jobs: List[CronJob]) -> List[Alert]:
        alerts = []
        for job in jobs:
            alert = self.evaluate(job)
            if alert:
                alerts.append(alert)
        return alerts

    def _dispatch(self, alert: Alert) -> None:
        for handler in self.handlers:
            try:
                handler.send(alert)
            except Exception:  # noqa: BLE001
                logger.exception("Alert handler %s failed", handler)
