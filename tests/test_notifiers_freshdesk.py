"""Tests for the Freshdesk notifier."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.freshdesk import FreshdeskAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="nightly-backup", level=level, message="overdue by 5 min")


@pytest.fixture()
def handler() -> FreshdeskAlertHandler:
    return FreshdeskAlertHandler(
        domain="acme.freshdesk.com",
        api_key="testkey123",
        email="ops@acme.com",
    )


@pytest.fixture()
def mock_urlopen(handler):
    fake_resp = MagicMock()
    fake_resp.status = 201
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.freshdesk.urlopen", return_value=fake_resp) as m:
        yield m


class TestFreshdeskAlertHandler:
    def test_empty_domain_raises(self):
        with pytest.raises(ValueError, match="domain"):
            FreshdeskAlertHandler(domain="", api_key="k", email="a@b.com")

    def test_empty_api_key_raises(self):
        with pytest.raises(ValueError, match="api_key"):
            FreshdeskAlertHandler(domain="x.freshdesk.com", api_key="", email="a@b.com")

    def test_empty_email_raises(self):
        with pytest.raises(ValueError, match="email"):
            FreshdeskAlertHandler(domain="x.freshdesk.com", api_key="k", email="")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == "https://acme.freshdesk.com/api/v2/tickets"

    def test_uses_post_method(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"

    def test_payload_contains_job_name(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert "nightly-backup" in body["subject"]

    def test_critical_alert_sets_high_priority(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["priority"] == 3

    def test_warning_alert_sets_medium_priority(self, handler, mock_urlopen):
        handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["priority"] == 2

    def test_default_tags_include_cronwatch(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert "cronwatch" in body["tags"]

    def test_custom_tags_are_forwarded(self, mock_urlopen):
        h = FreshdeskAlertHandler(
            domain="acme.freshdesk.com",
            api_key="k",
            email="a@b.com",
            tags=["infra", "cron"],
        )
        h.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["tags"] == ["infra", "cron"]

    def test_auth_header_is_basic(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization").startswith("Basic ")

    def test_bad_status_raises_runtime_error(self, handler):
        fake_resp = MagicMock()
        fake_resp.status = 500
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("cronwatch.notifiers.freshdesk.urlopen", return_value=fake_resp):
            with pytest.raises(RuntimeError, match="unexpected status"):
                handler.send(_make_alert())
