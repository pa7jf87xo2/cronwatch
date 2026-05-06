"""VictorOps (Splunk On-Call) alert notifier."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel, AlertHandler


_MESSAGE_TYPES = {
    AlertLevel.INFO: "INFO",
    AlertLevel.WARNING: "WARNING",
    AlertLevel.CRITICAL: "CRITICAL",
}


class VictorOpsAlertHandler(AlertHandler):
    """Send alerts to a VictorOps REST endpoint."""

    def __init__(self, rest_endpoint_url: str, routing_key: str = "default") -> None:
        if not rest_endpoint_url:
            raise ValueError("rest_endpoint_url must not be empty")
        if not routing_key:
            raise ValueError("routing_key must not be empty")
        self._url = f"{rest_endpoint_url.rstrip('/')}/{routing_key}"

    def send(self, alert: Alert) -> None:
        payload = {
            "message_type": _MESSAGE_TYPES.get(alert.level, "WARNING"),
            "entity_id": f"cronwatch.{alert.job_name}",
            "entity_display_name": f"Cron job '{alert.job_name}' overdue",
            "state_message": alert.message,
            "monitoring_tool": "cronwatch",
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self._url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status not in (200, 201):
                    raise RuntimeError(
                        f"VictorOps returned unexpected status {resp.status}"
                    )
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Failed to reach VictorOps endpoint: {exc}") from exc
