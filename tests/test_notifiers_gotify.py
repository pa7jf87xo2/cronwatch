"""Tests for the Gotify alert handler."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.gotify import GotifyAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        job_name="backup",
        level=level,
        message="Job is overdue by 10 minutes",
        checked_at=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def handler() -> GotifyAlertHandler:
    return GotifyAlertHandler(url="http://gotify.example.com", token="abc123")


@pytest.fixture()
def mock_urlopen():
    fake_resp = MagicMock()
    fake_resp.status = 200
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.gotify.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


class TestGotifyAlertHandler:
    def test_empty_url_raises(self):
        with pytest.raises(ValueError, match="URL"):
            GotifyAlertHandler(url="", token="tok")

    def test_empty_token_raises(self):
        with pytest.raises(ValueError, match="token"):
            GotifyAlertHandler(url="http://gotify.example.com", token="")

    def test_posts_to_message_endpoint(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "http://gotify.example.com/message"

    def test_request_uses_correct_token_header(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("X-gotify-key") == "abc123"

    def test_payload_contains_job_name(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert "backup" in body["title"]

    def test_critical_alert_has_high_priority(self, mock_urlopen):
        h = GotifyAlertHandler(url="http://gotify.example.com", token="tok")
        h.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["priority"] == 9

    def test_warning_alert_priority(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["priority"] == 5

    def test_priority_override_respected(self, mock_urlopen):
        h = GotifyAlertHandler(url="http://gotify.example.com", token="tok", priority=1)
        h.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["priority"] == 1

    def test_trailing_slash_normalized(self, mock_urlopen):
        h = GotifyAlertHandler(url="http://gotify.example.com/", token="tok")
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "http://gotify.example.com/message"

    def test_unexpected_status_raises(self, handler):
        fake_resp = MagicMock()
        fake_resp.status = 403
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("cronwatch.notifiers.gotify.urllib.request.urlopen", return_value=fake_resp):
            with pytest.raises(RuntimeError, match="403"):
                handler.send(_make_alert())
