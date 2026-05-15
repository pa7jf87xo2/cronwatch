"""Splunk HTTP Event Collector (HEC) alert handler."""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.error
from typing import Any

from cronwatch.alerting import Alert, AlertHandler, AlertLevel


class SplunkAlertHandler(AlertHandler):
    """Send alerts to a Splunk HTTP Event Collector endpoint."""

    def __init__(
        self,
        hec_url: str,
        token: str,
        index: str = "main",
        source: str = "cronwatch",
        sourcetype: str = "_json",
        verify_ssl: bool = True,
    ) -> None:
        if not hec_url:
            raise ValueError("hec_url must not be empty")
        if not token:
            raise ValueError("token must not be empty")

        self._hec_url = hec_url.rstrip("/")
        self._token = token
        self._index = index
        self._source = source
        self._sourcetype = sourcetype
        self._verify_ssl = verify_ssl

    def send(self, alert: Alert) -> None:
        """POST alert as a Splunk HEC event."""
        event: dict[str, Any] = {
            "job": alert.job_name,
            "level": alert.level.name,
            "message": str(alert),
            "overdue_by_seconds": alert.overdue_by,
        }

        payload = json.dumps(
            {
                "time": time.time(),
                "host": "cronwatch",
                "source": self._source,
                "sourcetype": self._sourcetype,
                "index": self._index,
                "event": event,
            }
        ).encode()

        req = urllib.request.Request(
            f"{self._hec_url}/services/collector/event",
            data=payload,
            headers={
                "Authorization": f"Splunk {self._token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        ctx = None
        if not self._verify_ssl:
            import ssl
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE

        with urllib.request.urlopen(req, context=ctx) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(
                    f"Splunk HEC returned unexpected status {resp.status}"
                )
