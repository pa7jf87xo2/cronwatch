"""Tests for the Rocket.Chat notifier."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.rocketchat import RocketChatAlertHandler

_WEBHOOK = "https://rocketchat.example.com/hooks/abc123"


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        job_name="backup",
        level=level,
        message="Job is overdue by 5 minutes",
        timestamp=datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def handler() -> RocketChatAlertHandler:
    return RocketChatAlertHandler(webhook_url=_WEBHOOK)


@pytest.fixture()
def mock_urlopen():
    fake_resp = MagicMock()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.rocketchat.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


class TestRocketChatAlertHandler:
    def test_empty_webhook_url_raises(self):
        with pytest.raises(ValueError, match="webhook_url"):
            RocketChatAlertHandler(webhook_url="")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == _WEBHOOK

    def test_uses_post_method(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"

    def test_content_type_is_json(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Content-type") == "application/json"

    def test_payload_contains_job_name(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert "backup" in body["attachments"][0]["title"]

    def test_warning_colour_is_warning(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["attachments"][0]["color"] == "warning"

    def test_critical_colour_is_danger(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["attachments"][0]["color"] == "danger"

    def test_custom_username_in_payload(self, mock_urlopen):
        h = RocketChatAlertHandler(webhook_url=_WEBHOOK, username="bot")
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["username"] == "bot"

    def test_url_error_raises_runtime_error(self, handler):
        import urllib.error
        with patch(
            "cronwatch.notifiers.rocketchat.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with pytest.raises(RuntimeError, match="Rocket.Chat"):
                handler.send(_make_alert())
