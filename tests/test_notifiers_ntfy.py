"""Tests for the ntfy alert handler."""

from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.ntfy import NtfyAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="backup", level=level, message="backup is overdue by 5m")


@pytest.fixture()
def handler() -> NtfyAlertHandler:
    return NtfyAlertHandler(topic="cronwatch-alerts")


@pytest.fixture()
def mock_urlopen():
    fake_resp = MagicMock()
    fake_resp.status = 200
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.ntfy.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


class TestNtfyAlertHandler:
    def test_empty_topic_raises(self):
        with pytest.raises(ValueError, match="topic"):
            NtfyAlertHandler(topic="")

    def test_empty_server_raises(self):
        with pytest.raises(ValueError, match="server"):
            NtfyAlertHandler(topic="alerts", server="")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://ntfy.sh/cronwatch-alerts"

    def test_custom_server_in_url(self, mock_urlopen):
        h = NtfyAlertHandler(topic="alerts", server="https://ntfy.example.com")
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://ntfy.example.com/alerts"

    def test_payload_contains_job_name(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert "backup" in body["title"]

    def test_critical_maps_to_urgent_priority(self, mock_urlopen):
        h = NtfyAlertHandler(topic="alerts")
        h.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["priority"] == "urgent"

    def test_warning_maps_to_default_priority(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["priority"] == "default"

    def test_auth_header_added_when_token_provided(self, mock_urlopen):
        h = NtfyAlertHandler(topic="alerts", token="secret123")
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer secret123"

    def test_no_auth_header_without_token(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") is None

    def test_runtime_error_on_bad_status(self, handler):
        fake_resp = MagicMock()
        fake_resp.status = 403
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("cronwatch.notifiers.ntfy.urllib.request.urlopen", return_value=fake_resp):
            with pytest.raises(RuntimeError, match="403"):
                handler.send(_make_alert())
