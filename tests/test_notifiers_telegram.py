"""Tests for the Telegram alert notifier."""

import json
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.telegram import TelegramAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        level=level,
        job_name="backup-db",
        message="Job is overdue by 10 minutes",
        timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@unittest.fixture  # type: ignore[attr-defined]
def handler() -> TelegramAlertHandler:
    return TelegramAlertHandler(token="bot-token-123", chat_id="-100123456")


class _FakeResponse:
    def __init__(self, status: int = 200) -> None:
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


class TestTelegramAlertHandler(unittest.TestCase):
    def setUp(self):
        self.handler = TelegramAlertHandler(
            token="bot-token-123", chat_id="-100123456"
        )

    def test_empty_token_raises(self):
        with self.assertRaises(ValueError):
            TelegramAlertHandler(token="", chat_id="-100123456")

    def test_empty_chat_id_raises(self):
        with self.assertRaises(ValueError):
            TelegramAlertHandler(token="bot-token-123", chat_id="")

    @patch("cronwatch.notifiers.telegram.urllib.request.urlopen")
    def test_posts_to_correct_url(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        call_args = mock_urlopen.call_args[0][0]
        assert "bot-token-123" in call_args.full_url
        assert "sendMessage" in call_args.full_url

    @patch("cronwatch.notifiers.telegram.urllib.request.urlopen")
    def test_payload_contains_chat_id(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        assert payload["chat_id"] == "-100123456"

    @patch("cronwatch.notifiers.telegram.urllib.request.urlopen")
    def test_payload_contains_job_name(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        assert "backup-db" in payload["text"]

    @patch("cronwatch.notifiers.telegram.urllib.request.urlopen")
    def test_payload_contains_alert_level(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        self.handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        assert "CRITICAL" in payload["text"]

    @patch("cronwatch.notifiers.telegram.urllib.request.urlopen")
    def test_custom_parse_mode(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(200)
        handler = TelegramAlertHandler(
            token="tok", chat_id="123", parse_mode="HTML"
        )
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        assert payload["parse_mode"] == "HTML"

    @patch("cronwatch.notifiers.telegram.urllib.request.urlopen")
    def test_non_200_raises_runtime_error(self, mock_urlopen):
        mock_urlopen.return_value = _FakeResponse(500)
        with self.assertRaises(RuntimeError):
            self.handler.send(_make_alert())
