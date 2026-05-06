"""Tests for the VictorOps alert notifier."""

import json
import unittest
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.victorops import VictorOpsAlertHandler


ENDPOINT = "https://alert.victorops.com/integrations/generic/20131114/alert/TOKEN"
ROUTING_KEY = "team-ops"


def _make_alert(level: AlertLevel = AlertLevel.CRITICAL) -> Alert:
    return Alert(
        job_name="nightly-backup",
        level=level,
        message="Job is overdue by 30 minutes",
        checked_at=datetime(2024, 1, 15, 3, 0, tzinfo=timezone.utc),
    )


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> VictorOpsAlertHandler:
    return VictorOpsAlertHandler(ENDPOINT, ROUTING_KEY)


class TestVictorOpsAlertHandler(unittest.TestCase):

    def setUp(self):
        self.handler = VictorOpsAlertHandler(ENDPOINT, ROUTING_KEY)

    # --- construction ---

    def test_empty_endpoint_raises(self):
        with self.assertRaises(ValueError):
            VictorOpsAlertHandler("", ROUTING_KEY)

    def test_empty_routing_key_raises(self):
        with self.assertRaises(ValueError):
            VictorOpsAlertHandler(ENDPOINT, "")

    def test_url_includes_routing_key(self):
        h = VictorOpsAlertHandler("https://example.com/alert/TOKEN", "my-key")
        assert h._url.endswith("/my-key")

    def test_trailing_slash_on_endpoint_is_normalised(self):
        h = VictorOpsAlertHandler("https://example.com/alert/TOKEN/", "key")
        assert "//key" not in h._url

    # --- send ---

    @patch("cronwatch.notifiers.victorops.urllib.request.urlopen")
    def test_posts_to_correct_url(self, mock_open):
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.status = 200
        self.handler.send(_make_alert())
        called_url = mock_open.call_args[0][0].full_url
        assert called_url == f"{ENDPOINT}/{ROUTING_KEY}"

    @patch("cronwatch.notifiers.victorops.urllib.request.urlopen")
    def test_payload_message_type_critical(self, mock_open):
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.status = 200
        self.handler.send(_make_alert(AlertLevel.CRITICAL))
        body = json.loads(mock_open.call_args[0][0].data)
        assert body["message_type"] == "CRITICAL"

    @patch("cronwatch.notifiers.victorops.urllib.request.urlopen")
    def test_payload_message_type_warning(self, mock_open):
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.status = 200
        self.handler.send(_make_alert(AlertLevel.WARNING))
        body = json.loads(mock_open.call_args[0][0].data)
        assert body["message_type"] == "WARNING"

    @patch("cronwatch.notifiers.victorops.urllib.request.urlopen")
    def test_payload_contains_entity_id(self, mock_open):
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.status = 200
        self.handler.send(_make_alert())
        body = json.loads(mock_open.call_args[0][0].data)
        assert body["entity_id"] == "cronwatch.nightly-backup"

    @patch("cronwatch.notifiers.victorops.urllib.request.urlopen")
    def test_non_200_status_raises(self, mock_open):
        mock_open.return_value.__enter__ = lambda s: s
        mock_open.return_value.__exit__ = MagicMock(return_value=False)
        mock_open.return_value.status = 500
        with self.assertRaises(RuntimeError):
            self.handler.send(_make_alert())

    @patch("cronwatch.notifiers.victorops.urllib.request.urlopen")
    def test_url_error_raises_runtime_error(self, mock_open):
        import urllib.error
        mock_open.side_effect = urllib.error.URLError("connection refused")
        with self.assertRaises(RuntimeError):
            self.handler.send(_make_alert())
