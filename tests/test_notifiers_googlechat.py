"""Tests for the Google Chat notifier."""

import json
from datetime import datetime, timezone
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.googlechat import GoogleChatAlertHandler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        level=level,
        job_name="backup-db",
        message="Job is overdue by 10 minutes",
        triggered_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def handler() -> GoogleChatAlertHandler:
    return GoogleChatAlertHandler(webhook_url="https://chat.googleapis.com/v1/spaces/ABC/messages?key=tok")


@pytest.fixture()
def mock_urlopen(handler):
    fake_resp = MagicMock()
    fake_resp.status = 200
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.googlechat.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestGoogleChatAlertHandler:
    def test_empty_webhook_url_raises(self):
        with pytest.raises(ValueError, match="webhook_url"):
            GoogleChatAlertHandler(webhook_url="")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://chat.googleapis.com/v1/spaces/ABC/messages?key=tok"

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
        assert "backup-db" in body["text"]

    def test_payload_contains_message(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert "overdue by 10 minutes" in body["text"]

    def test_critical_alert_includes_emoji(self, handler, mock_urlopen):
        handler.send(_make_alert(level=AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert "🚨" in body["text"]

    def test_warning_alert_includes_emoji(self, handler, mock_urlopen):
        handler.send(_make_alert(level=AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert "⚠️" in body["text"]

    def test_http_error_raises_runtime_error(self, handler):
        import urllib.error
        with patch(
            "cronwatch.notifiers.googlechat.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with pytest.raises(RuntimeError, match="Failed to reach Google Chat"):
                handler.send(_make_alert())

    def test_non_200_status_raises(self, handler):
        fake_resp = MagicMock()
        fake_resp.status = 400
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("cronwatch.notifiers.googlechat.urllib.request.urlopen", return_value=fake_resp):
            with pytest.raises(RuntimeError, match="HTTP 400"):
                handler.send(_make_alert())
