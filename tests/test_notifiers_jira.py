"""Tests for the Jira notifier."""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.jira import JiraAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.CRITICAL) -> Alert:
    return Alert(
        job_name="backup",
        level=level,
        message="Job is overdue by 10 minutes",
        checked_at=datetime(2024, 1, 15, 9, 0, 0, tzinfo=timezone.utc),
    )


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> JiraAlertHandler:
    return JiraAlertHandler(
        base_url="https://example.atlassian.net",
        email="user@example.com",
        api_token="secret-token",
        project_key="OPS",
    )


class TestJiraAlertHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = JiraAlertHandler(
            base_url="https://example.atlassian.net",
            email="user@example.com",
            api_token="secret-token",
            project_key="OPS",
        )

    def test_empty_base_url_raises(self) -> None:
        with self.assertRaises(ValueError):
            JiraAlertHandler("", "u@x.com", "tok", "OPS")

    def test_empty_email_raises(self) -> None:
        with self.assertRaises(ValueError):
            JiraAlertHandler("https://x.atlassian.net", "", "tok", "OPS")

    def test_empty_api_token_raises(self) -> None:
        with self.assertRaises(ValueError):
            JiraAlertHandler("https://x.atlassian.net", "u@x.com", "", "OPS")

    def test_empty_project_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            JiraAlertHandler("https://x.atlassian.net", "u@x.com", "tok", "")

    def test_posts_to_correct_url(self) -> None:
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        fake_resp.read.return_value = b'{"id": "10001"}'

        with patch("cronwatch.notifiers.jira.urllib.request.urlopen", return_value=fake_resp) as mock_open:
            self.handler.send(_make_alert())

        req = mock_open.call_args[0][0]
        self.assertIn("/rest/api/3/issue", req.full_url)

    def test_payload_contains_project_key(self) -> None:
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        fake_resp.read.return_value = b'{"id": "10001"}'

        with patch("cronwatch.notifiers.jira.urllib.request.urlopen", return_value=fake_resp) as mock_open:
            self.handler.send(_make_alert())

        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        self.assertEqual(body["fields"]["project"]["key"], "OPS")

    def test_critical_maps_to_highest_priority(self) -> None:
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        fake_resp.read.return_value = b'{"id": "10001"}'

        with patch("cronwatch.notifiers.jira.urllib.request.urlopen", return_value=fake_resp) as mock_open:
            self.handler.send(_make_alert(AlertLevel.CRITICAL))

        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        self.assertEqual(body["fields"]["priority"]["name"], "Highest")

    def test_warning_maps_to_medium_priority(self) -> None:
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        fake_resp.read.return_value = b'{"id": "10001"}'

        with patch("cronwatch.notifiers.jira.urllib.request.urlopen", return_value=fake_resp) as mock_open:
            self.handler.send(_make_alert(AlertLevel.WARNING))

        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        self.assertEqual(body["fields"]["priority"]["name"], "Medium")

    def test_authorization_header_is_basic(self) -> None:
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        fake_resp.read.return_value = b'{"id": "10001"}'

        with patch("cronwatch.notifiers.jira.urllib.request.urlopen", return_value=fake_resp) as mock_open:
            self.handler.send(_make_alert())

        req = mock_open.call_args[0][0]
        self.assertTrue(req.get_header("Authorization").startswith("Basic "))

    def test_summary_contains_job_name(self) -> None:
        fake_resp = MagicMock()
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        fake_resp.read.return_value = b'{"id": "10001"}'

        with patch("cronwatch.notifiers.jira.urllib.request.urlopen", return_value=fake_resp) as mock_open:
            self.handler.send(_make_alert())

        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        self.assertIn("backup", body["fields"]["summary"])
