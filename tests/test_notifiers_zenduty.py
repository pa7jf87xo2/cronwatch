"""Tests for the Zenduty alert notifier."""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.zenduty import ZendutyAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="nightly-backup", level=level, message="overdue by 5 min")


@pytest.fixture()
def handler() -> ZendutyAlertHandler:
    return ZendutyAlertHandler(integration_key="test-key-abc")


@pytest.fixture()
def mock_urlopen(monkeypatch):
    fake_resp = MagicMock()
    fake_resp.status = 202
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    m = MagicMock(return_value=fake_resp)
    monkeypatch.setattr("cronwatch.notifiers.zenduty.urllib.request.urlopen", m)
    return m


class TestZendutyAlertHandler:
    def test_empty_integration_key_raises(self):
        with pytest.raises(ValueError, match="integration_key"):
            ZendutyAlertHandler(integration_key="")

    def test_posts_to_events_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == ZendutyAlertHandler.EVENTS_URL

    def test_uses_post_method(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"

    def test_authorization_header_contains_key(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Token test-key-abc"

    def test_content_type_is_json(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Content-type") == "application/json"

    def test_warning_maps_to_warning_action(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["alert_type"] == "warning"

    def test_critical_maps_to_critical_action(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["alert_type"] == "critical"

    def test_payload_contains_job_name(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["entity_id"] == "nightly-backup"
        assert body["payload"]["job_name"] == "nightly-backup"

    def test_url_error_raises_runtime_error(self, handler, monkeypatch):
        import urllib.error
        monkeypatch.setattr(
            "cronwatch.notifiers.zenduty.urllib.request.urlopen",
            MagicMock(side_effect=urllib.error.URLError("connection refused")),
        )
        with pytest.raises(RuntimeError, match="Failed to reach Zenduty"):
            handler.send(_make_alert())

    def test_non_2xx_status_raises(self, monkeypatch):
        fake_resp = MagicMock()
        fake_resp.status = 403
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        monkeypatch.setattr(
            "cronwatch.notifiers.zenduty.urllib.request.urlopen",
            MagicMock(return_value=fake_resp),
        )
        h = ZendutyAlertHandler(integration_key="key")
        with pytest.raises(RuntimeError, match="403"):
            h.send(_make_alert())
