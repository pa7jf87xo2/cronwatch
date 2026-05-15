"""Tests for the Grafana notifier."""

import json
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.grafana import GrafanaAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        job_name="nightly-backup",
        level=level,
        message="Job is overdue",
        last_run_at=datetime(2024, 1, 10, 2, 0, tzinfo=timezone.utc),
        expected_at=datetime(2024, 1, 10, 3, 0, tzinfo=timezone.utc),
    )


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> GrafanaAlertHandler:
    return GrafanaAlertHandler(url="https://grafana.example.com/api/alerts")


class _FakeResponse:
    def __init__(self, status: int = 200):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestGrafanaAlertHandler(unittest.TestCase):
    def setUp(self):
        self.handler = GrafanaAlertHandler(
            url="https://grafana.example.com/api/alerts",
            api_key="test-token",
        )

    def test_empty_url_raises(self):
        with self.assertRaises(ValueError):
            GrafanaAlertHandler(url="")

    @patch("cronwatch.notifiers.grafana.urllib.request.urlopen")
    def test_posts_to_correct_url(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.full_url, "https://grafana.example.com/api/alerts")

    @patch("cronwatch.notifiers.grafana.urllib.request.urlopen")
    def test_payload_contains_job_name(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        self.assertIn("nightly-backup", payload["title"])
        self.assertEqual(payload["ruleName"], "nightly-backup")

    @patch("cronwatch.notifiers.grafana.urllib.request.urlopen")
    def test_critical_alert_maps_to_critical_severity(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        self.assertEqual(payload["severity"], "critical")
        self.assertEqual(payload["state"], "alerting")

    @patch("cronwatch.notifiers.grafana.urllib.request.urlopen")
    def test_info_alert_maps_to_ok_state(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert(AlertLevel.INFO))
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        self.assertEqual(payload["state"], "ok")
        self.assertEqual(payload["severity"], "default")

    @patch("cronwatch.notifiers.grafana.urllib.request.urlopen")
    def test_api_key_added_as_bearer_token(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Authorization"), "Bearer test-token")

    @patch("cronwatch.notifiers.grafana.urllib.request.urlopen")
    def test_no_auth_header_when_no_api_key(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        handler = GrafanaAlertHandler(url="https://grafana.example.com/api/alerts")
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        self.assertIsNone(req.get_header("Authorization"))

    @patch("cronwatch.notifiers.grafana.urllib.request.urlopen")
    def test_non_200_status_raises(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(500)
        with self.assertRaises(RuntimeError):
            self.handler.send(_make_alert())
