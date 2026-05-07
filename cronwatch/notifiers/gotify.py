"""Gotify push notification alert handler."""
from __future__ import annotations

import json
import urllib.request
import urllib.error
from urllib.parse import urljoin

from cronwatch.alerting import Alert, AlertLevel, AlertHandler


_PRIORITY_MAP = {
    AlertLevel.INFO: 3,
    AlertLevel.WARNING: 5,
    AlertLevel.CRITICAL: 9,
}


class GotifyAlertHandler(AlertHandler):
    """Send alerts to a self-hosted Gotify server."""

    def __init__(self, url: str, token: str, priority: int | None = None) -> None:
        if not url:
            raise ValueError("Gotify server URL must not be empty")
        if not token:
            raise ValueError("Gotify application token must not be empty")
        self._url = url.rstrip("/")
        self._token = token
        self._priority_override = priority

    def send(self, alert: Alert) -> None:
        priority = (
            self._priority_override
            if self._priority_override is not None
            else _PRIORITY_MAP.get(alert.level, 5)
        )
        payload = json.dumps(
            {
                "title": f"[cronwatch] {alert.level.name}: {alert.job_name}",
                "message": str(alert),
                "priority": priority,
            }
        ).encode()

        endpoint = urljoin(self._url + "/", "message")
        req = urllib.request.Request(
            endpoint,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Gotify-Key": self._token,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            if resp.status not in (200, 201):
                raise RuntimeError(
                    f"Gotify returned unexpected status {resp.status}"
                )
