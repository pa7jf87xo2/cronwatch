"""Tests for the Matrix alert notifier."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.matrix import MatrixAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    return Alert(job_name="backup", level=level, message="Overdue by 5 min")


@pytest.fixture()
def handler() -> MatrixAlertHandler:
    return MatrixAlertHandler(
        homeserver="https://matrix.example.com",
        access_token="syt_secret_token",
        room_id="!abcdef:example.com",
    )


@pytest.fixture()
def mock_urlopen(handler):
    fake_resp = MagicMock()
    fake_resp.status = 200
    fake_resp.__enter__ = lambda s: s
    fake_resp.__exit__ = MagicMock(return_value=False)
    with patch("cronwatch.notifiers.matrix.urllib.request.urlopen", return_value=fake_resp) as m:
        yield m


class TestMatrixAlertHandler:
    def test_empty_homeserver_raises(self):
        with pytest.raises(ValueError, match="homeserver"):
            MatrixAlertHandler(homeserver="", access_token="tok", room_id="!r:h")

    def test_empty_access_token_raises(self):
        with pytest.raises(ValueError, match="access_token"):
            MatrixAlertHandler(homeserver="https://h", access_token="", room_id="!r:h")

    def test_empty_room_id_raises(self):
        with pytest.raises(ValueError, match="room_id"):
            MatrixAlertHandler(homeserver="https://h", access_token="tok", room_id="")

    def test_posts_to_correct_url(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert "/_matrix/client/v3/rooms/" in req.full_url
        assert "send/m.room.message" in req.full_url

    def test_authorization_header_set(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Authorization") == "Bearer syt_secret_token"

    def test_content_type_is_json(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("Content-type") == "application/json"

    def test_payload_contains_alert_text(self, handler, mock_urlopen):
        alert = _make_alert(AlertLevel.CRITICAL)
        handler.send(alert)
        req = mock_urlopen.call_args[0][0]
        body = json.loads(req.data.decode())
        assert body["msgtype"] == "m.text"
        assert "backup" in body["body"]
        assert "CRITICAL" in body["body"]

    def test_room_id_is_url_encoded(self, handler, mock_urlopen):
        handler.send(_make_alert())
        req = mock_urlopen.call_args[0][0]
        # '!' and ':' should be percent-encoded in the path segment
        assert "!abcdef:example.com" not in req.full_url

    def test_non_200_status_raises(self, handler):
        fake_resp = MagicMock()
        fake_resp.status = 403
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = MagicMock(return_value=False)
        with patch("cronwatch.notifiers.matrix.urllib.request.urlopen", return_value=fake_resp):
            with pytest.raises(RuntimeError, match="403"):
                handler.send(_make_alert())

    def test_timeout_forwarded(self, handler, mock_urlopen):
        handler.send(_make_alert())
        _, kwargs = mock_urlopen.call_args
        assert kwargs.get("timeout") == 10
