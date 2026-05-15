"""HipChat notifier for cronwatch alerts."""

import json
import urllib.request
import urllib.error
from cronwatch.alerting import Alert, AlertLevel


class HipChatAlertHandler:
    """Send alerts to a HipChat room via the v2 API."""

    COLORS = {
        AlertLevel.INFO: "green",
        AlertLevel.WARNING: "yellow",
        AlertLevel.CRITICAL: "red",
    }

    def __init__(self, token: str, room_id: str, server_url: str = "https://api.hipchat.com"):
        if not token:
            raise ValueError("HipChat API token must not be empty")
        if not room_id:
            raise ValueError("HipChat room_id must not be empty")
        self.token = token
        self.room_id = room_id
        self.server_url = server_url.rstrip("/")

    def send(self, alert: Alert) -> None:
        """Post a notification message to the configured HipChat room."""
        url = f"{self.server_url}/v2/room/{self.room_id}/notification"
        color = self.COLORS.get(alert.level, "gray")
        payload = json.dumps({
            "message": str(alert),
            "color": color,
            "notify": alert.level == AlertLevel.CRITICAL,
            "message_format": "text",
        }).encode()
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req) as resp:
                return resp.status
        except urllib.error.HTTPError as exc:
            raise RuntimeError(
                f"HipChat notification failed with HTTP {exc.code}: {exc.reason}"
            ) from exc
