"""Telegram alert notifier for cronwatch."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertHandler


class TelegramAlertHandler(AlertHandler):
    """Send alerts via Telegram Bot API."""

    BASE_URL = "https://api.telegram.org/bot{token}/sendMessage"

    def __init__(self, token: str, chat_id: str, parse_mode: str = "Markdown") -> None:
        if not token:
            raise ValueError("Telegram bot token must not be empty")
        if not chat_id:
            raise ValueError("Telegram chat_id must not be empty")
        self._token = token
        self._chat_id = chat_id
        self._parse_mode = parse_mode

    def send(self, alert: Alert) -> None:
        url = self.BASE_URL.format(token=self._token)
        text = (
            f"*[{alert.level.name}]* cronwatch alert\n"
            f"Job: `{alert.job_name}`\n"
            f"{alert.message}"
        )
        payload = json.dumps(
            {
                "chat_id": self._chat_id,
                "text": text,
                "parse_mode": self._parse_mode,
            }
        ).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            if resp.status not in (200, 201):
                raise RuntimeError(
                    f"Telegram API returned unexpected status {resp.status}"
                )
