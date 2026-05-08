"""ntfy.sh push notification alert handler."""

from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError

from cronwatch.alerting import Alert, AlertHandler, AlertLevel


class NtfyAlertHandler(AlertHandler):
    """Send alerts via ntfy.sh (or a self-hosted ntfy instance)."""

    def __init__(
        self,
        topic: str,
        server: str = "https://ntfy.sh",
        token: str | None = None,
        priority_map: dict[str, str] | None = None,
    ) -> None:
        if not topic:
            raise ValueError("ntfy topic must not be empty")
        if not server:
            raise ValueError("ntfy server must not be empty")
        self.topic = topic
        self.server = server.rstrip("/")
        self.token = token
        self._priority_map: dict[str, str] = priority_map or {
            AlertLevel.INFO.value: "low",
            AlertLevel.WARNING.value: "default",
            AlertLevel.CRITICAL.value: "urgent",
        }

    def _build_request(self, alert: Alert) -> urllib.request.Request:
        """Build the HTTP request for the given alert."""
        url = f"{self.server}/{self.topic}"
        priority = self._priority_map.get(alert.level.value, "default")
        payload = json.dumps(
            {
                "topic": self.topic,
                "title": f"[cronwatch] {alert.level.value.upper()}: {alert.job_name}",
                "message": str(alert),
                "priority": priority,
                "tags": ["clock", alert.level.value],
            }
        ).encode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        return req

    def send(self, alert: Alert) -> None:
        """Send an alert as a push notification via ntfy."""
        req = self._build_request(alert)
        try:
            with urllib.request.urlopen(req) as resp:  # noqa: S310
                if resp.status not in (200, 201):
                    raise RuntimeError(
                        f"ntfy returned unexpected status {resp.status}"
                    )
        except URLError as exc:
            raise RuntimeError(f"Failed to send ntfy alert: {exc}") from exc
