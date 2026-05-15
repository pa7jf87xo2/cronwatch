"""Squadcast alert handler for cronwatch."""

from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError

from cronwatch.alerting import Alert, AlertLevel, AlertHandler


_STATUS_MAP = {
    AlertLevel.INFO: "resolve",
    AlertLevel.WARNING: "trigger",
    AlertLevel.CRITICAL: "trigger",
}


class SquadcastAlertHandler(AlertHandler):
    """Send alerts to a Squadcast webhook endpoint."""

    def __init__(self, webhook_url: str) -> None:
        if not webhook_url:
            raise ValueError("Squadcast webhook_url must not be empty")
        self._webhook_url = webhook_url

    def _map_status(self, level: AlertLevel) -> str:
        return _STATUS_MAP.get(level, "trigger")

    def send(self, alert: Alert) -> None:
        payload = {
            "message": str(alert),
            "description": (
                f"CronJob '{alert.job_name}' is {alert.level.value}. "
                f"Last run: {alert.last_run_at}, "
                f"Expected: {alert.expected_run_at}"
            ),
            "status": self._map_status(alert.level),
            "tags": {
                "job": alert.job_name,
                "level": alert.level.value,
            },
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self._webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except URLError as exc:
            raise RuntimeError(
                f"Failed to send Squadcast alert: {exc}"
            ) from exc
