"""Grafana Alerting notifier for cronwatch."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel


class GrafanaAlertHandler:
    """Send alerts to a Grafana Alerting webhook endpoint."""

    def __init__(self, url: str, api_key: str = "", title_prefix: str = "[cronwatch]"):
        if not url:
            raise ValueError("Grafana webhook URL must not be empty")
        self._url = url
        self._api_key = api_key
        self._title_prefix = title_prefix

    def _severity(self, level: AlertLevel) -> str:
        return {
            AlertLevel.INFO: "default",
            AlertLevel.WARNING: "warning",
            AlertLevel.CRITICAL: "critical",
        }.get(level, "default")

    def send(self, alert: Alert) -> None:
        payload = {
            "title": f"{self._title_prefix} {alert.job_name}",
            "message": str(alert),
            "severity": self._severity(alert.level),
            "state": "alerting" if alert.level != AlertLevel.INFO else "ok",
            "ruleId": 0,
            "ruleName": alert.job_name,
            "evalMatches": [],
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            self._url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        if self._api_key:
            req.add_header("Authorization", f"Bearer {self._api_key}")
        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 204):
                raise RuntimeError(
                    f"Grafana webhook returned unexpected status {resp.status}"
                )
