"""Tests for the Microsoft Teams notifier."""

import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.teams import TeamsAlertHandler

WEBHOOK_URL = "https://outlook.office.com/webhook/test-id/IncomingWebhook/token"


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="nightly-backup", level=level, message="Job is overdue")


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> TeamsAlertHandler:
    return TeamsAlertHandler(webhook_url=WEBHOOK_URL)


class _FakeResponse:
    def __init__(self, status: int = 200) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self) -> bytes:
        return b"1"


class TestTeamsAlertHandler(unittest.TestCase):
    def setUp(self):
        self.handler = TeamsAlertHandler(webhook_url=WEBHOOK_URL)

    def test_empty_webhook_url_raises(self):
        with self.assertRaises(ValueError):
            TeamsAlertHandler(webhook_url="")

    @patch("cronwatch.notifiers.teams.urllib.request.urlopen")
    def test_posts_to_correct_url(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        call_args = mock_urlopen.call_args
        req = call_args[0][0]
        self.assertEqual(req.full_url, WEBHOOK_URL)

    @patch("cronwatch.notifiers.teams.urllib.request.urlopen")
    def test_uses_post_method(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.method, "POST")

    @patch("cronwatch.notifiers.teams.urllib.request.urlopen")
    def test_payload_contains_job_name(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        alert = _make_alert()
        self.handler.send(alert)
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        facts = body["sections"][0]["facts"]
        job_fact = next(f for f in facts if f["name"] == "Job")
        self.assertEqual(job_fact["value"], "nightly-backup")

    @patch("cronwatch.notifiers.teams.urllib.request.urlopen")
    def test_critical_uses_red_theme(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["themeColor"], "D13438")

    @patch("cronwatch.notifiers.teams.urllib.request.urlopen")
    def test_warning_uses_orange_theme(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode("utf-8"))
        self.assertEqual(body["themeColor"], "FFA500")

    @patch("cronwatch.notifiers.teams.urllib.request.urlopen")
    def test_bad_status_raises(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(500)
        with self.assertRaises(RuntimeError):
            self.handler.send(_make_alert())

    @patch("cronwatch.notifiers.teams.urllib.request.urlopen")
    def test_content_type_header(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Content-type"), "application/json")


if __name__ == "__main__":
    unittest.main()
