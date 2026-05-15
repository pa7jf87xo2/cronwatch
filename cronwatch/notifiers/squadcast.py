"""Squadcast incident notifier for cronwatch."""

from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError

from cronwatch.alerting import Alert, AlertLevel, AlertHandler


class SquadcastAlertHandler(AlertHandler):
    """Send alerts to Squadcast via its incident webhook API."""

    def __init__(self, webhook_url: str, *, timeout: int = 10) -> None:
        if not webhook_url:
            raise ValueError("Squadcast webhook_url must not be empty")
        self._url = webhook_url
        self._timeout = timeout

    def _map_status(self, level: AlertLevel) -> str:
        return {
            AlertLevel.INFO: "resolve",
            AlertLevel.WARNING: "trigger",
            AlertLevel.CRITICAL: "trigger",
        }.get(level, "trigger")

    def send(self, alert: Alert) -> None:
        payload = {
            "message": str(alert),
            "description": (
                f"CronJob '{alert.job_name}' is {alert.level.name.lower()}. "
                f"Last run: {alert.last_run_at}"
            ),
            "status": self._map_status(alert.level),
            "tags": {
                "level": alert.level.name.lower(),
                "job": alert.job_name,
            },
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self._url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout):
                pass
        except URLError as exc:
            raise RuntimeError(f"Squadcast notification failed: {exc}") from exc
