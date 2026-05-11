"""Pushover alert handler for cronwatch."""

import json
import urllib.request
import urllib.parse
from cronwatch.alerting import Alert, AlertHandler, AlertLevel

_PUSHOVER_API_URL = "https://api.pushover.net/1/messages.json"

_PRIORITY_MAP = {
    AlertLevel.INFO: 0,
    AlertLevel.WARNING: 0,
    AlertLevel.CRITICAL: 1,
}


class PushoverAlertHandler(AlertHandler):
    """Send alerts via the Pushover notification service."""

    def __init__(self, user_key: str, api_token: str, device: str = "") -> None:
        if not user_key:
            raise ValueError("Pushover user_key must not be empty")
        if not api_token:
            raise ValueError("Pushover api_token must not be empty")
        self._user_key = user_key
        self._api_token = api_token
        self._device = device

    def send(self, alert: Alert) -> None:
        priority = _PRIORITY_MAP.get(alert.level, 0)
        payload: dict = {
            "token": self._api_token,
            "user": self._user_key,
            "title": f"[{alert.level.name}] cronwatch: {alert.job_name}",
            "message": str(alert),
            "priority": priority,
        }
        if self._device:
            payload["device"] = self._device

        data = urllib.parse.urlencode(payload).encode()
        req = urllib.request.Request(
            _PUSHOVER_API_URL,
            data=data,
            method="POST",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req) as resp:
            if resp.status != 200:
                raise RuntimeError(
                    f"Pushover API returned unexpected status {resp.status}"
                )
