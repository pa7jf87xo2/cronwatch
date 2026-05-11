"""Tests for the Pushover alert handler."""

import json
import unittest
from unittest.mock import MagicMock, patch
from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.pushover import PushoverAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        job_name="backup-job",
        level=level,
        message="Job is overdue by 5 minutes",
    )


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> PushoverAlertHandler:
    return PushoverAlertHandler(user_key="uKEY123", api_token="aTOKEN456")


class TestPushoverAlertHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = PushoverAlertHandler(
            user_key="uKEY123", api_token="aTOKEN456"
        )

    def test_empty_user_key_raises(self) -> None:
        with self.assertRaises(ValueError):
            PushoverAlertHandler(user_key="", api_token="aTOKEN456")

    def test_empty_api_token_raises(self) -> None:
        with self.assertRaises(ValueError):
            PushoverAlertHandler(user_key="uKEY123", api_token="")

    @patch("cronwatch.notifiers.pushover.urllib.request.urlopen")
    def test_posts_to_pushover_api(self, mock_urlopen: MagicMock) -> None:
        fake_resp = MagicMock()
        fake_resp.status = 200
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = fake_resp

        self.handler.send(_make_alert())

        mock_urlopen.assert_called_once()
        req = mock_urlopen.call_args[0][0]
        self.assertIn("pushover.net", req.full_url)

    @patch("cronwatch.notifiers.pushover.urllib.request.urlopen")
    def test_payload_contains_user_and_token(self, mock_urlopen: MagicMock) -> None:
        fake_resp = MagicMock()
        fake_resp.status = 200
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = fake_resp

        self.handler.send(_make_alert())

        req = mock_urlopen.call_args[0][0]
        body = req.data.decode()
        self.assertIn("uKEY123", body)
        self.assertIn("aTOKEN456", body)

    @patch("cronwatch.notifiers.pushover.urllib.request.urlopen")
    def test_critical_alert_uses_priority_1(self, mock_urlopen: MagicMock) -> None:
        fake_resp = MagicMock()
        fake_resp.status = 200
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = fake_resp

        self.handler.send(_make_alert(level=AlertLevel.CRITICAL))

        req = mock_urlopen.call_args[0][0]
        body = req.data.decode()
        self.assertIn("priority=1", body)

    @patch("cronwatch.notifiers.pushover.urllib.request.urlopen")
    def test_device_included_when_set(self, mock_urlopen: MagicMock) -> None:
        fake_resp = MagicMock()
        fake_resp.status = 200
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = fake_resp

        handler = PushoverAlertHandler(
            user_key="uKEY123", api_token="aTOKEN456", device="my-phone"
        )
        handler.send(_make_alert())

        req = mock_urlopen.call_args[0][0]
        body = req.data.decode()
        self.assertIn("my-phone", body)

    @patch("cronwatch.notifiers.pushover.urllib.request.urlopen")
    def test_non_200_status_raises(self, mock_urlopen: MagicMock) -> None:
        fake_resp = MagicMock()
        fake_resp.status = 400
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = fake_resp

        with self.assertRaises(RuntimeError):
            self.handler.send(_make_alert())
