"""Tests for the Linear notifier."""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from cronwatch.alerting import Alert, AlertLevel
from cronwatch.notifiers.linear import LinearAlertHandler


def _make_alert(level: AlertLevel = AlertLevel.WARNING) -> Alert:
    from datetime import datetime, timezone
    return Alert(
        job_name="backup-db",
        level=level,
        message="Job is overdue by 15 minutes",
        checked_at=datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture()
def handler() -> LinearAlertHandler:
    return LinearAlertHandler(
        api_key="lin_api_testkey",
        team_id="TEAM-1",
        label_id="LABEL-99",
        assignee_id="USER-42",
    )


def _success_response(body: dict):
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(body).encode()
    mock_resp.__enter__ = lambda s: s
    mock_resp.__exit__ = MagicMock(return_value=False)
    return mock_resp


class TestLinearAlertHandler:
    def test_empty_api_key_raises(self):
        with pytest.raises(ValueError, match="api_key"):
            LinearAlertHandler(api_key="", team_id="TEAM-1")

    def test_empty_team_id_raises(self):
        with pytest.raises(ValueError, match="team_id"):
            LinearAlertHandler(api_key="lin_api_x", team_id="")

    def test_posts_to_linear_api(self, handler):
        good = {"data": {"issueCreate": {"success": True, "issue": {"id": "I-1", "title": "t"}}}}
        with patch("urllib.request.urlopen", return_value=_success_response(good)) as mock_open:
            handler.send(_make_alert())
        mock_open.assert_called_once()
        req = mock_open.call_args[0][0]
        assert req.full_url == "https://api.linear.app/graphql"
        assert req.get_header("Authorization") == "lin_api_testkey"

    def test_request_body_contains_title(self, handler):
        good = {"data": {"issueCreate": {"success": True, "issue": {"id": "I-2", "title": "t"}}}}
        with patch("urllib.request.urlopen", return_value=_success_response(good)) as mock_open:
            handler.send(_make_alert())
        req = mock_open.call_args[0][0]
        payload = json.loads(req.data)
        assert "backup-db" in payload["variables"]["title"]
        assert "WARNING" in payload["variables"]["title"]

    def test_critical_alert_maps_to_urgent_priority(self, handler):
        good = {"data": {"issueCreate": {"success": True, "issue": {"id": "I-3", "title": "t"}}}}
        with patch("urllib.request.urlopen", return_value=_success_response(good)) as mock_open:
            handler.send(_make_alert(AlertLevel.CRITICAL))
        req = mock_open.call_args[0][0]
        payload = json.loads(req.data)
        assert payload["variables"]["priority"] == 1

    def test_warning_alert_maps_to_medium_priority(self, handler):
        good = {"data": {"issueCreate": {"success": True, "issue": {"id": "I-4", "title": "t"}}}}
        with patch("urllib.request.urlopen", return_value=_success_response(good)) as mock_open:
            handler.send(_make_alert(AlertLevel.WARNING))
        req = mock_open.call_args[0][0]
        payload = json.loads(req.data)
        assert payload["variables"]["priority"] == 2

    def test_label_and_assignee_included(self, handler):
        good = {"data": {"issueCreate": {"success": True, "issue": {"id": "I-5", "title": "t"}}}}
        with patch("urllib.request.urlopen", return_value=_success_response(good)) as mock_open:
            handler.send(_make_alert())
        req = mock_open.call_args[0][0]
        payload = json.loads(req.data)
        assert payload["variables"]["labelIds"] == ["LABEL-99"]
        assert payload["variables"]["assigneeId"] == "USER-42"

    def test_api_failure_raises_runtime_error(self, handler):
        bad = {"data": {"issueCreate": {"success": False}}, "errors": [{"message": "not found"}]}
        with patch("urllib.request.urlopen", return_value=_success_response(bad)):
            with pytest.raises(RuntimeError, match="Linear issue creation failed"):
                handler.send(_make_alert())

    def test_url_error_raises_runtime_error(self, handler):
        from urllib.error import URLError
        with patch("urllib.request.urlopen", side_effect=URLError("timeout")):
            with pytest.raises(RuntimeError, match="Linear API request failed"):
                handler.send(_make_alert())
