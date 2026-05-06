"""Tests for the SMS (Twilio) alert notifier."""

import json
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone, timedelta
import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.schedule import CronJob
from cronwatch.notifiers.sms import SMSAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    job = CronJob(
        name="backup",
        schedule="0 2 * * *",
        last_run_at=datetime.now(timezone.utc) - timedelta(hours=3),
    )
    return Alert(level=level, job=job, message="Job is overdue")


@pytest.fixture
def handler() -> SMSAlertHandler:
    return SMSAlertHandler(
        account_sid="ACtest123",
        auth_token="token456",
        from_number="+15550001111",
        to_number="+15559998888",
    )


@pytest.fixture
def mock_urlopen():
    mock_resp = MagicMock()
    mock_resp.status = 201
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.sms.urllib.request.urlopen", return_value=mock_resp) as m:
        yield m


class TestSMSAlertHandler:
    def test_empty_account_sid_raises(self):
        with pytest.raises(ValueError, match="account_sid"):
            SMSAlertHandler("", "token", "+1555", "+1556")

    def test_empty_auth_token_raises(self):
        with pytest.raises(ValueError, match="auth_token"):
            SMSAlertHandler("ACtest", "", "+1555", "+1556")

    def test_empty_from_number_raises(self):
        with pytest.raises(ValueError, match="from_number"):
            SMSAlertHandler("ACtest", "token", "", "+1556")

    def test_empty_to_number_raises(self):
        with pytest.raises(ValueError, match="to_number"):
            SMSAlertHandler("ACtest", "token", "+1555", "")

    def test_posts_to_twilio_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert "api.twilio.com" in req.full_url
        assert "ACtest123" in req.full_url

    def test_request_method_is_post(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"

    def test_authorization_header_present(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert "Authorization" in req.headers
        assert req.headers["Authorization"].startswith("Basic ")

    def test_payload_contains_phone_numbers(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = req.data.decode()
        assert "%2B15550001111" in body or "+15550001111" in body
        assert "%2B15559998888" in body or "+15559998888" in body

    def test_payload_contains_alert_message(self, handler, mock_urlopen):
        alert = _make_alert(AlertLevel.CRITICAL)
        handler.send(alert)
        req = mock_urlopen.call_args[0][0]
        body = req.data.decode()
        assert "backup" in urllib_unquote(body)


def urllib_unquote(s: str) -> str:
    import urllib.parse
    return urllib.parse.unquote_plus(s)
