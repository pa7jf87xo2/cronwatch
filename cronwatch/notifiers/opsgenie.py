"""OpsGenie alert notifier for cronwatch."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel, AlertHandler


OPSGENIE_API_URL = "https://api.opsgenie.com/v2/alerts"

PRIORITY_MAP = {
    AlertLevel.INFO: "P5",
    AlertLevel.WARNING: "P3",
    AlertLevel.CRITICAL: "P1",
}


class OpsGenieAlertHandler(AlertHandler):
    """Sends alerts to OpsGenie via the REST API."""

    def __init__(self, api_key: str, tags: list[str] | None = None) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("OpsGenie api_key must not be empty")
        self._api_key = api_key
        self._tags = tags or []

    def send(self, alert: Alert) -> None:
        priority = PRIORITY_MAP.get(alert.level, "P3")
        payload = {
            "message": f"[cronwatch] {alert.level.name}: {alert.job_name}",
            "description": str(alert),
            "priority": priority,
            "source": "cronwatch",
            "tags": self._tags,
            "details": {
                "job": alert.job_name,
                "level": alert.level.name,
                "overdue_by": str(alert.overdue_by),
            },
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            OPSGENIE_API_URL,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"GenieKey {self._api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                if resp.status not in (200, 201, 202):
                    raise RuntimeError(
                        f"OpsGenie API returned unexpected status {resp.status}"
                    )
        except urllib.error.HTTPError as exc:
            raise RuntimeError(f"OpsGenie API error: {exc.code} {exc.reason}") from exc
