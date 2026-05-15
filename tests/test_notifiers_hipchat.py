"""Tests for the HipChat notifier."""

import json
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.hipchat import HipChatAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    from cronwatch.schedule import CronJob
    job = CronJob(
        name="nightly-backup",
        schedule="0 2 * * *",
        last_run_at=datetime(2024, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
        warning_threshold=60,
        critical_threshold=120,
    )
    return Alert(job=job, level=level, message="Job is overdue")


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> HipChatAlertHandler:
    return HipChatAlertHandler(token="tok-abc", room_id="42")


class TestHipChatAlertHandler(unittest.TestCase):

    def setUp(self):
        self.handler = HipChatAlertHandler(token="tok-abc", room_id="42")

    def test_empty_token_raises(self):
        with self.assertRaises(ValueError):
            HipChatAlertHandler(token="", room_id="42")

    def test_empty_room_id_raises(self):
        with self.assertRaises(ValueError):
            HipChatAlertHandler(token="tok-abc", room_id="")

    def test_posts_to_correct_url(self):
        alert = _make_alert()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 204
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            self.handler.send(alert)
            req = mock_open.call_args[0][0]
            self.assertIn("/v2/room/42/notification", req.full_url)

    def test_payload_contains_message(self):
        alert = _make_alert()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 204
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            self.handler.send(alert)
            req = mock_open.call_args[0][0]
            body = json.loads(req.data.decode())
            self.assertIn("Job is overdue", body["message"])

    def test_critical_alert_sets_notify_true(self):
        alert = _make_alert(level=AlertLevel.CRITICAL)
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 204
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            self.handler.send(alert)
            req = mock_open.call_args[0][0]
            body = json.loads(req.data.decode())
            self.assertTrue(body["notify"])

    def test_warning_alert_color_is_yellow(self):
        alert = _make_alert(level=AlertLevel.WARNING)
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 204
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            self.handler.send(alert)
            req = mock_open.call_args[0][0]
            body = json.loads(req.data.decode())
            self.assertEqual(body["color"], "yellow")

    def test_custom_server_url_is_used(self):
        handler = HipChatAlertHandler(
            token="tok-abc", room_id="42", server_url="https://hipchat.internal.example.com"
        )
        alert = _make_alert()
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 204
        with patch("urllib.request.urlopen", return_value=mock_resp) as mock_open:
            handler.send(alert)
            req = mock_open.call_args[0][0]
            self.assertIn("hipchat.internal.example.com", req.full_url)

    def test_http_error_raises_runtime_error(self):
        import urllib.error
        alert = _make_alert()
        with patch(
            "urllib.request.urlopen",
            side_effect=urllib.error.HTTPError(url="", code=401, msg="Unauthorized", hdrs=None, fp=None),
        ):
            with self.assertRaises(RuntimeError):
                self.handler.send(alert)
