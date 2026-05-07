"""Webhook notifier for cronwatch alerts."""

import json
import urllib.request
import urllib.error
from typing import Optional

from cronwatch.alerting import Alert, AlertHandler


class WebhookAlertHandler(AlertHandler):
    """Sends alerts as JSON POST requests to a configurable webhook URL."""

    def __init__(
        self,
        url: str,
        secret_header: Optional[str] = None,
        secret_value: Optional[str] = None,
        timeout: int = 10,
    ) -> None:
        """
        Args:
            url: The webhook endpoint to POST alerts to.
            secret_header: Optional HTTP header name for authentication.
            secret_value: Optional value for the secret header.
            timeout: Request timeout in seconds.
        """
        self.url = url
        self.secret_header = secret_header
        self.secret_value = secret_value
        self.timeout = timeout

    def send(self, alert: Alert) -> None:
        """Serialize the alert as JSON and POST it to the webhook URL."""
        payload = {
            "level": alert.level.name,
            "job_name": alert.job_name,
            "message": alert.message,
            "overdue_by_seconds": alert.overdue_by.total_seconds()
            if alert.overdue_by is not None
            else None,
        }
        body = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            self.url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )

        if self.secret_header and self.secret_value:
            req.add_header(self.secret_header, self.secret_value)

        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status not in range(200, 300):
                    raise RuntimeError(
                        f"Webhook returned non-2xx status: {resp.status}"
                    )
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"Webhook returned non-2xx status: {exc.code} {exc.reason}"
            ) from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Webhook request failed: {exc.reason}") from exc
