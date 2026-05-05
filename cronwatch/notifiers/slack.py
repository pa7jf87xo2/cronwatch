"""Slack webhook alert handler for cronwatch."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Optional

from cronwatch.alerting import Alert, AlertHandler, AlertLevel

logger = logging.getLogger(__name__)

_LEVEL_EMOJI = {
    AlertLevel.WARNING: ":warning:",
    AlertLevel.CRITICAL: ":rotating_light:",
}


class SlackAlertHandler(AlertHandler):
    """Sends alerts to a Slack incoming webhook URL."""

    def __init__(self, webhook_url: str, timeout: int = 10) -> None:
        if not webhook_url:
            raise ValueError("webhook_url must not be empty")
        self._webhook_url = webhook_url
        self._timeout = timeout

    def send(self, alert: Alert) -> None:
        emoji = _LEVEL_EMOJI.get(alert.level, ":bell:")
        payload = {
            "text": f"{emoji} *cronwatch alert*",
            "attachments": [
                {
                    "color": "danger" if alert.level == AlertLevel.CRITICAL else "warning",
                    "fields": [
                        {"title": "Job", "value": alert.job_name, "short": True},
                        {"title": "Level", "value": alert.level.value, "short": True},
                        {"title": "Message", "value": alert.message, "short": False},
                        {"title": "Triggered at", "value": alert.triggered_at.isoformat(), "short": True},
                    ],
                }
            ],
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._webhook_url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                status = resp.status
                if status != 200:
                    logger.error("Slack webhook returned HTTP %s", status)
        except urllib.error.URLError as exc:
            logger.error("Failed to send Slack alert: %s", exc)
