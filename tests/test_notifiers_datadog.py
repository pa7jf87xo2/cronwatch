"""Tests for the Datadog notifier."""

import json
import unittest
from io import BytesIO
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.datadog import DatadogAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        job_name="daily-backup",
        level=level,
        message="Job is overdue by 10 minutes",
        checked_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> DatadogAlertHandler:
    return DatadogAlertHandler(api_key="test-api-key")


class _FakeResponse:
    def __init__(self, status: int = 202):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        return b'{"status": "ok"}'


class TestDatadogAlertHandler(unittest.TestCase):
    def setUp(self):
        self.handler = DatadogAlertHandler(api_key="test-api-key")

    def test_empty_api_key_raises(self):
        with self.assertRaises(ValueError):
            DatadogAlertHandler(api_key="")

    def test_custom_site_changes_url(self):
        h = DatadogAlertHandler(api_key="k", site="datadoghq.eu")
        self.assertIn("datadoghq.eu", h._base_url)

    @patch("cronwatch.notifiers.datadog.urllib.request.urlopen")
    def test_posts_to_events_endpoint(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(202)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        self.assertIn("/api/v1/events", req.full_url)

    @patch("cronwatch.notifiers.datadog.urllib.request.urlopen")
    def test_api_key_in_header(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(202)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Dd-api-key"), "test-api-key")

    @patch("cronwatch.notifiers.datadog.urllib.request.urlopen")
    def test_app_key_added_when_provided(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(202)
        h = DatadogAlertHandler(api_key="k", app_key="app-123")
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Dd-application-key"), "app-123")

    @patch("cronwatch.notifiers.datadog.urllib.request.urlopen")
    def test_critical_maps_to_error_alert_type(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(202)
        self.handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["alert_type"], "error")

    @patch("cronwatch.notifiers.datadog.urllib.request.urlopen")
    def test_warning_maps_to_warning_alert_type(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(202)
        self.handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        self.assertEqual(body["alert_type"], "warning")

    @patch("cronwatch.notifiers.datadog.urllib.request.urlopen")
    def test_payload_contains_job_name_tag(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(202)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        self.assertIn("job:daily-backup", body["tags"])

    @patch("cronwatch.notifiers.datadog.urllib.request.urlopen")
    def test_http_error_raises_runtime_error(self, mock_urlopen):
        import urllib.error
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs=None, fp=None
        )
        with self.assertRaises(RuntimeError):
            self.handler.send(_make_alert())


if __name__ == "__main__":
    unittest.main()
