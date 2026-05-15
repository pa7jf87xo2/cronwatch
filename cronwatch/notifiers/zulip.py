"""Zulip notifier for cronwatch alerts."""

import json
import urllib.request
import urllib.parse
import base64
from cronwatch.alerting import Alert, AlertHandler


class ZulipAlertHandler(AlertHandler):
    """Send alerts to a Zulip stream via the Zulip REST API."""

    def __init__(
        self,
        site: str,
        email: str,
        api_key: str,
        stream: str,
        topic: str = "cronwatch",
    ) -> None:
        if not site:
            raise ValueError("Zulip site URL must not be empty")
        if not email:
            raise ValueError("Zulip bot email must not be empty")
        if not api_key:
            raise ValueError("Zulip API key must not be empty")
        if not stream:
            raise ValueError("Zulip stream must not be empty")

        self._site = site.rstrip("/")
        self._email = email
        self._api_key = api_key
        self._stream = stream
        self._topic = topic

    def send(self, alert: Alert) -> None:
        """Post an alert message to the configured Zulip stream."""
        url = f"{self._site}/api/v1/messages"
        payload = urllib.parse.urlencode(
            {
                "type": "stream",
                "to": self._stream,
                "topic": self._topic,
                "content": str(alert),
            }
        ).encode()

        credentials = base64.b64encode(
            f"{self._email}:{self._api_key}".encode()
        ).decode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Basic {credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 204):
                raise RuntimeError(
                    f"Zulip API returned unexpected status {resp.status}"
                )
