"""Jira notifier – creates a Jira issue for every alert."""

from __future__ import annotations

import json
import urllib.request
import urllib.error
import base64
from typing import Any

from cronwatch.alerting import Alert, AlertLevel


class JiraAlertHandler:
    """Opens a Jira issue when a cron job alert fires."""

    def __init__(
        self,
        base_url: str,
        email: str,
        api_token: str,
        project_key: str,
        issue_type: str = "Bug",
    ) -> None:
        if not base_url:
            raise ValueError("Jira base_url must not be empty")
        if not email:
            raise ValueError("Jira email must not be empty")
        if not api_token:
            raise ValueError("Jira api_token must not be empty")
        if not project_key:
            raise ValueError("Jira project_key must not be empty")

        self._base_url = base_url.rstrip("/")
        self._project_key = project_key
        self._issue_type = issue_type
        credentials = base64.b64encode(f"{email}:{api_token}".encode()).decode()
        self._auth_header = f"Basic {credentials}"

    def _priority(self, alert: Alert) -> str:
        return {
            AlertLevel.CRITICAL: "Highest",
            AlertLevel.WARNING: "Medium",
            AlertLevel.INFO: "Low",
        }.get(alert.level, "Medium")

    def send(self, alert: Alert) -> None:
        payload: dict[str, Any] = {
            "fields": {
                "project": {"key": self._project_key},
                "summary": f"[cronwatch] {alert.level.name}: {alert.job_name}",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": str(alert)}],
                        }
                    ],
                },
                "issuetype": {"name": self._issue_type},
                "priority": {"name": self._priority(alert)},
            }
        }
        data = json.dumps(payload).encode()
        url = f"{self._base_url}/rest/api/3/issue"
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": self._auth_header,
            },
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:  # noqa: S310
            resp.read()
