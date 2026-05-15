"""SignalWire SMS alert handler for cronwatch."""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
import base64
from cronwatch.alerting import Alert, AlertHandler


class SignalWireAlertHandler(AlertHandler):
    """Send SMS alerts via the SignalWire REST API."""

    def __init__(
        self,
        space_url: str,
        project_id: str,
        api_token: str,
        from_number: str,
        to_number: str,
    ) -> None:
        if not space_url:
            raise ValueError("SignalWire space_url must not be empty")
        if not project_id:
            raise ValueError("SignalWire project_id must not be empty")
        if not api_token:
            raise ValueError("SignalWire api_token must not be empty")
        if not from_number:
            raise ValueError("SignalWire from_number must not be empty")
        if not to_number:
            raise ValueError("SignalWire to_number must not be empty")

        self.space_url = space_url.rstrip("/")
        self.project_id = project_id
        self.api_token = api_token
        self.from_number = from_number
        self.to_number = to_number

    def send(self, alert: Alert) -> None:
        url = (
            f"https://{self.space_url}/api/laml/2010-04-01"
            f"/Accounts/{self.project_id}/Messages.json"
        )
        payload = urllib.parse.urlencode(
            {
                "From": self.from_number,
                "To": self.to_number,
                "Body": str(alert),
            }
        ).encode()

        credentials = f"{self.project_id}:{self.api_token}"
        token = base64.b64encode(credentials.encode()).decode()

        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Authorization": f"Basic {token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            resp.read()
