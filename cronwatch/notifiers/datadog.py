"""Datadog Events API notifier for cronwatch."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel


class DatadogAlertHandler:
    """Send cronwatch alerts as Datadog events."""

    _API_URL = "https://api.datadoghq.com/api/v1/events"

    def __init__(self, api_key: str, app_key: str = "", site: str = "datadoghq.com"):
        if not api_key:
            raise ValueError("Datadog api_key must not be empty")
        self._api_key = api_key
        self._app_key = app_key
        self._base_url = f"https://api.{site}/api/v1/events"

    def send(self, alert: Alert) -> None:
        alert_type = self._map_alert_type(alert.level)
        payload = {
            "title": f"[cronwatch] {alert.job_name} — {alert.level.name}",
            "text": str(alert),
            "alert_type": alert_type,
            "tags": [
                "source:cronwatch",
                f"job:{alert.job_name}",
                f"level:{alert.level.name.lower()}",
            ],
        }
        data = json.dumps(payload).encode()
        headers = {
            "Content-Type": "application/json",
            "DD-API-KEY": self._api_key,
        }
        if self._app_key:
            headers["DD-APPLICATION-KEY"] = self._app_key

        req = urllib.request.Request(
            self._base_url, data=data, headers=headers, method="POST"
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status not in (200, 202):
                    raise RuntimeError(
                        f"Datadog API returned unexpected status {resp.status}"
                    )
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"Datadog API error: {exc.code} {exc.reason}") from exc

    @staticmethod
    def _map_alert_type(level: AlertLevel) -> str:
        return {
            AlertLevel.INFO: "info",
            AlertLevel.WARNING: "warning",
            AlertLevel.CRITICAL: "error",
        }.get(level, "info")
