"""Tests for the Splunk HEC alert handler."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.splunk import SplunkAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="nightly-backup", level=level, overdue_by=120)


@pytest.fixture()
def handler() -> SplunkAlertHandler:
    return SplunkAlertHandler(
        hec_url="https://splunk.example.com:8088",
        token="abc-123",
        index="ops",
    )


@pytest.fixture()
def mock_urlopen():
    fake_resp = MagicMock()
    fake_resp.status = 200
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.splunk.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


class TestSplunkAlertHandler:
    def test_empty_hec_url_raises(self):
        with pytest.raises(ValueError, match="hec_url"):
            SplunkAlertHandler(hec_url="", token="tok")

    def test_empty_token_raises(self):
        with pytest.raises(ValueError, match="token"):
            SplunkAlertHandler(hec_url="https://splunk.example.com:8088", token="")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://splunk.example.com:8088/services/collector/event"

    def test_authorization_header(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Splunk abc-123"

    def test_payload_contains_job_name(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["event"]["job"] == "nightly-backup"

    def test_payload_contains_level(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["event"]["level"] == "CRITICAL"

    def test_payload_uses_configured_index(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["index"] == "ops"

    def test_payload_contains_overdue_seconds(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["event"]["overdue_by_seconds"] == 120

    def test_non_200_raises(self, handler):
        fake_resp = MagicMock()
        fake_resp.status = 400
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("cronwatch.notifiers.splunk.urllib.request.urlopen", return_value=fake_resp):
            with pytest.raises(RuntimeError, match="400"):
                handler.send(_make_alert())
