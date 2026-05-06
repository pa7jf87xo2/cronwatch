"""Tests for the OpsGenie notifier."""

import json
import unittest
from datetime import timedelta
from unittest.mock import MagicMock, patch

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.opsgenie import OpsGenieAlertHandler, PRIORITY_MAP


def _make_alert(level: AlertLevel = AlertLevel.CRITICAL) -> Alert:
    return Alert(
        job_name="backup-db",
        level=level,
        overdue_by=timedelta(minutes=15),
    )


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> OpsGenieAlertHandler:
    return OpsGenieAlertHandler(api_key="test-api-key-123", tags=["prod", "cron"])


@patch("cronwatch.notifiers.opsgenie.urllib.request.urlopen")
def mock_urlopen(mock):
    cm = MagicMock()
    cm.__enter__ = lambda s: s
    cm.__exit__ = MagicMock(return_value=False)
    cm.status = 202
    mock.return_value = cm
    return mock


class TestOpsGenieAlertHandler(unittest.TestCase):

    def setUp(self):
        self.handler = OpsGenieAlertHandler(
            api_key="test-api-key-123", tags=["prod", "cron"]
        )

    def test_empty_api_key_raises(self):
        with self.assertRaises(ValueError):
            OpsGenieAlertHandler(api_key="")

    def test_blank_api_key_raises(self):
        with self.assertRaises(ValueError):
            OpsGenieAlertHandler(api_key="   ")

    @patch("cronwatch.notifiers.opsgenie.urllib.request.urlopen")
    def test_posts_to_opsgenie_url(self, mock_open):
        cm = MagicMock()
        cm.__enter__ = lambda s: s
        cm.__exit__ = MagicMock(return_value=False)
        cm.status = 202
        mock_open.return_value = cm

        self.handler.send(_make_alert())
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        self.assertIn("opsgenie.com", req.full_url)

    @patch("cronwatch.notifiers.opsgenie.urllib.request.urlopen")
    def test_authorization_header_contains_api_key(self, mock_open):
        cm = MagicMock()
        cm.__enter__ = lambda s: s
        cm.__exit__ = MagicMock(return_value=False)
        cm.status = 202
        mock_open.return_value = cm

        self.handler.send(_make_alert())
        req = mock_open.call_args[0][0]
        self.assertIn("test-api-key-123", req.get_header("Authorization"))

    @patch("cronwatch.notifiers.opsgenie.urllib.request.urlopen")
    def test_critical_maps_to_p1(self, mock_open):
        cm = MagicMock()
        cm.__enter__ = lambda s: s
        cm.__exit__ = MagicMock(return_value=False)
        cm.status = 202
        mock_open.return_value = cm

        self.handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        self.assertEqual(body["priority"], "P1")

    @patch("cronwatch.notifiers.opsgenie.urllib.request.urlopen")
    def test_warning_maps_to_p3(self, mock_open):
        cm = MagicMock()
        cm.__enter__ = lambda s: s
        cm.__exit__ = MagicMock(return_value=False)
        cm.status = 202
        mock_open.return_value = cm

        self.handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        self.assertEqual(body["priority"], "P3")

    @patch("cronwatch.notifiers.opsgenie.urllib.request.urlopen")
    def test_tags_included_in_payload(self, mock_open):
        cm = MagicMock()
        cm.__enter__ = lambda s: s
        cm.__exit__ = MagicMock(return_value=False)
        cm.status = 202
        mock_open.return_value = cm

        self.handler.send(_make_alert())
        req = mock_open.call_args[0][0]
        body = json.loads(req.data.decode())
        self.assertIn("prod", body["tags"])
        self.assertIn("cron", body["tags"])

    @patch("cronwatch.notifiers.opsgenie.urllib.request.urlopen")
    def test_http_error_raises_runtime_error(self, mock_open):
        import urllib.error
        mock_open.side_effect = urllib.error.HTTPError(
            url="", code=403, msg="Forbidden", hdrs=None, fp=None
        )
        with self.assertRaises(RuntimeError):
            self.handler.send(_make_alert())

    def test_priority_map_covers_all_levels(self):
        from cronwatch.alerting import AlertLevel
        for level in AlertLevel:
            self.assertIn(level, PRIORITY_MAP)
