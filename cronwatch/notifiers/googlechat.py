"""Google Chat notifier via incoming webhook."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel


class GoogleChatAlertHandler:
    """Send alerts to a Google Chat space via an incoming webhook URL."""

    def __init__(self, webhook_url: str) -> None:
        if not webhook_url:
            raise ValueError("Google Chat webhook_url must not be empty")
        self._webhook_url = webhook_url

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_text(self, alert: Alert) -> str:
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨",
        }.get(alert.level, "🔔")
        return (
            f"{level_emoji} *CronWatch {alert.level.name}*\n"
            f"Job: `{alert.job_name}`\n"
            f"{alert.message}"
        )

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def send(self, alert: Alert) -> None:
        payload = json.dumps({"text": self._build_text(alert)}).encode()
        req = urllib.request.Request(
            self._webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status not in (200, 204):
                    raise RuntimeError(
                        f"Google Chat webhook returned HTTP {resp.status}"
                    )
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Failed to reach Google Chat webhook: {exc}") from exc
