"""Mattermost notifier for cronwatch alerts."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel


class MattermostAlertHandler:
    """Send alerts to a Mattermost channel via incoming webhook."""

    def __init__(self, webhook_url: str, username: str = "cronwatch", icon_emoji: str = ":robot:", channel: str = ""):
        if not webhook_url:
            raise ValueError("Mattermost webhook_url must not be empty")
        self._webhook_url = webhook_url
        self._username = username
        self._icon_emoji = icon_emoji
        self._channel = channel

    def send(self, alert: Alert) -> None:
        """Post an alert message to Mattermost."""
        level_emoji = {
            AlertLevel.WARNING: ":warning:",
            AlertLevel.CRITICAL: ":rotating_light:",
        }.get(alert.level, ":information_source:")

        text = f"{level_emoji} **[{alert.level.name}]** {alert}"

        payload: dict = {
            "text": text,
            "username": self._username,
            "icon_emoji": self._icon_emoji,
        }
        if self._channel:
            payload["channel"] = self._channel

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(
                    f"Mattermost webhook returned unexpected status {resp.status}"
                )
