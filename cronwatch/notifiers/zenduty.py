"""Zenduty alert notifier for cronwatch."""
from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError

from cronwatch.alerting import Alert, AlertHandler, AlertLevel


class ZendutyAlertHandler(AlertHandler):
    """Send alerts to a Zenduty service via its Events API."""

    EVENTS_URL = "https://events.zenduty.com/api/events/"

    def __init__(self, integration_key: str, *, timeout: int = 10) -> None:
        if not integration_key:
            raise ValueError("Zenduty integration_key must not be empty")
        self._key = integration_key
        self._timeout = timeout

    # ------------------------------------------------------------------
    def _map_action(self, level: AlertLevel) -> str:
        return "critical" if level == AlertLevel.CRITICAL else "warning"

    def send(self, alert: Alert) -> None:
        payload = {
            "alert_type": self._map_action(alert.level),
            "message": str(alert),
            "summary": f"cronwatch: {alert.job_name} is {alert.level.name.lower()}",
            "entity_id": alert.job_name,
            "payload": {
                "job_name": alert.job_name,
                "level": alert.level.name,
            },
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self.EVENTS_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Token {self._key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                if resp.status not in (200, 201, 202):
                    raise RuntimeError(
                        f"Zenduty returned unexpected status {resp.status}"
                    )
        except URLError as exc:
            raise RuntimeError(f"Failed to reach Zenduty: {exc}") from exc
