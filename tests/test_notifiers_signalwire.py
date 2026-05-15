"""Tests for the SignalWire SMS alert handler."""

from __future__ import annotations

import base64
import json
import urllib.parse
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.signalwire import SignalWireAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="nightly-backup", level=level, message="Job is overdue")


@pytest.fixture()
def handler() -> SignalWireAlertHandler:
    return SignalWireAlertHandler(
        space_url="example.signalwire.com",
        project_id="proj-123",
        api_token="tok-abc",
        from_number="+15550001111",
        to_number="+15559998888",
    )


@pytest.fixture()
def mock_urlopen():
    fake_resp = MagicMock()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    fake_resp.read.return_value = b'{"sid": "SM123"}'
    with patch("cronwatch.notifiers.signalwire.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


class TestSignalWireAlertHandler:
    def test_empty_space_url_raises(self):
        with pytest.raises(ValueError, match="space_url"):
            SignalWireAlertHandler("", "pid", "tok", "+1", "+2")

    def test_empty_project_id_raises(self):
        with pytest.raises(ValueError, match="project_id"):
            SignalWireAlertHandler("example.signalwire.com", "", "tok", "+1", "+2")

    def test_empty_api_token_raises(self):
        with pytest.raises(ValueError, match="api_token"):
            SignalWireAlertHandler("example.signalwire.com", "pid", "", "+1", "+2")

    def test_empty_from_number_raises(self):
        with pytest.raises(ValueError, match="from_number"):
            SignalWireAlertHandler("example.signalwire.com", "pid", "tok", "", "+2")

    def test_empty_to_number_raises(self):
        with pytest.raises(ValueError, match="to_number"):
            SignalWireAlertHandler("example.signalwire.com", "pid", "tok", "+1", "")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert "example.signalwire.com" in req.full_url
        assert "proj-123" in req.full_url
        assert "Messages.json" in req.full_url

    def test_sends_correct_numbers(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = urllib.parse.parse_qs(req.data.decode())
        assert body["From"] == ["+15550001111"]
        assert body["To"] == ["+15559998888"]

    def test_body_contains_alert_text(self, handler, mock_urlopen):
        alert = _make_alert(AlertLevel.CRITICAL)
        handler.send(alert)
        req = mock_urlopen.call_args[0][0]
        body = urllib.parse.parse_qs(req.data.decode())
        assert str(alert) in body["Body"][0]

    def test_uses_basic_auth_header(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        auth = req.get_header("Authorization")
        expected = base64.b64encode(b"proj-123:tok-abc").decode()
        assert auth == f"Basic {expected}"

    def test_content_type_is_form_encoded(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Content-type") == "application/x-www-form-urlencoded"
