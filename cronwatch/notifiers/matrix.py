"""Matrix (matrix.org) alert notifier via the Client-Server API."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any

from cronwatch.alerting import Alert, AlertHandler


class MatrixAlertHandler(AlertHandler):
    """Send alerts to a Matrix room using the Matrix Client-Server API."""

    def __init__(
        self,
        homeserver: str,
        access_token: str,
        room_id: str,
        timeout: int = 10,
    ) -> None:
        if not homeserver:
            raise ValueError("homeserver must not be empty")
        if not access_token:
            raise ValueError("access_token must not be empty")
        if not room_id:
            raise ValueError("room_id must not be empty")

        self.homeserver = homeserver.rstrip("/")
        self.access_token = access_token
        self.room_id = room_id
        self.timeout = timeout

    def send(self, alert: Alert) -> None:
        """POST a plain-text message event to the configured Matrix room."""
        url = (
            f"{self.homeserver}/_matrix/client/v3/rooms/"
            f"{urllib.request.quote(self.room_id, safe='')}"
            "/send/m.room.message"
        )
        payload: dict[str, Any] = {
            "msgtype": "m.text",
            "body": str(alert),
        }
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:  # noqa: S310
            if resp.status not in (200, 201):
                raise RuntimeError(
                    f"Matrix API returned unexpected status {resp.status}"
                )
