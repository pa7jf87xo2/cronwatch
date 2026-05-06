"""SMS alert notifier using Twilio REST API."""

import json
import urllib.request
import urllib.parse
import base64
from cronwatch.alerting import Alert, AlertHandler


class SMSAlertHandler(AlertHandler):
    """Send alerts via SMS using the Twilio API."""

    TWILIO_API_URL = "https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_number: str,
    ) -> None:
        if not account_sid:
            raise ValueError("Twilio account_sid must not be empty")
        if not auth_token:
            raise ValueError("Twilio auth_token must not be empty")
        if not from_number:
            raise ValueError("from_number must not be empty")
        if not to_number:
            raise ValueError("to_number must not be empty")

        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_number = to_number
        self._url = self.TWILIO_API_URL.format(account_sid=account_sid)

    def send(self, alert: Alert) -> None:
        """Send an SMS message for the given alert."""
        body = str(alert)

        payload = urllib.parse.urlencode({
            "From": self.from_number,
            "To": self.to_number,
            "Body": body,
        }).encode()

        credentials = f"{self.account_sid}:{self.auth_token}"
        encoded = base64.b64encode(credentials.encode()).decode()

        req = urllib.request.Request(
            self._url,
            data=payload,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        with urllib.request.urlopen(req) as response:
            if response.status not in (200, 201):
                raise RuntimeError(
                    f"Twilio API returned unexpected status {response.status}"
                )
