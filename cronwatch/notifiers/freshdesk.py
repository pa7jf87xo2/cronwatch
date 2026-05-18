"""Freshdesk notifier – creates a support ticket for each alert."""

from __future__ import annotations

import base64
import json
from urllib.request import Request, urlopen
from urllib.error import URLError

from cronwatch.alerting import Alert, AlertLevel, AlertHandler


_PRIORITY = {
    AlertLevel.INFO: 1,      # Low
    AlertLevel.WARNING: 2,   # Medium
    AlertLevel.CRITICAL: 3,  # High
}


class FreshdeskAlertHandler(AlertHandler):
    """Open a Freshdesk ticket when a cron alert fires."""

    def __init__(
        self,
        domain: str,
        api_key: str,
        email: str,
        tags: list[str] | None = None,
    ) -> None:
        if not domain:
            raise ValueError("Freshdesk domain must not be empty")
        if not api_key:
            raise ValueError("Freshdesk api_key must not be empty")
        if not email:
            raise ValueError("Freshdesk requester email must not be empty")

        self._url = f"https://{domain}/api/v2/tickets"
        self._auth = base64.b64encode(f"{api_key}:X".encode()).decode()
        self._email = email
        self._tags = tags or ["cronwatch"]

    def send(self, alert: Alert) -> None:
        payload = {
            "subject": f"[cronwatch] {alert.level.name}: {alert.job_name}",
            "description": str(alert),
            "email": self._email,
            "priority": _PRIORITY.get(alert.level, 1),
            "status": 2,  # Open
            "tags": self._tags,
        }
        data = json.dumps(payload).encode()
        req = Request(
            self._url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Basic {self._auth}",
            },
            method="POST",
        )
        try:
            with urlopen(req, timeout=10) as resp:
                if resp.status not in (200, 201):
                    raise RuntimeError(
                        f"Freshdesk returned unexpected status {resp.status}"
                    )
        except URLError as exc:
            raise RuntimeError(f"Failed to reach Freshdesk: {exc}") from exc
