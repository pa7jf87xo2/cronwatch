"""Tests for the Discord webhook notifier."""

import json
from io import BytesIO
from unittest.mock import MagicMock, patch
import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.discord import DiscordAlertHandler


WEBHOOK_URL = "https://discord.com/api/webhooks/123/abc"


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="backup", level=level, message="Job is overdue by 5 minutes")


@pytest.fixture()
def handler() -> DiscordAlertHandler:
    return DiscordAlertHandler(webhook_url=WEBHOOK_URL, username="TestBot")


@pytest.fixture()
def mock_urlopen():
    fake_resp = MagicMock()
    fake_resp.status = 204
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.discord.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


class TestDiscordAlertHandler:
    def test_empty_webhook_url_raises(self):
        with pytest.raises(ValueError, match="webhook_url"):
            DiscordAlertHandler(webhook_url="")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == WEBHOOK_URL

    def test_request_method_is_post(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"

    def test_content_type_header(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.headers["Content-type"] == "application/json"

    def test_payload_contains_job_name(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert "backup" in body["embeds"][0]["title"]

    def test_payload_contains_message(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert "overdue" in body["embeds"][0]["description"]

    def test_critical_alert_uses_red_color(self, handler, mock_urlopen):
        handler.send(_make_alert(level=AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["embeds"][0]["color"] == 15158332

    def test_warning_alert_uses_yellow_color(self, handler, mock_urlopen):
        handler.send(_make_alert(level=AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["embeds"][0]["color"] == 16776960

    def test_custom_username_in_payload(self, mock_urlopen):
        h = DiscordAlertHandler(webhook_url=WEBHOOK_URL, username="MyBot")
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["username"] == "MyBot"

    def test_http_error_raises_runtime_error(self, handler):
        import urllib.error
        err = urllib.error.HTTPError(WEBHOOK_URL, 400, "Bad Request", {}, BytesIO(b""))
        with patch("cronwatch.notifiers.discord.urllib.request.urlopen", side_effect=err):
            with pytest.raises(RuntimeError, match="400"):
                handler.send(_make_alert())
