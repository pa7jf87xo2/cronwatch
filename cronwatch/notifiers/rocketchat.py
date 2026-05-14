"""Rocket.Chat notifier via incoming webhook."""

from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError

from cronwatch.alerting import Alert, AlertLevel


class RocketChatAlertHandler:
    """Send alerts to a Rocket.Chat channel via an incoming webhook URL."""

    def __init__(
        self,
        webhook_url: str,
        username: str = "cronwatch",
        icon_emoji: str = ":alarm_clock:",
        timeout: int = 10,
    ) -> None:
        if not webhook_url:
            raise ValueError("webhook_url must not be empty")
        self._webhook_url = webhook_url
        self._username = username
        self._icon_emoji = icon_emoji
        self._timeout = timeout

    def send(self, alert: Alert) -> None:
        colour = {
            AlertLevel.WARNING: "warning",
            AlertLevel.CRITICAL: "danger",
            AlertLevel.INFO: "good",
        }.get(alert.level, "good")

        payload = {
            "username": self._username,
            "icon_emoji": self._icon_emoji,
            "attachments": [
                {
                    "color": colour,
                    "title": f"[{alert.level.name}] {alert.job_name}",
                    "text": str(alert),
                    "mrkdwn_in": ["text"],
                }
            ],
        }

        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self._webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout):
                pass
        except URLError as exc:
            raise RuntimeError(f"Failed to send Rocket.Chat alert: {exc}") from exc
