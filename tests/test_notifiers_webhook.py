"""Tests for the webhook notifier."""

import json
from datetime import timedelta
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.webhook import WebhookAlertHandler


WEBHOOK_URL = "https://example.com/hooks/cronwatch"


def _make_alert(
    level: AlertLevel = AlertLevel.WARNING,
    job_name: str = "backup",
    message: str = "Job is overdue",
    overdue_by: timedelta = timedelta(minutes=5),
) -> Alert:
    return Alert(level=level, job_name=job_name, message=message, overdue_by=overdue_by)


@pytest.fixture()
def handler() -> WebhookAlertHandler:
    return WebhookAlertHandler(url=WEBHOOK_URL)


@pytest.fixture()
def mock_urlopen():
    mock_resp = MagicMock()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    mock_resp.status = 200
    with patch("cronwatch.notifiers.webhook.urllib.request.urlopen", return_value=mock_resp) as m:
        yield m


class TestWebhookAlertHandler:
    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == WEBHOOK_URL
        assert req.method == "POST"

    def test_payload_contains_expected_fields(self, handler, mock_urlopen):
        alert = _make_alert(level=AlertLevel.CRITICAL, job_name="db-dump", overdue_by=timedelta(seconds=90))
        handler.send(alert)
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        assert payload["level"] == "CRITICAL"
        assert payload["job_name"] == "db-dump"
        assert payload["overdue_by_seconds"] == 90.0

    def test_content_type_header_is_json(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Content-type") == "application/json"

    def test_secret_header_is_attached_when_configured(self, mock_urlopen):
        h = WebhookAlertHandler(url=WEBHOOK_URL, secret_header="X-Secret", secret_value="tok123")
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("X-secret") == "tok123"

    def test_no_secret_header_when_not_configured(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("X-secret") is None

    def test_raises_on_non_2xx_response(self, handler):
        mock_resp = MagicMock()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_resp.status = 500
        with patch("cronwatch.notifiers.webhook.urllib.request.urlopen", return_value=mock_resp):
            with pytest.raises(RuntimeError, match="non-2xx"):
                handler.send(_make_alert())

    def test_raises_on_url_error(self, handler):
        import urllib.error
        with patch(
            "cronwatch.notifiers.webhook.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with pytest.raises(RuntimeError, match="Webhook request failed"):
                handler.send(_make_alert())

    def test_overdue_by_none_serializes_as_null(self, mock_urlopen):
        h = WebhookAlertHandler(url=WEBHOOK_URL)
        alert = Alert(level=AlertLevel.INFO, job_name="ping", message="ok", overdue_by=None)
        h.send(alert)
        req = mock_urlopen.call_args[0][0]
        payload = json.loads(req.data.decode())
        assert payload["overdue_by_seconds"] is None
