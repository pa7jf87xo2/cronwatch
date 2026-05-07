"""Discord webhook notifier for cronwatch alerts."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel


COLOR_MAP = {
    AlertLevel.INFO: 3447003,      # blue
    AlertLevel.WARNING: 16776960,  # yellow
    AlertLevel.CRITICAL: 15158332, # red
}


class DiscordAlertHandler:
    """Sends alerts to a Discord channel via an incoming webhook."""

    def __init__(self, webhook_url: str, username: str = "CronWatch") -> None:
        if not webhook_url:
            raise ValueError("Discord webhook_url must not be empty")
        self._webhook_url = webhook_url
        self._username = username

    def send(self, alert: Alert) -> None:
        color = COLOR_MAP.get(alert.level, 3447003)
        payload = {
            "username": self._username,
            "embeds": [
                {
                    "title": f"[{alert.level.name}] {alert.job_name}",
                    "description": alert.message,
                    "color": color,
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
            with urllib.request.urlopen(req) as resp:
                if resp.status not in (200, 204):
                    raise RuntimeError(
                        f"Discord webhook returned HTTP {resp.status}"
                    )
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Discord webhook request failed: {exc.code} {exc.reason}"
            ) from exc
