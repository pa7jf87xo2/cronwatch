"""Microsoft Teams notifier via Incoming Webhook."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel


class TeamsAlertHandler:
    """Send alerts to a Microsoft Teams channel via an Incoming Webhook URL."""

    def __init__(self, webhook_url: str, timeout: int = 10) -> None:
        if not webhook_url:
            raise ValueError("Teams webhook_url must not be empty")
        self._webhook_url = webhook_url
        self._timeout = timeout

    def send(self, alert: Alert) -> None:
        colour = {
            AlertLevel.INFO: "0076D7",
            AlertLevel.WARNING: "FFA500",
            AlertLevel.CRITICAL: "D13438",
        }.get(alert.level, "0076D7")

        payload = {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "themeColor": colour,
            "summary": str(alert),
            "sections": [
                {
                    "activityTitle": f"CronWatch Alert — {alert.level.name}",
                    "activitySubtitle": alert.job_name,
                    "facts": [
                        {"name": "Job", "value": alert.job_name},
                        {"name": "Level", "value": alert.level.name},
                        {"name": "Message", "value": alert.message},
                    ],
                    "markdown": True,
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
        with urllib.request.urlopen(req, timeout=self._timeout) as resp:
            if resp.status not in (200, 202):
                raise RuntimeError(
                    f"Teams webhook returned unexpected status {resp.status}"
                )
