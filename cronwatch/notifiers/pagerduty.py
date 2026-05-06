"""PagerDuty notifier for cronwatch alerts."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel

PAGERDUTY_EVENTS_API = "https://events.pagerduty.com/v2/enqueue"

_SEVERITY_MAP = {
    AlertLevel.INFO: "info",
    AlertLevel.WARNING: "warning",
    AlertLevel.CRITICAL: "critical",
}


class PagerDutyAlertHandler:
    """Sends alerts to PagerDuty via the Events API v2."""

    def __init__(self, integration_key: str, source: str = "cronwatch"):
        if not integration_key:
            raise ValueError("integration_key must not be empty")
        self._integration_key = integration_key
        self._source = source

    def send(self, alert: Alert) -> None:
        """Send an alert event to PagerDuty."""
        payload = {
            "routing_key": self._integration_key,
            "event_action": "trigger",
            "dedup_key": f"cronwatch-{alert.job_name}",
            "payload": {
                "summary": str(alert),
                "source": self._source,
                "severity": _SEVERITY_MAP.get(alert.level, "warning"),
                "custom_details": {
                    "job_name": alert.job_name,
                    "message": alert.message,
                    "level": alert.level.name,
                },
            },
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            PAGERDUTY_EVENTS_API,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status not in (200, 202):
                    raise RuntimeError(
                        f"PagerDuty returned unexpected status {resp.status}"
                    )
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"PagerDuty request failed: {exc.code} {exc.reason}"
            ) from exc
