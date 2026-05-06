"""Tests for the PagerDuty notifier."""

import json
import pytest
from unittest.mock import MagicMock, patch
from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.pagerduty import PagerDutyAlertHandler, PAGERDUTY_EVENTS_API


INTEGRATION_KEY = "test-integration-key-abc123"


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(
        job_name="nightly-backup",
        level=level,
        message="Job is overdue by 30 minutes",
    )


@pytest.fixture
def handler() -> PagerDutyAlertHandler:
    return PagerDutyAlertHandler(integration_key=INTEGRATION_KEY)


@pytest.fixture
def mock_urlopen():
    mock_resp = MagicMock()
    mock_resp.status = 202
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.pagerduty.urllib.request.urlopen") as m:
        m.return_value = mock_resp
        yield m


class TestPagerDutyAlertHandler:
    def test_empty_integration_key_raises(self):
        with pytest.raises(ValueError, match="integration_key"):
            PagerDutyAlertHandler(integration_key="")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == PAGERDUTY_EVENTS_API

    def test_request_method_is_post(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"

    def test_payload_contains_routing_key(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["routing_key"] == INTEGRATION_KEY

    def test_payload_dedup_key_uses_job_name(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["dedup_key"] == "cronwatch-nightly-backup"

    def test_critical_alert_maps_to_critical_severity(self, handler, mock_urlopen):
        handler.send(_make_alert(level=AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["payload"]["severity"] == "critical"

    def test_warning_alert_maps_to_warning_severity(self, handler, mock_urlopen):
        handler.send(_make_alert(level=AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["payload"]["severity"] == "warning"

    def test_custom_source_is_included(self, mock_urlopen):
        h = PagerDutyAlertHandler(INTEGRATION_KEY, source="my-service")
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["payload"]["source"] == "my-service"

    def test_http_error_raises_runtime_error(self, handler):
        import urllib.error
        with patch("cronwatch.notifiers.pagerduty.urllib.request.urlopen") as m:
            m.side_effect = urllib.error.HTTPError(
                PAGERDUTY_EVENTS_API, 400, "Bad Request", {}, None
            )
            with pytest.raises(RuntimeError, match="PagerDuty request failed"):
                handler.send(_make_alert())
