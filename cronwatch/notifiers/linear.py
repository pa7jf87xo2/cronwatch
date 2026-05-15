"""Linear issue-tracker notifier for cronwatch."""
from __future__ import annotations

import json
import urllib.request
from urllib.error import URLError

from cronwatch.alerting import Alert, AlertLevel

_LINEAR_API = "https://api.linear.app/graphql"

_PRIORITY = {
    AlertLevel.WARNING: 2,   # Medium
    AlertLevel.CRITICAL: 1,  # Urgent
}


class LinearAlertHandler:
    """Creates a Linear issue when a cron alert fires."""

    def __init__(
        self,
        api_key: str,
        team_id: str,
        label_id: str | None = None,
        assignee_id: str | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("Linear api_key must not be empty")
        if not team_id:
            raise ValueError("Linear team_id must not be empty")
        self._api_key = api_key
        self._team_id = team_id
        self._label_id = label_id
        self._assignee_id = assignee_id

    def send(self, alert: Alert) -> None:
        title = f"[cronwatch] {alert.level.name}: {alert.job_name}"
        body = str(alert)
        priority = _PRIORITY.get(alert.level, 2)

        variables: dict = {
            "teamId": self._team_id,
            "title": title,
            "description": body,
            "priority": priority,
        }
        if self._label_id:
            variables["labelIds"] = [self._label_id]
        if self._assignee_id:
            variables["assigneeId"] = self._assignee_id

        mutation = (
            "mutation CreateIssue($teamId: String!, $title: String!, "
            "$description: String, $priority: Int, $labelIds: [String!], "
            "$assigneeId: String) {"
            "  issueCreate(input: {teamId: $teamId, title: $title, "
            "description: $description, priority: $priority, "
            "labelIds: $labelIds, assigneeId: $assigneeId}) {"
            "    success issue { id title } } }"
        )
        payload = json.dumps({"query": mutation, "variables": variables}).encode()
        req = urllib.request.Request(
            _LINEAR_API,
            data=payload,
            headers={
                "Authorization": self._api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read())
        except URLError as exc:
            raise RuntimeError(f"Linear API request failed: {exc}") from exc

        if not result.get("data", {}).get("issueCreate", {}).get("success"):
            errors = result.get("errors", [])
            raise RuntimeError(f"Linear issue creation failed: {errors}")
