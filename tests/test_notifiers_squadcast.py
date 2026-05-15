"""Tests for the Squadcast notifier."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.squadcast import SquadcastAlertHandler

_WEBHOOK = "https://api.squadcast.com/v2/incidents/api/abc123"


def _make_alert(level: AlertLevel = AlertLevel.CRITICAL) -> Alert:
    return Alert(
        job_name="nightly-backup",
        level=level,
        message="Job is overdue",
        last_run_at=datetime(2024, 1, 15, 3, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def handler() -> SquadcastAlertHandler:
    return SquadcastAlertHandler(webhook_url=_WEBHOOK)


@pytest.fixture()
def mock_urlopen():
    fake_resp = MagicMock()
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.squadcast.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


class TestSquadcastAlertHandler:
    def test_empty_webhook_url_raises(self) -> None:
        with pytest.raises(ValueError, match="webhook_url"):
            SquadcastAlertHandler(webhook_url="")

    def test_posts_to_correct_url(self, handler, mock_urlopen) -> None:
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.full_url == _WEBHOOK

    def test_request_method_is_post(self, handler, mock_urlopen) -> None:
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.method == "POST"

    def test_content_type_header(self, handler, mock_urlopen) -> None:
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Content-type") == "application/json"

    def test_critical_maps_to_trigger(self, handler, mock_urlopen) -> None:
        handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["status"] == "trigger"

    def test_warning_maps_to_trigger(self, handler, mock_urlopen) -> None:
        handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["status"] == "trigger"

    def test_info_maps_to_resolve(self, handler, mock_urlopen) -> None:
        handler.send(_make_alert(AlertLevel.INFO))
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["status"] == "resolve"

    def test_payload_contains_job_name(self, handler, mock_urlopen) -> None:
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data)
        assert body["tags"]["job"] == "nightly-backup"

    def test_url_error_raises_runtime_error(self, handler) -> None:
        import urllib.error
        with patch(
            "cronwatch.notifiers.squadcast.urllib.request.urlopen",
            side_effect=urllib.error.URLError("connection refused"),
        ):
            with pytest.raises(RuntimeError, match="Squadcast notification failed"):
                handler.send(_make_alert())
