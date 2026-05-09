"""Tests for the Mattermost notifier."""

import json
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.mattermost import MattermostAlertHandler


WEBHOOK_URL = "https://mattermost.example.com/hooks/abc123"


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        job_name="nightly-backup",
        level=level,
        message="Job is overdue by 15 minutes",
        checked_at=datetime(2024, 6, 1, 3, 0, 0, tzinfo=timezone.utc),
    )


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> MattermostAlertHandler:
    return MattermostAlertHandler(webhook_url=WEBHOOK_URL)


class _FakeResponse:
    def __init__(self, status: int = 200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestMattermostAlertHandler(unittest.TestCase):

    def setUp(self):
        self.handler = MattermostAlertHandler(webhook_url=WEBHOOK_URL)

    def test_empty_webhook_url_raises(self):
        with self.assertRaises(ValueError):
            MattermostAlertHandler(webhook_url="")

    def test_default_username(self):
        self.assertEqual(self.handler._username, "cronwatch")

    def test_custom_username(self):
        h = MattermostAlertHandler(webhook_url=WEBHOOK_URL, username="watchbot")
        self.assertEqual(h._username, "watchbot")

    def test_custom_channel_included_in_payload(self):
        h = MattermostAlertHandler(webhook_url=WEBHOOK_URL, channel="#ops")
        alert = _make_alert()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _FakeResponse(200)
            h.send(alert)
            call_args = mock_open.call_args[0][0]
            body = json.loads(call_args.data.decode())
            self.assertEqual(body["channel"], "#ops")

    def test_no_channel_key_when_not_set(self):
        alert = _make_alert()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _FakeResponse(200)
            self.handler.send(alert)
            call_args = mock_open.call_args[0][0]
            body = json.loads(call_args.data.decode())
            self.assertNotIn("channel", body)

    def test_posts_to_correct_url(self):
        alert = _make_alert()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _FakeResponse(200)
            self.handler.send(alert)
            req = mock_open.call_args[0][0]
            self.assertEqual(req.full_url, WEBHOOK_URL)

    def test_payload_contains_job_name(self):
        alert = _make_alert()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _FakeResponse(200)
            self.handler.send(alert)
            req = mock_open.call_args[0][0]
            body = json.loads(req.data.decode())
            self.assertIn("nightly-backup", body["text"])

    def test_critical_alert_contains_rotating_light(self):
        alert = _make_alert(level=AlertLevel.CRITICAL)
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _FakeResponse(200)
            self.handler.send(alert)
            req = mock_open.call_args[0][0]
            body = json.loads(req.data.decode())
            self.assertIn(":rotating_light:", body["text"])

    def test_bad_status_raises(self):
        alert = _make_alert()
        with patch("urllib.request.urlopen") as mock_open:
            mock_open.return_value = _FakeResponse(500)
            with self.assertRaises(RuntimeError):
                self.handler.send(alert)


if __name__ == "__main__":
    unittest.main()
